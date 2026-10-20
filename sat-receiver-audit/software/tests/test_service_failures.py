"""Adversarial host/Pico integration checks; no devices or acceptance fabricated.

The fake clock drives the actual Engine, SimLink wire codecs and Pico Supervisor.
A separate smoke test uses the real Unix socket service in a child process.
"""
import copy
import json
import os
from pathlib import Path
import socket
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from srrx.daemon import MAX_REQUEST, Server, request_once
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SimLink
from srrx.wire import FrameDecoder, encode_frame

PROJECT = Path(__file__).resolve().parents[2]


class FaultLink:
    """Fault injection around the real model transport, not a second controller."""
    def __init__(self):
        self.delegate = SimLink(PROJECT)
        self.freeze_status = False
        self.silence_status = False
        self.drop_hb = False
        self.fail_hb = False
        self.last_frames = []
        self.injected = []
        self.sent = []

    def send(self, frame, now_ms=None):
        self.sent.append(copy.deepcopy(frame))
        if frame['t'] == 'HB':
            if self.fail_hb:
                raise OSError('injected UART write failure')
            if self.drop_hb:
                return
        self.delegate.send(frame, now_ms)

    def poll(self, now_ms):
        actual = self.delegate.poll(now_ms)
        if self.injected:
            result, self.injected = self.injected, []
            return result
        if self.silence_status:
            return []
        if self.freeze_status:
            return copy.deepcopy(self.last_frames)
        if actual:
            self.last_frames = copy.deepcopy(actual)
        return actual

    def inject_status(self, engine, **changes):
        status = dict(engine.pico, **changes)
        frame = {'v': 1, 't': 'STATUS', 's': engine.session,
                 'q': engine.rx_seq + 100, 'p': status}
        # Prove the payload is accepted by the actual UART codec before injecting.
        self.injected.extend(FrameDecoder().feed(encode_frame(frame)))
        assert self.injected

    def close(self):
        self.delegate.close()


class EngineFailureTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith('DCS_')})
        self.link = FaultLink()
        self.engine = Engine(self.hardware, self.link, simulated=True)
        self.now = 0
        self.engine.tick(self.now)

    def tearDown(self):
        self.engine.close()

    def advance(self, target):
        while self.now < target:
            self.now = min(target, self.now + 20)
            self.engine.tick(self.now)

    def arm(self):
        self.assertTrue(self.engine.request({'op': 'arm', '_owner': 'operator-A'})['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())
        self.assertTrue(self.engine.request({'op': 'control', 'name': 'EN_LNA1',
                                              'value': True, '_owner': 'operator-A'})['ok'])
        self.assertTrue(self.hardware.outputs['EN_LNA1'])

    def assert_safe(self):
        self.assertFalse(self.engine.policy.armed)
        self.assertTrue(self.hardware.outputs['CHG_INHIBIT'])
        self.assertFalse(any(value for name, value in self.hardware.outputs.items() if name != 'CHG_INHIBIT'))

    def assert_stays_latched(self, milliseconds=1000):
        self.advance(self.now + milliseconds)
        self.assert_safe()
        self.assertFalse(self.engine.request({'op': 'control', 'name': 'EN_LNA1',
                                               'value': True, '_owner': 'operator-A'})['ok'])

    def test_default_simulation_is_never_hardware_qualification(self):
        self.arm()
        self.assertEqual(self.engine.status()['mode'], 'SIMULATION')
        self.assertFalse(self.engine.status()['hardware_qualified'])
        self.assertIsNone(self.engine.acceptance)

    def test_stale_pico_status_trips_before_independent_heartbeat_timeout(self):
        self.arm()
        self.link.silence_status = True
        self.advance(self.now + 520)
        self.assert_safe()
        self.assertIn('pico_status_timeout', self.engine.last_error)
        self.link.silence_status = False
        self.assert_stays_latched()

    def test_replayed_status_does_not_refresh_freshness(self):
        self.arm()
        last_fresh = self.engine.last_status_ms
        self.link.freeze_status = True
        self.advance(self.now + 520)
        self.assertEqual(self.engine.last_status_ms, last_fresh)
        self.assert_safe()
        self.link.freeze_status = False
        self.assert_stays_latched()

    def test_one_way_host_heartbeat_loss_asserts_pico_reset(self):
        self.arm()
        self.link.drop_hb = True
        self.advance(self.now + 800)
        self.assertTrue(self.link.delegate.model.outputs['mcp_reset'])
        self.assertFalse(self.link.delegate.model.outputs['disp_en'])
        self.assert_safe()
        self.link.drop_hb = False
        self.assert_stays_latched()

    def test_uart_write_failure_disables_and_never_auto_recovers(self):
        self.arm()
        self.link.fail_hb = True
        self.advance(self.now + 220)
        self.assert_safe()
        self.assertIn('UART write failure', self.engine.last_error)
        self.link.fail_hb = False
        self.assert_stays_latched()

    def test_gpio_read_failure_disables_then_restored_io_does_not_rearm(self):
        self.arm()
        with patch.object(self.hardware, 'read_inputs', side_effect=OSError('injected I2C read failure')):
            self.advance(self.now + 20)
        self.assert_safe()
        self.assertIn('I2C read failure', self.engine.last_error)
        self.assert_stays_latched()

    def test_physical_fault_clear_does_not_clear_host_latch(self):
        self.arm()
        self.hardware.set_inputs({'FAULT_LNA1': False})
        self.advance(self.now + 20)
        self.assert_safe()
        self.hardware.set_inputs({'FAULT_LNA1': True})
        self.assert_stays_latched()

    def test_explicit_recovery_arms_without_restoring_previous_enabled_loads(self):
        self.arm()
        self.hardware.set_inputs({'FAULT_LNA1': False})
        self.advance(self.now + 20)
        self.hardware.set_inputs({'FAULT_LNA1': True})
        self.advance(self.now + 200)
        self.assert_safe()
        self.assertTrue(self.engine.request({'op': 'recover', '_owner': 'operator-A'})['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())
        self.assertFalse(any(v for n, v in self.hardware.outputs.items() if n != 'CHG_INHIBIT'))

    def test_lease_expiry_and_late_renewal_never_rearm(self):
        self.arm()
        deadline = self.engine.policy.lease_deadline_ms
        self.advance(deadline)
        self.assert_safe()
        self.engine.request({'op': 'lease', 'value': {'ttl_ms': 5000}, '_owner': 'operator-A'})
        self.assert_stays_latched()

    def test_owner_cannot_be_spoofed_inside_lease_value_or_steal_active_control(self):
        self.arm()
        self.assertFalse(self.engine.request({'op': 'lease', 'value': {'ttl_ms': 5000, 'owner': 'operator-A'}, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.engine.request({'op': 'control', 'name': 'EN_LNA2', 'value': True, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.hardware.outputs['EN_LNA2'])
        # Another client may always request de-energizing an output.
        self.assertTrue(self.engine.request({'op': 'control', 'name': 'EN_LNA1', 'value': False, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.hardware.outputs['EN_LNA1'])

    def test_codec_valid_malformed_status_and_contradictory_active_fail_closed(self):
        for changes in ({'state': []}, {'state': {}}, {'mcp_reset': 'false'},
                        {'mcp_reset': True}, {'calibration_valid': False},
                        {'hardware_commissioned': False}, {'q6a_on': False}, {'hb_fresh': False}):
            with self.subTest(changes=changes):
                # Each subcase gets a new real model/engine because recovery is explicit.
                hardware = SimHardware()
                link = FaultLink()
                engine = Engine(hardware, link, simulated=True)
                try:
                    engine.tick(0)
                    self.assertTrue(engine.request({'op': 'arm'})['ok'])
                    for now in range(20, 821, 20):
                        engine.tick(now)
                    self.assertTrue(engine.policy.armed)
                    self.assertTrue(engine.request({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
                    link.inject_status(engine, **changes)
                    engine.tick(840)  # Must not raise TypeError for codec-valid payloads.
                    self.assertFalse(engine.policy.armed)
                    self.assertFalse(hardware.outputs['EN_LNA1'])
                    self.assertTrue(hardware.outputs['CHG_INHIBIT'])
                finally:
                    engine.close()

    def test_pico_new_session_revokes_old_permission(self):
        self.arm()
        previous = self.engine.session
        self.link.delegate.model._trip('injected Pico reset')
        self.advance(self.now + 120)
        self.assertNotEqual(self.engine.session, previous)
        self.assert_safe()
        self.assert_stays_latched()

    def test_close_is_idempotent_and_deenergizes(self):
        self.arm()
        self.engine.close()
        self.engine.close()
        self.assert_safe()
        self.assertTrue(self.hardware.closed)

    def test_rpc_parser_rejects_malformed_types_and_server_overrides_owner(self):
        server = object.__new__(Server)
        server.engine = self.engine
        for payload in (b'not json', b'[]', b'{"op":[]}',
                        b'{"op":"lease","value":{"ttl_ms":NaN}}',
                        b'{"op":"control","name":"EN_LNA1","value":1}',
                        b'{"op":"route","receiver":[],"value":"RF2"}',
                        b'[' * 1200 + b']' * 1200):
            with self.subTest(payload=payload[:60]):
                state = {'rx': bytearray(payload + b'\n'), 'uid': 1234}
                server._request(state)
                self.assertFalse(json.loads(state['tx'])['ok'])
                self.assert_safe()
        # The parser boundary uses its peer UID, not caller-controlled _owner.
        request = {'op': 'lease', 'value': {'ttl_ms': 1000}, '_owner': 'uid:0'}
        state = {'rx': bytearray(json.dumps(request).encode() + b'\n'), 'uid': 1234}
        server._request(state)
        self.assertTrue(json.loads(state['tx'])['ok'])
        self.assertEqual(self.engine.policy.owner, 'uid:1234')
        self.assert_safe()

    def test_live_hardware_identity_and_calibration_binding_before_arm(self):
        class PhysicalBoundaryFake(SimHardware):
            physical = True
        class IdentityLink(FaultLink):
            def __init__(self, serial, crc):
                super().__init__()
                self.serial, self.crc = serial, crc
            def poll(self, now_ms):
                frames = super().poll(now_ms)
                for frame in frames:
                    if frame['t'] == 'HELLO':
                        frame['p'].update(serial=self.serial, calibration_crc32=self.crc)
                return frames
        # This is an in-memory Engine unit fixture, never a commissioned file.
        acceptance = {'branch_limits': copy.deepcopy(self.engine.policy.limits),
                      'lab5_budget': {'always_on_a': .6, 'max_lab5_a': 3.2},
                      'pico_serial': 'e661000000001234',
                      'battery_adc': {'record': {'crc32': '7bd013af'}}}
        for serial, crc, allowed in ((None, None, False),
                                     ('e661000000005678', '7bd013af', False),
                                     ('e661000000001234', '00000000', False),
                                     ('e661000000001234', '7bd013af', True)):
            with self.subTest(serial=serial, crc=crc):
                hardware, link = PhysicalBoundaryFake(), IdentityLink(serial, crc)
                engine = Engine(hardware, link, simulated=False, acceptance=acceptance)
                try:
                    engine.tick(0)
                    result = engine.request({'op': 'arm'})
                    self.assertEqual(result['ok'], allowed, result)
                    self.assertEqual(any(f['t'] == 'ARM' for f in link.sent), allowed)
                    self.assertEqual(engine.status()['live_identity_verified'], allowed)
                    self.assertFalse(hardware.initialized)  # No MCP write before full handshake.
                finally:
                    engine.close()

    def test_close_still_releases_hardware_and_telemetry_when_link_close_raises(self):
        class Reader:
            closed = False
            def close(self):
                self.closed = True
        reader = Reader()
        self.engine.telemetry_reader = reader
        self.arm()
        with patch.object(self.link, 'close', side_effect=OSError('injected link-close error')):
            with self.assertRaises(OSError):
                self.engine.close()
        self.assertTrue(self.hardware.closed)
        self.assertTrue(reader.closed)
        self.assertTrue(self.engine.closed)
        self.assert_safe()

    def test_hardware_mode_never_substitutes_simulation_acceptance(self):
        # Physical-like fake verifies refusal without touching a Linux device.
        class PhysicalBoundaryFake(SimHardware):
            physical = True
        hardware = PhysicalBoundaryFake()
        link = FaultLink()
        engine = Engine(hardware, link, simulated=False, acceptance=None)
        try:
            engine.tick(0)
            self.assertFalse(engine.request({'op': 'arm'})['ok'])
            self.assertFalse(engine.request({'op': 'sim', 'name': 'drop_link', 'value': True})['ok'])
            self.assertFalse(hardware.initialized)
            self.assertFalse(engine.status()['hardware_qualified'])
            self.assertEqual(engine.policy.telemetry, {})
            self.assertFalse(any(hardware.outputs[n] for n in hardware.outputs if n.startswith('EN_')))
        finally:
            engine.close()


class StdioServiceIntegrationTests(unittest.TestCase):
    def test_real_child_service_arms_trips_on_link_loss_and_stays_latched(self):
        env = dict(os.environ, PYTHONPATH=str(PROJECT / 'software'))
        process = subprocess.Popen([sys.executable, '-m', 'srrx.daemon', '--simulate',
                                    '--stdio', '--project', str(PROJECT)], cwd=PROJECT,
                                   env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, bufsize=1)
        def rpc(request):
            process.stdin.write(json.dumps(request) + '\n')
            process.stdin.flush()
            ready, _, _ = select.select([process.stdout], [], [], 3)
            self.assertTrue(ready, 'child control response deadline exceeded')
            line = process.stdout.readline()
            self.assertTrue(line, 'child exited before a JSON response')
            return json.loads(line)
        def wait_status(predicate, timeout=3):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                status = rpc({'op': 'status'})['data']
                if predicate(status):
                    return status
                time.sleep(.03)
            self.fail('child state-transition deadline exceeded')
        try:
            status = rpc({'op': 'status'})['data']
            self.assertEqual(status['mode'], 'SIMULATION')
            self.assertFalse(status['hardware_qualified'])
            self.assertFalse(status['policy']['armed'])
            self.assertTrue(rpc({'op': 'arm'})['ok'])
            wait_status(lambda s: s['policy']['armed'])
            self.assertTrue(rpc({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
            self.assertTrue(rpc({'op': 'status'})['data']['policy']['outputs']['EN_LNA1'])
            self.assertFalse(rpc({'op': []})['ok'])
            self.assertTrue(rpc({'op': 'sim', 'name': 'drop_link', 'value': True})['ok'])
            status = wait_status(lambda s: not s['policy']['armed'])
            self.assertFalse(any(v for n, v in status['policy']['outputs'].items() if n != 'CHG_INHIBIT'))
            self.assertTrue(rpc({'op': 'sim', 'name': 'drop_link', 'value': False})['ok'])
            time.sleep(.25)
            status = rpc({'op': 'status'})['data']
            self.assertFalse(status['policy']['armed'])
            self.assertFalse(rpc({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
            process.stdin.close()
            process.stdin = None
            stdout, stderr = process.communicate(timeout=4)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=2)


class UnixServiceFailureTests(unittest.TestCase):
    def test_invalid_rpc_is_bounded_and_service_remains_disarmed(self):
        try:
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except PermissionError as exc:
            self.skipTest('Execution environment forbids AF_UNIX socket creation: ' + str(exc))
        else:
            probe.close()
        with tempfile.TemporaryDirectory(prefix='srrx-rpc-') as directory:
            path = Path(directory) / 'ctl.sock'
            env = dict(os.environ, PYTHONPATH=str(PROJECT / 'software'))
            process = subprocess.Popen([sys.executable, '-m', 'srrx.daemon', '--simulate',
                                        '--project', str(PROJECT), '--socket', str(path)],
                                       cwd=PROJECT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            startup_complete = False
            try:
                # Cold ARM64 TCG startup is separate from all live RPC limits.
                deadline = time.monotonic() + 20
                while not path.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertIsNone(process.poll(), 'daemon exited before creating its socket')
                self.assertTrue(path.exists(), 'daemon socket startup timed out')
                startup_complete = True
                malformed = [b'not json\n', b'[]\n', b'{"op":[]}\n',
                             b'{"op":"lease","value":{"ttl_ms":NaN}}\n',
                             b'{"op":"control","name":"EN_LNA1","value":1}\n',
                             b'{"op":"route","receiver":[],"value":"RF2"}\n',
                             (b'[' * 1200) + (b']' * 1200) + b'\n',
                             b'x' * (MAX_REQUEST + 1) + b'\n']
                for data in malformed:
                    with self.subTest(data=data[:60]):
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                            client.settimeout(2)
                            client.connect(str(path))
                            client.sendall(data)
                            try:
                                reply = client.recv(8192)
                            except ConnectionResetError:
                                reply = b''  # Oversize input may be closed without a reply.
                        if reply:
                            self.assertFalse(json.loads(reply.split(b'\n', 1)[0])['ok'])
                        status = request_once(path, {'op': 'status'})['data']
                        self.assertEqual(status['mode'], 'SIMULATION')
                        self.assertFalse(status['hardware_qualified'])
                        self.assertFalse(status['policy']['armed'])
                        self.assertFalse(any(v for n, v in status['policy']['outputs'].items() if n != 'CHG_INHIBIT'))
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate(timeout=2)
                # Preserve the primary startup failure if SIGTERM arrived before
                # the child had installed its clean-shutdown signal handler.
                if startup_complete:
                    self.assertEqual(process.returncode, 0, stdout + stderr)
                self.assertFalse(path.exists(), 'clean service shutdown left the socket behind')


if __name__ == '__main__':
    unittest.main()
