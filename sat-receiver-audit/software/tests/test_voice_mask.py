"""srrx.voice_mask on synthetic IQ only; no result here is a recording or RF evidence."""
import importlib.util
import unittest
from unittest.mock import patch

from srrx import voice_mask
from srrx.spectrum import MASKED_BANDS_HZ

HAS_NUMPY = importlib.util.find_spec("numpy") is not None


def plan(**changes):
    entry = {"norad_id": 57166, "aos_utc": "2026-10-20T18:16:39.113Z", "los_utc": "2026-10-20T18:31:51.583Z"}
    value = {"time_verified": True, "passes": [entry, dict(entry, norad_id=90100)]}
    value.update(changes)
    return value


LRPT = {57166: [{"downlink_hz": 137.9e6, "bandwidth_hz": 115.2e3, "mode": "LRPT"}]}


def capture(np, centre, rate, voices=(), carriers=(), seed=1, size=1 << 15):
    rng = np.random.default_rng(seed)
    t = np.arange(size) / rate
    noise = (rng.standard_normal(size) + 1j * rng.standard_normal(size)) * 7e-4
    audio = .6 * np.sin(2 * np.pi * 400 * t) + .4 * np.sin(2 * np.pi * 1700 * t)
    signal = np.zeros(size, complex)
    for frequency in voices:
        signal += .1 * np.exp(1j * (2 * np.pi * (frequency - centre) * t + 2 * np.pi * 2500 * np.cumsum(audio) / rate))
    for frequency in carriers:
        signal += .01 * np.exp(2j * np.pi * (frequency - centre) * t)
    return (noise + signal).astype(np.complex64), noise


def band(np, samples, centre, rate, frequency, half):
    size, window, total = 2048, np.hanning(2048), np.zeros(2048)
    for start in range(0, samples.size - size + 1, size // 2):
        total += np.abs(np.fft.fftshift(np.fft.fft(samples[start:start + size] * window))) ** 2
    bins = np.abs(centre + (np.arange(size) - size // 2) * rate / size - frequency) <= half
    return total[bins].mean()


class FrequencyPlanTests(unittest.TestCase):
    def test_static_masks_and_voice_bands_are_the_specified_ones(self):
        self.assertEqual([(c, h) for _, c, h in voice_mask.STATIC_VOICE_MASKS],
                         [(437.8e6, 8e3), (436.795e6, 8e3), (145.8e6, 8e3)])
        bands = {name: (low, high) for low, high, name in voice_mask.VOICE_BANDS_HZ}
        self.assertEqual(bands["amateur_2m"], (144e6, 146e6))
        self.assertEqual(bands["amateur_70cm"], (430e6, 440e6))
        self.assertEqual(bands["pmr446"], (446.0e6, 446.2e6))
        self.assertEqual(bands["aeronautical_mobile_r"], (117.975e6, 137e6))
        self.assertEqual(bands["maritime_vhf"], (156e6, 162.05e6))
        # Weather-satellite and sonde downlinks stay outside every cut band.
        for frequency in (137.1e6, 137.9e6, 137.9125e6, 400.5e6, 403.0e6, 1698e6):
            self.assertFalse(voice_mask._touches(frequency, frequency, voice_mask._VOICE_HZ), frequency)

    def test_bin_rules(self):
        keep = lambda centre, rate, windows=(), bench=False: voice_mask.bin_keep(centre, rate, 64, windows, bench=bench)
        self.assertFalse(any(keep(137.5e6, 64e3)))  # allowlist only: no window, no bench -> nothing
        self.assertTrue(all(keep(137.5e6, 64e3, bench=True)))  # bench, no voice band
        self.assertFalse(any(keep(145.5e6, 64e3, bench=True)))  # amateur 2 m voice band
        self.assertFalse(any(keep(446.1e6, 64e3, ((446.0e6, 446.2e6),), bench=True)))  # a window never re-opens PMR446
        self.assertFalse(any(keep(433.5e6, 64e3, ((433.4e6, 433.6e6),))))  # 70 cm outside the satellite segment
        opened = keep(145.9e6, 64e3, ((145.89e6, 145.91e6),))
        self.assertTrue(any(opened) and not all(opened))  # a window inside 145.8-146 MHz re-opens its bins only
        # Static masks hold inside a window: +-8 kHz is cut, the rest of a satellite-segment window stays.
        for centre in (145.8e6, 437.8e6, 436.795e6):
            self.assertFalse(any(keep(centre, 16e3, ((centre - 1e5, centre + 1e5),))), centre)
        wider = keep(437.8e6, 64e3, ((437.7e6, 437.9e6),))
        self.assertEqual(sum(wider), 64 - 17)  # the 1 kHz bins centred -8..+8 kHz touch 437.792-437.808 MHz
        self.assertFalse(any(keep(300e6, 64e3, bench=True)))  # spectrum no-data band 225-400 MHz
        self.assertFalse(any(keep(406.05e6, 64e3, ((406.0e6, 406.1e6),), bench=True)))  # Cospas-Sarsat uplink
        self.assertIn((225e6, 400e6), MASKED_BANDS_HZ)
        # A bin is judged over its full width: the top bin ends at 117.975 MHz (aviation edge, inclusive) and
        # the even-FFT Nyquist bin 0 also covers the wrapped half-bin above the top one.
        edge = keep(117.975e6 - 31.5e3, 64e3, bench=True)
        self.assertEqual((edge[0], edge[1], edge[-2], edge[-1]), (False, True, True, False))
        with self.assertRaises(voice_mask.VoiceMaskError):
            keep(137.5e6, 64e3, ((2, 1),))
        with self.assertRaises(voice_mask.VoiceMaskError):
            voice_mask.bin_keep(137.5e6, 64e3, 100)
        with self.assertRaises(voice_mask.VoiceMaskError):
            voice_mask.bin_keep(True, 64e3)

    def test_plan_windows_follow_the_verified_plan_and_the_data_allowlist(self):
        windows = voice_mask.plan_windows(plan(), LRPT)
        self.assertEqual(len(windows), 1)  # 90100 has no allowlisted downlink
        start, end, low, high = windows[0]
        self.assertAlmostEqual(end - start, 912.47 + 120, places=2)  # AOS-60 s .. LOS+60 s
        half = 115.2e3 / 2 + 137.9e6 * 7000 / 299792458 + 20e3
        self.assertAlmostEqual(high - 137.9e6, half, places=3)
        self.assertAlmostEqual(137.9e6 - low, half, places=3)
        self.assertEqual(voice_mask.active_windows(windows, start + 1), ((low, high),))
        self.assertEqual(voice_mask.active_windows(windows, end + 1), ())
        for bad_plan in (plan(time_verified=False), plan(passes=None), plan(passes=[{"norad_id": "57166"}]),
                         plan(passes=[{"norad_id": 57166, "aos_utc": "2026-10-20T18:16:39", "los_utc": "2026-10-20T18:31:51Z"}])):
            with self.assertRaises(voice_mask.VoiceMaskError):
                voice_mask.plan_windows(bad_plan, LRPT)
        refusals = {"TRANSMITTER_MODE_NOT_DATA": {"downlink_hz": 145.8e6, "bandwidth_hz": 12e3, "mode": "FM"},
                    "DOWNLINK_IN_VOICE_BAND": {"downlink_hz": 446.00625e6, "bandwidth_hz": 12e3, "mode": "GMSK"},
                    "TRANSMITTER_ALLOWLIST": {"downlink_hz": 137.9e6, "bandwidth_hz": 0, "mode": "LRPT"}}
        for code, entry in refusals.items():
            with self.assertRaises(voice_mask.VoiceMaskError) as raised:
                voice_mask.plan_windows(plan(), {57166: [entry]})
            self.assertEqual(str(raised.exception), code)
        amateur = {57166: [{"downlink_hz": 437.775e6, "bandwidth_hz": 9.6e3, "mode": "GMSK"}]}
        self.assertEqual(len(voice_mask.plan_windows(plan(), amateur)), 1)  # 435-438 MHz satellite segment


@unittest.skipUnless(HAS_NUMPY, "optional NumPy is not installed")
class ExcisionTests(unittest.TestCase):
    def test_nfm_voice_is_cut_and_allowlisted_carriers_survive(self):
        import numpy as np
        lrpt = voice_mask.plan_windows(plan(), LRPT)
        for centre, rate, voices, windows, bench, carriers in (
                (145.65e6, 500e3, (145.5e6, 145.8e6), ((145.85e6, 145.87e6), (145.79e6, 145.81e6)), True, (145.86e6,)),
                (434.3e6, 2.048e6, (433.5e6,), ((435.17e6, 435.23e6),), True, (435.2e6,)),
                (446.05e6, 500e3, (446.00625e6,), ((445.99e6, 446.02e6),), False, ()),
                (137.9e6, 256e3, (), voice_mask.active_windows(lrpt, lrpt[0][0] + 100), False, (137.9e6,))):
            with self.subTest(centre=centre):
                samples, noise = capture(np, centre, rate, voices, carriers)
                out = voice_mask.excise(samples, centre, rate, windows, bench=bench)
                self.assertEqual((out.shape, out.dtype), (samples.shape, np.complex64))
                for frequency in voices:
                    self.assertGreater(band(np, samples, centre, rate, frequency, 6e3), 1e4 * band(np, noise, centre, rate, frequency, 6e3))
                    self.assertLess(band(np, out, centre, rate, frequency, 6e3), 1e-4 * band(np, noise, centre, rate, frequency, 6e3))
                for frequency in carriers:
                    ratio = band(np, out, centre, rate, frequency, 1e3) / band(np, samples, centre, rate, frequency, 1e3)
                    self.assertAlmostEqual(ratio, 1.0, delta=0.02)

    def test_streaming_push_equals_whole_capture_and_stopband_is_verified(self):
        import numpy as np
        samples, _ = capture(np, 145.65e6, 500e3, (145.5e6,), (145.86e6,))
        windows = ((145.85e6, 145.87e6),)
        whole = voice_mask.excise(samples, 145.65e6, 500e3, windows, bench=True)
        excisor = voice_mask.VoiceExcisor(145.65e6, 500e3, windows, bench=True)
        parts = [excisor.push(chunk) for chunk in np.array_split(np.concatenate((samples, np.zeros(excisor.DELAY, np.complex64))), 7)]
        streamed = np.concatenate(parts)[excisor.DELAY:]
        self.assertLess(np.max(np.abs(streamed - whole)), 1e-6)
        self.assertGreater(excisor.kept_bins, 0)
        response = np.abs(np.fft.fftshift(np.fft.fft(excisor.taps, 4 * voice_mask.MASK_FFT_SIZE))) ** 2
        keep = np.array(voice_mask.bin_keep(145.65e6, 500e3, voice_mask.MASK_FFT_SIZE, windows, bench=True))
        self.assertLess(response[4 * np.flatnonzero(~keep)].max(), 10 ** (voice_mask.STOPBAND_DB / 10))
        # A filter that cannot meet the stopband is refused, not used.
        with patch.object(voice_mask, "STOPBAND_DB", -400.0), self.assertRaises(voice_mask.VoiceMaskError):
            voice_mask.VoiceExcisor(145.65e6, 500e3, windows, bench=True)
        # Fully cut and fully kept captures: zeros, and a delayed copy.
        self.assertFalse(np.any(voice_mask.excise(samples, 446.05e6, 500e3, bench=True)))
        passed = voice_mask.excise(samples, 137.5e6, 500e3, bench=True)
        self.assertLess(np.max(np.abs(passed - samples)), 1e-6)
        for bad in (samples.real, samples.reshape(2, -1), np.full(4, np.nan + 0j)):
            with self.assertRaises(voice_mask.VoiceMaskError):
                excisor.push(bad)

    def test_without_numpy_planning_works_and_excision_refuses(self):
        with patch.object(voice_mask, "_np", None):
            self.assertTrue(all(voice_mask.bin_keep(137.5e6, 64e3, 64, bench=True)))
            with self.assertRaises(voice_mask.VoiceMaskDependencyError):
                voice_mask.excise([0j] * 8, 137.5e6, 64e3, bench=True)


if __name__ == "__main__":
    unittest.main()
