"""Numerical FFT, policy-mask and RAM/persistence boundary regressions."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError:
    np = None

from srrx.spectrum import (DEFAULT_RING_BYTES, FRAME_FIELDS, GUARD_BINS, MASKED_BANDS_HZ,
                           MAX_RING_BYTES, MAX_RING_CHUNKS, SampleRing, SpectrumDependencyError,
                           SpectrumError, SpectrumProcessor, append_survey,
                           mask_frame, validate_frame)

GUARD_HZ = GUARD_BINS * 100.0  # raw_frame bins are 100 Hz wide


def raw_frame(center=100_000_000.0, rate=1600.0, size=16):
    return {'v': 1, 'kind': 'spectrum', 'center_hz': center, 'sample_rate_hz': rate,
            'fft_size': size, 'power_dbfs': [-42.0] * size, 'valid': [True] * size,
            'relative_frequency_hz': [(i - size // 2) * (rate / size) for i in range(size)],
            'source': 'SIMULATION', 'sample_count': size}


class FrameBoundaryTests(unittest.TestCase):
    def test_exact_inclusive_lower_and_upper_bandwidth_edges(self):
        for lower, upper in MASKED_BANDS_HZ:
            with self.subTest(band=(lower, upper), edge='lower'):
                # Center bin's upper edge plus the leakage guard lands exactly on lower.
                frame = mask_frame(raw_frame(lower - 50.0 - GUARD_HZ))
                self.assertFalse(frame['valid'][8])
                self.assertIsNone(frame['power_dbfs'][8])
                self.assertTrue(frame['valid'][7])
            with self.subTest(band=(lower, upper), edge='upper'):
                frame = mask_frame(raw_frame(upper + 50.0 + GUARD_HZ))
                self.assertFalse(frame['valid'][8])
                self.assertTrue(frame['valid'][9])

    def test_wrapped_nyquist_half_bin_is_masked_at_upper_capture_edge(self):
        for lower, _ in MASKED_BANDS_HZ:
            # Fs/2=800Hz; guarded upper capture edge is25Hz inside the prohibited band.
            # Last non-Nyquist bin's guarded edge is still25Hz below it; Nyquist wraps both ends.
            frame = mask_frame(raw_frame(lower - 775.0 - GUARD_HZ))
            self.assertFalse(frame['valid'][0])
            self.assertIsNone(frame['power_dbfs'][0])
            self.assertTrue(frame['valid'][-1])

    def test_cospas_sarsat_distress_bands_are_mandatory_no_data(self):
        # STACK.md v2: 406.0-406.1 MHz and 1544.0-1545.0 MHz are masked as no data.
        self.assertIn((406_000_000.0, 406_100_000.0), MASKED_BANDS_HZ)
        self.assertTrue(any(lower <= 1_544_000_000.0 and 1_545_000_000.0 <= upper
                            for lower, upper in MASKED_BANDS_HZ))
        for center in (406_001_000.0, 406_050_000.0, 406_099_000.0, 1_544_500_000.0):
            with self.subTest(center=center):
                frame = raw_frame(center)
                frame['source'] = 'HARDWARE'
                safe = mask_frame(frame)
                self.assertFalse(any(safe['valid']))
                self.assertEqual(safe['power_dbfs'], [None] * 16)
                with self.assertRaises(SpectrumError):
                    validate_frame(frame)

    def test_radiosonde_survey_keeps_405_9_but_blanks_beacon_uplink(self):
        # A 2 MS/s radiosonde survey centred at 405.5 MHz spans 404.5-406.5 MHz.
        size, rate, center = 1024, 2_000_000.0, 405_500_000.0
        frame = raw_frame(center, rate, size)
        frame['source'] = 'HARDWARE'
        safe = mask_frame(frame)
        width = rate / size
        guard = GUARD_BINS * width  # leakage guard beyond each band edge
        for index, relative in enumerate(safe['relative_frequency_hz']):
            low = center + relative - width / 2 - guard
            high = center + relative + width / 2 + guard
            touches = low <= 406_100_000.0 and high >= 406_000_000.0
            with self.subTest(bin=index):
                self.assertEqual(safe['valid'][index], not touches)
                if touches:
                    self.assertIsNone(safe['power_dbfs'][index])
        # Bins clear of 406.0-406.1 MHz plus the guard (405.9 MHz, 406.2 MHz) stay valid.
        def bin_at(hz):
            return round((hz - center) / width) + size // 2
        self.assertTrue(safe['valid'][bin_at(405_900_000.0)])
        self.assertTrue(safe['valid'][bin_at(406_200_000.0)])
        self.assertFalse(safe['valid'][bin_at(406_050_000.0)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'survey.jsonl'
            saved = append_survey(path, frame)
            self.assertEqual(saved, safe)
            stored = json.loads(path.read_text())
            self.assertIsNone(stored['power_dbfs'][bin_at(406_050_000.0)])

    def test_negative_absolute_mirror_of_vlf_band_is_masked(self):
        # Center9kHz, Fs192kHz: the capture crosses0Hz and |f| falls in3..30kHz.
        frame = mask_frame(raw_frame(9000.0, 192000.0, 1024))
        width = 192000.0 / 1024
        guard = GUARD_BINS * width
        for f, flag, power in zip(frame['relative_frequency_hz'], frame['valid'], frame['power_dbfs']):
            low, high = 9000.0 + f - width / 2 - guard, 9000.0 + f + width / 2 + guard
            if low <= -3000.0 and high >= -30000.0:
                self.assertFalse(flag)
                self.assertIsNone(power)
        valid = [9000.0 + f for f, flag in zip(frame['relative_frequency_hz'], frame['valid']) if flag]
        self.assertTrue(any(f < -40000 for f in valid) and any(f > 40000 for f in valid))
        self.assertFalse(any(1500 < abs(f) < 31500 for f in valid))

    def test_forged_valid_flags_are_remasked_and_strict_validator_rejects_them(self):
        original = raw_frame(300e6)
        untouched = copy.deepcopy(original)
        with self.assertRaises(SpectrumError):
            validate_frame(original)
        safe = mask_frame(original)
        self.assertFalse(any(safe['valid']))
        self.assertEqual(safe['power_dbfs'], [None] * 16)
        self.assertEqual(validate_frame(safe), safe)
        self.assertEqual(original, untouched)

    def test_caller_invalid_gap_never_reenabled_or_interpolated(self):
        original = raw_frame()
        original['valid'][5] = False
        safe = mask_frame(original)
        self.assertFalse(safe['valid'][5])
        self.assertIsNone(safe['power_dbfs'][5])
        self.assertTrue(safe['valid'][4] and safe['valid'][6])
        with self.assertRaises(SpectrumError):
            validate_frame(original)  # invalid finite power is not canonical

    def test_incomplete_sample_count_is_always_no_data(self):
        frame = raw_frame()
        frame['sample_count'] = 15
        safe = mask_frame(frame)
        self.assertFalse(any(safe['valid']))
        self.assertEqual(safe['power_dbfs'], [None] * 16)
        with self.assertRaises(SpectrumError):
            validate_frame(frame)

    def test_frequency_geometry_cannot_be_spoofed_to_bypass_mask(self):
        frame = raw_frame(300e6)
        frame['relative_frequency_hz'] = [v - 200e6 for v in frame['relative_frequency_hz']]
        with self.assertRaises(SpectrumError):
            mask_frame(frame)

    def test_bad_schema_types_nonfinite_and_extra_private_fields_rejected(self):
        changes = [('v', True), ('kind', 'iq'), ('center_hz', -1), ('center_hz', float('inf')),
                   ('sample_rate_hz', 0), ('sample_rate_hz', float('nan')), ('fft_size', True),
                   ('fft_size', 17), ('fft_size', 2**21), ('sample_count', -1), ('sample_count', True),
                   ('sample_count', 17), ('source', 'guessed'), ('source', True),
                   ('power_dbfs', [-1.0] * 15), ('valid', [1] * 16),
                   ('power_dbfs', [float('nan')] * 16), ('power_dbfs', [float('inf')] * 16)]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                frame = raw_frame()
                frame[key] = value
                with self.assertRaises(SpectrumError):
                    mask_frame(frame)
        for extra in ('raw_iq', 'samples', 'gnss_position', 'emitter_id', 'annotation'):
            frame = raw_frame()
            frame[extra] = [1, 2, 3]
            with self.assertRaises(SpectrumError):
                mask_frame(frame)

    def test_extreme_frequency_geometry_rejected_without_allocation(self):
        for center, rate in ((1e308, 1e308), (0, 5e-324), (True, 1000)):
            frame = raw_frame()
            frame['center_hz'], frame['sample_rate_hz'] = center, rate
            with self.assertRaises(SpectrumError):
                mask_frame(frame)

    def test_export_applies_masks_before_any_write_and_never_includes_raw_iq(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'survey.jsonl'
            forged = raw_frame(1_575e6)
            forged['power_dbfs'] = [123.456] * 16
            result = append_survey(path, forged)
            saved = json.loads(path.read_text())
            self.assertEqual(saved, result)
            self.assertEqual(set(saved), FRAME_FIELDS)
            self.assertNotIn('123.456', path.read_text())
            self.assertFalse(any(saved['valid']))
            append_survey(path, raw_frame())
            self.assertEqual(len(path.read_text().splitlines()), 2)
            before = path.read_bytes()
            bad = raw_frame()
            bad['raw_iq'] = [[.1, .2]]
            with self.assertRaises(SpectrumError):
                append_survey(path, bad)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['survey.jsonl'])

    def test_missing_numpy_is_explicit_while_mask_helpers_still_work(self):
        with patch('srrx.spectrum._np', None):
            with self.assertRaisesRegex(SpectrumDependencyError, 'NumPy'):
                SpectrumProcessor()
            with self.assertRaises(SpectrumDependencyError):
                SampleRing()
            self.assertEqual(len(validate_frame(mask_frame(raw_frame()))['valid']), 16)


@unittest.skipIf(np is None, 'Optional NumPy dependency is not installed')
class NumericalSpectrumTests(unittest.TestCase):
    def test_real_complex_tone_frequency_and_minus6dbfs_amplitude(self):
        n = 1024
        samples = .5 * np.exp(2j * np.pi * 31 * np.arange(n) / n)
        frame = SpectrumProcessor(n).process(samples, 145e6, 1024e3)
        peak = max(range(n), key=lambda i: frame['power_dbfs'][i])
        self.assertEqual(frame['relative_frequency_hz'][peak], 31e3)
        self.assertAlmostEqual(frame['power_dbfs'][peak], 20 * math.log10(.5), places=5)
        self.assertEqual(frame['sample_count'], n)
        self.assertTrue(all(frame['valid']))

    def test_negative_tone_and_unit_complex_fullscale(self):
        n = 256
        samples = np.exp(-2j * np.pi * 17 * np.arange(n) / n)
        frame = SpectrumProcessor(n).process(samples, 100e6, 256e3)
        peak = max(range(n), key=lambda i: frame['power_dbfs'][i])
        self.assertEqual(frame['relative_frequency_hz'][peak], -17e3)
        self.assertAlmostEqual(frame['power_dbfs'][peak], 0, places=5)

    def test_zero_signal_has_finite_floor_and_no_nan_json(self):
        frame = SpectrumProcessor(32).process(np.zeros(32), 100e6, 32000)
        self.assertEqual(frame['power_dbfs'], [-300.0] * 32)
        json.dumps(frame, allow_nan=False)

    def test_chunks_accumulate_but_no_zero_padding_fakes_complete_data(self):
        processor = SpectrumProcessor(16, capacity_bytes=128, chunk_samples=3)
        partial = processor.process(np.ones(8), 100e6, 16000)
        self.assertEqual(partial['sample_count'], 8)
        self.assertFalse(any(partial['valid']))
        self.assertEqual(partial['power_dbfs'], [None] * 16)
        complete = processor.process(np.ones(8), 100e6, 16000)
        self.assertEqual(complete['sample_count'], 16)
        self.assertTrue(all(complete['valid']))

    def test_no_new_samples_never_republishes_a_cached_fft(self):
        processor = SpectrumProcessor(16)
        processor.process(np.ones(16), 100e6, 16000)
        empty = processor.process([], 100e6, 16000)
        self.assertEqual(empty['sample_count'], 0)
        self.assertFalse(any(empty['valid']))
        self.assertEqual(empty['power_dbfs'], [None] * 16)

    def test_tuning_rate_and_source_changes_flush_previous_history(self):
        for next_center, next_rate, next_source in ((101e6, 16000, 'SIMULATION'),
                                                   (100e6, 32000, 'SIMULATION'),
                                                   (100e6, 16000, 'HARDWARE')):
            with self.subTest(context=(next_center, next_rate, next_source)):
                processor = SpectrumProcessor(16)
                processor.process(np.ones(8), 100e6, 16000)
                frame = processor.process(np.ones(8), next_center, next_rate, next_source)
                self.assertEqual(frame['sample_count'], 8)
                self.assertFalse(any(frame['valid']))
                self.assertEqual((frame['center_hz'], frame['sample_rate_hz'], frame['source']),
                                 (next_center, next_rate, next_source))

    def test_all_three_forbidden_bands_mask_the_actual_fft_result(self):
        for center, rate in ((15e3, 2000), (300e6, 1e6), (1575e6, 1e6)):
            with self.subTest(center=center):
                frame = SpectrumProcessor(16).process(np.ones(16), center, rate, 'HARDWARE')
                self.assertFalse(any(frame['valid']))
                self.assertEqual(frame['power_dbfs'], [None] * 16)
                self.assertEqual(frame['center_hz'], center)
                self.assertEqual(frame['sample_rate_hz'], rate)
                self.assertEqual(frame['source'], 'HARDWARE')

    def test_mixed_band_keeps_original_hardware_frequency_coverage(self):
        frame = SpectrumProcessor(64).process(np.ones(64), 225e6, 1.6e6, 'HARDWARE')
        self.assertTrue(any(frame['valid']))
        self.assertFalse(all(frame['valid']))
        self.assertEqual(frame['relative_frequency_hz'][0], -800000)
        self.assertEqual(frame['relative_frequency_hz'][-1], 775000)
        self.assertEqual(frame['sample_rate_hz'], 1.6e6)

    def test_strong_emitter_inside_band_edge_does_not_leak_into_valid_bins(self):
        n, rate, center = 1024, 1.024e6, 224.9e6
        tone = .9 * np.exp(2j * np.pi * (225.0006e6 - center) / rate * np.arange(n))
        frame = SpectrumProcessor(n).process(tone, center, rate, 'HARDWARE')
        valid = [p for p, flag in zip(frame['power_dbfs'], frame['valid']) if flag]
        self.assertGreater(len(valid), n // 2)
        # Unguarded, the 224.999MHz neighbour read about-19dBFS; now the guard masks it.
        self.assertFalse(frame['valid'][n // 2 + 99])
        self.assertLess(max(valid), -60)

    def test_invalid_samples_fail_and_clear_buffer(self):
        bad = ([complex(float('nan'), 0)] * 16, [float('inf')] * 16,
               np.ones((4, 4)), np.array([True] * 16), ['text'] * 16,
               np.array([1e300] * 16), iter(range(16)))
        for samples in bad:
            with self.subTest(kind=type(samples).__name__):
                processor = SpectrumProcessor(16)
                processor.process(np.ones(16), 100e6, 16000)
                with self.assertRaises(SpectrumError):
                    processor.process(samples, 100e6, 16000)
                self.assertEqual(len(processor.ring), 0)

    def test_ring_evicts_exact_oldest_samples_without_retaining_big_views(self):
        ring = SampleRing(capacity_bytes=256, chunk_samples=11)
        for start in range(0, 500, 17):
            values = np.arange(start, start + 17)
            ring.append(values)
            self.assertLessEqual(ring.allocated_bytes, 256)
            self.assertLessEqual(len(ring), 32)
            self.assertTrue(all(chunk.base is None for chunk in ring._chunks))
        np.testing.assert_array_equal(ring.tail(32).real, np.arange(478, 510))
        ring.clear()
        self.assertEqual(ring.allocated_bytes, 0)

    def test_tiny_append_metadata_is_bounded_as_well_as_iq_payload(self):
        ring = SampleRing(capacity_bytes=1024**2, chunk_samples=1)
        for i in range(MAX_RING_CHUNKS + 20):
            ring.append([i])
        self.assertLessEqual(ring.chunk_count, MAX_RING_CHUNKS)
        self.assertLessEqual(ring.allocated_bytes, ring.capacity_bytes)
        self.assertEqual(ring.tail(1)[0].real, MAX_RING_CHUNKS + 19)

    def test_input_arrays_are_not_retained_by_reference(self):
        source = np.arange(16, dtype=np.complex64)
        ring = SampleRing(128, 5)
        ring.append(source)
        source[:] = -99
        np.testing.assert_array_equal(ring.tail(16), np.arange(16))

    def test_capacity_bounds_and_4gib_is_lazy_not_allocated(self):
        for capacity in (0, True, 15, MAX_RING_BYTES + 8):
            with self.subTest(capacity=capacity):
                with self.assertRaises(SpectrumError):
                    SampleRing(capacity)
        with self.assertRaises(SpectrumError):
            SpectrumProcessor(1024, capacity_bytes=128)
        ring = SampleRing(MAX_RING_BYTES)
        self.assertEqual(ring.allocated_bytes, 0)
        self.assertEqual(ring.capacity_bytes, MAX_RING_BYTES)
        self.assertEqual(SampleRing().capacity_bytes, DEFAULT_RING_BYTES)

    def test_fft_and_ring_have_no_persistence_calls(self):
        with patch.object(np, 'save', side_effect=AssertionError('raw persistence')) as save, \
             patch.object(np, 'savez', side_effect=AssertionError('raw persistence')) as savez, \
             patch.object(np, 'memmap', side_effect=AssertionError('disk-backed ring')) as memmap:
            processor = SpectrumProcessor(16)
            frame = processor.process(np.ones(32), 100e6, 16000)
            self.assertEqual(set(frame), FRAME_FIELDS)
            processor.clear()
            save.assert_not_called()
            savez.assert_not_called()
            memmap.assert_not_called()


if __name__ == '__main__':
    unittest.main()
