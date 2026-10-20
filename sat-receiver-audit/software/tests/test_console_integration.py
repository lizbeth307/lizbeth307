"""Cross-module RX/FFT/HMI/learning workflows, without SDR or private content."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

import numpy as np

from srrx import learning
from srrx.hmi import ConsoleController, DemoTransport, load_spectrum, spectrum_columns
from srrx.labrx import run_capture
from srrx.receivers import ControlGuard
from srrx.spectrum import FRAME_FIELDS, SpectrumProcessor, validate_frame

PROJECT = Path(__file__).resolve().parents[2]


def command(module, *arguments):
    return subprocess.run([sys.executable, '-m', module, *map(str, arguments)], cwd=PROJECT,
                          env=dict(os.environ, PYTHONPATH=str(PROJECT / 'software'),
                                   OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
                          # ARM64 TCG must cold-load NumPy/ORT from the guest disk.
                          # This bounds the test subprocess, not a service lease.
                          capture_output=True, text=True, timeout=90)


def ready_status():
    # Explicit in-memory guard fixture only, never a persisted hardware acceptance.
    return {'ok': True, 'data': {'mode': 'HARDWARE', 'hardware_qualified': True,
        'live_identity_verified': True, 'configured': True, 'last_error': None,
        'session': 17, 'pico': {'state': 'ACTIVE', 'mcp_reset': False},
        'policy': {'armed': True, 'commissioned': True, 'pico_active': True,
                   'fault': None, 'outputs': {'EN_RTLA': True}}}}


def fft_example(seed, family, size=128):
    rng = np.random.default_rng(seed)
    t = np.arange(size)
    if family == 0:
        samples = .3 * np.exp(2j * np.pi * 16 * t / size)
    else:
        samples = sum(.12 * np.exp(2j * np.pi * k * t / size) for k in (-20, -10, 0, 10, 20))
    samples += .01 * (rng.normal(size=size) + 1j * rng.normal(size=size))
    return SpectrumProcessor(size).process(samples, 100e6, 1024e3, 'SIMULATION')


class ConsolePipelineTests(unittest.TestCase):
    def cli_ok(self, module, *arguments):
        result = command(module, *arguments)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_capture_cli_protected_survey_stays_no_data_through_hmi_and_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            output, survey = directory / 'spectrum.json', directory / 'survey.jsonl'
            result = self.cli_ok('srrx.labrx', '--simulate', '--center-hz', 300000000,
                                 '--fft-size', 64, '--frames', 2, '--output', output, '--survey', survey)
            self.assertEqual(result['source'], 'SIMULATION')
            self.assertFalse(result['raw_iq_persisted'])
            self.assertFalse(result['physical_tests_performed'])
            self.assertEqual(result['frames'], 2)
            frame = validate_frame(load_spectrum(output))
            self.assertEqual(frame['center_hz'], 300000000)
            self.assertEqual(frame['sample_rate_hz'], 1024000)
            self.assertEqual(set(frame), FRAME_FIELDS)
            self.assertEqual(frame['power_dbfs'], [None] * 64)
            self.assertFalse(any(frame['valid']))
            self.assertEqual(spectrum_columns(frame, columns=8), [None] * 8)
            lines = survey.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(load_spectrum(survey), frame)
            for line in lines:
                self.assertEqual(validate_frame(json.loads(line))['power_dbfs'], [None] * 64)
            with self.assertRaises(ValueError):
                learning.annotate(learning.empty_dataset(), frame, 0, 64, 'unknown_energy',
                                  group_id=uuid.UUID(int=1), user_confirmed=True)
            self.assertEqual({p.name for p in directory.iterdir()}, {'spectrum.json', 'survey.jsonl'})

    def test_real_capture_fft_annotation_cli_train_infer_and_saved_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            first = directory / 'frame0.json'
            result = self.cli_ok('srrx.labrx', '--simulate', '--fft-size', 128,
                                 '--frames', 1, '--output', first)
            self.assertEqual(result['source'], 'SIMULATION')
            dataset_path, model_path = directory / 'annotations.json', directory / 'model.json'
            examples = [load_spectrum(first), fft_example(101, 0),
                        fft_example(201, 1), fft_example(202, 1)]
            # Independent seeded simulation groups; labels are deliberate fixture
            # annotations of shapes, not a claimed radio-protocol ground truth.
            for index, frame in enumerate(examples):
                path = directory / f'frame{index}.json'
                path.write_text(json.dumps(frame, allow_nan=False))
                label = 'analog_broadcast' if index < 2 else 'digital_broadcast'
                annotated = self.cli_ok('srrx.learning', 'annotate', '--dataset', dataset_path,
                                        '--frame', path, '--start', 0, '--end', 128, '--label', label,
                                        '--group', str(uuid.UUID(int=index + 1)), '--user-confirmed')
                self.assertEqual(annotated['annotations'], index + 1)
            fitted = self.cli_ok('srrx.learning', 'train', '--dataset', dataset_path,
                                 '--model', model_path, '--seed', 7)
            dataset, model = learning.load_dataset(dataset_path), learning.load_model(model_path)
            self.assertEqual(len(dataset['annotations']), 4)
            self.assertEqual(model['sha256'], fitted['model_sha256'])
            self.assertEqual(model['provenance']['source_counts']['HARDWARE'], 0)
            self.assertGreater(model['provenance']['source_counts']['SIMULATION'], 0)
            self.assertEqual(model['validation']['scope'], 'held_out_capture_groups_only_not_field_accuracy')
            self.assertFalse(set(model['provenance']['train_groups']) & set(model['provenance']['validation_groups']))
            self.assertTrue(all(f['source'] == 'SIMULATION' and set(f) == FRAME_FIELDS for f in dataset['frames'].values()))
            query = directory / 'query.json'
            query.write_text(json.dumps(fft_example(999, 1), allow_nan=False))
            predicted = self.cli_ok('srrx.learning', 'infer', '--model', model_path, '--frame', query,
                                    '--start', 0, '--end', 128, '--backend', 'npu')
            self.assertEqual(predicted['source'], 'SIMULATION')
            self.assertEqual(predicted['backend'], 'CPU')
            self.assertFalse(predicted['npu']['available'])
            self.assertIn(predicted['label'], learning.LABELS)
            self.assertEqual(predicted['model_sha256'], model['sha256'])
            self.assertEqual(learning.infer(model, load_spectrum(query), 0, 128)['label'], predicted['label'])
            for path in directory.iterdir():
                parsed = json.loads(path.read_text())
                def inspect(value):
                    if isinstance(value, dict):
                        self.assertFalse(set(value) & {'raw_iq', 'iq', 'audio', 'latitude', 'longitude', 'emitter_id'})
                        for item in value.values():
                            inspect(item)
                    elif isinstance(value, list):
                        for item in value:
                            inspect(item)
                inspect(parsed)

    def test_untrusted_hmi_frame_is_remasked_before_saved_annotation(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            frame = SpectrumProcessor(64).process(np.ones(64), 225e6, 1024e3)
            original_invalid = [i for i, flag in enumerate(frame['valid']) if not flag]
            forged = copy.deepcopy(frame)
            for i in original_invalid:
                forged['valid'][i], forged['power_dbfs'][i] = True, 1111.2222
            input_path = directory / 'untrusted.json'
            input_path.write_text(json.dumps(forged))
            safe = load_spectrum(input_path)
            for i in original_invalid:
                self.assertFalse(safe['valid'][i])
                self.assertIsNone(safe['power_dbfs'][i])
            dataset = learning.annotate(learning.empty_dataset(), safe, 8, 24, 'unknown_energy',
                                        group_id=uuid.UUID(int=7), user_confirmed=True)
            output = directory / 'annotations.json'
            learning.save_dataset(output, dataset)
            self.assertNotIn('1111.2222', output.read_text())
            self.assertEqual(learning.load_dataset(output), dataset)
            with self.assertRaises(ValueError):
                learning.annotate(dataset, forged, 24, 48, 'unknown_energy',
                                  group_id=uuid.UUID(int=8), user_confirmed=True)

    def test_malformed_metadata_and_raw_fields_cannot_cross_hmi_annotation_boundary(self):
        base = fft_example(111, 0)
        mutations = []
        raw = copy.deepcopy(base); raw['raw_iq'] = [[1, 2]]; mutations.append(raw)
        gnss = copy.deepcopy(base); gnss['gnss_position'] = {'latitude': 50.0}; mutations.append(gnss)
        grid = copy.deepcopy(base); grid['relative_frequency_hz'][1] += 1; mutations.append(grid)
        invalid = copy.deepcopy(base); invalid['valid'][2] = 'true'; mutations.append(invalid)
        for frame in mutations:
            with self.subTest(fields=set(frame)):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'frame.json'
                    path.write_text(json.dumps(frame))
                    with self.assertRaises(ValueError):
                        load_spectrum(path)
                    with self.assertRaises(ValueError):
                        learning.annotate(learning.empty_dataset(), frame, 0, 128, 'unknown_energy',
                                          group_id=uuid.UUID(int=4), user_confirmed=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frame.json'
            path.write_text('{"center_hz":NaN}')
            with self.assertRaises(ValueError):
                load_spectrum(path)

    def test_missing_hardware_acceptance_cli_refuses_without_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'spectrum.json'
            result = command('srrx.labrx', '--hardware', '--frames', 1, '--output', output,
                             '--project', PROJECT)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('acceptance', result.stderr.lower())
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_live_demo_console_cannot_satisfy_physical_capture_guard(self):
        transport = DemoTransport(timeout=20)
        controller = ConsoleController(transport)
        try:
            # Bound interpreter startup separately from live console freshness.
            initial = transport({'op': 'status'})
            self.assertTrue(initial['ok'], initial)
            self.assertEqual(initial['data']['mode'], 'SIMULATION')
            self.assertFalse(initial['data']['policy']['armed'])
            transport.timeout = 2
            ready_at = time.monotonic() + 20
            while True:
                status = controller.poll()
                if (status['connected'] and status['data'].get('session') is not None
                        and status['data']['pico'].get('state') == 'SAFE'):
                    break
                self.assertLess(time.monotonic(), ready_at, status)
                time.sleep(.03)
            armed = controller.arm()
            self.assertTrue(armed['ok'], armed)
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                status = controller.poll()
                if status['data']['policy']['armed']:
                    break
                time.sleep(.03)
            self.assertTrue(status['data']['policy']['armed'])
            self.assertTrue(controller.command('control', name='EN_RTLA', value=True)['ok'])
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'spectrum.json'
                with patch('srrx.labrx.WorkerSource') as factory:
                    with self.assertRaises(RuntimeError):
                        run_capture(frames=1, output=output, record={'backend': 'rtl', 'branch': 'RTLA'},
                                    transport=transport, source_factory=factory)
                    factory.assert_not_called()
                self.assertFalse(output.exists())
        finally:
            controller.close()
            transport.close()

    def test_capture_session_change_and_malformed_status_stop_before_export(self):
        reply = ready_status()
        requests = []
        def transport(request):
            requests.append(copy.deepcopy(request))
            return copy.deepcopy(reply) if request['op'] == 'status' else {'ok': True}
        source = None
        class SessionChangesAtRead:
            closed = False
            def __init__(self, *args):
                nonlocal source
                source = self
            def read(self, guard):
                reply['data']['session'] = 18
                return np.ones(1024, dtype=np.complex64)
            def close(self):
                self.closed = True
        with tempfile.TemporaryDirectory() as directory:
            output, survey = Path(directory) / 'spectrum.json', Path(directory) / 'survey.jsonl'
            with self.assertRaisesRegex(RuntimeError, 'session changed'):
                run_capture(frames=1, output=output, survey=survey,
                            record={'backend': 'rtl', 'branch': 'RTLA'}, transport=transport,
                            source_factory=SessionChangesAtRead)
            self.assertTrue(source.closed)
            self.assertFalse(output.exists() or survey.exists())
            self.assertEqual(requests[-1], {'op': 'control', 'name': 'EN_RTLA', 'value': False})
        for data in ([], {'policy': []}, {'policy': {'outputs': []}, 'pico': {}},
                     {'policy': {}, 'pico': []}):
            with self.subTest(data=data):
                guard = ControlGuard(lambda request: {'ok': True, 'data': data}, 'RTLA')
                with self.assertRaises(RuntimeError):
                    guard.check()
        self.assertFalse(any(r['op'] in ('arm', 'recover', 'lease') for r in requests))


if __name__ == '__main__':
    unittest.main()
