"""Raw-IQ voice excision for the narrow pass recorder (STACK.md:977, build/07 §23 row 14, ПОЛ-05).

Frequency planning in pure Python plus one NumPy filter. Nothing here records, demodulates
or classifies, and no writer calls it yet: the recorder is item IQ-1. A raw bin may be
written only inside an allowlisted window (a predicted pass of an allowlisted data
downlink: AOS-60 s .. LOS+60 s, downlink +-(bandwidth/2 + LEO Doppler + 20 kHz)) or in an
explicit bench/conducted capture. Independently of any window or NPU detector:

- the static voice masks 437.800 MHz (ISS repeater), 436.795 MHz (SO-50) and 145.800 MHz
  (ARISS) +-8 kHz are always cut. The ARISS SSTV-window exception of STACK.md:977 (live
  slowrxd, IQ only until speech is classified) is not implemented, so the mask holds there too;
- in the voice bands (VOICE_BANDS_HZ: amateur 144-146 and 430-440 MHz, PMR446, land mobile,
  marine VHF, aviation 117.975-137 MHz) every bin outside a window is cut, and a window
  re-opens a voice-band bin only inside the amateur-satellite segments 145.8-146 and 435-438 MHz;
- the spectrum no-data bands (srrx.spectrum.MASKED_BANDS_HZ, also mirrored below 0 Hz) are cut.

Excision is FFT-domain overlap-save. The multiplier is the FFT of a Kaiser-windowed
linear-phase FIR built from the kept bin runs after eroding them by the transition width,
so overlap-save is exact linear convolution and every cut band lies in the stopband; the
construction verifies the response there against STOPBAND_DB and refuses otherwise. The
land-mobile, marine and CB edges are a DRAFT ITU/CEPT table for the policy reviewer
(receive-only-policy.json stays DRAFT); a regional profile may widen the bands, never narrow them.
"""
from datetime import datetime, timezone
import math

from .spectrum import MASKED_BANDS_HZ

try:
    import numpy as _np
except ImportError:  # Frequency planning stays usable without NumPy.
    _np = None

STATIC_VOICE_MASKS = (  # (name, centre Hz, half-width Hz); the width is a design value (STACK.md:977)
    ("iss_fm_repeater", 437_800_000.0, 8_000.0),
    ("so50_fm", 436_795_000.0, 8_000.0),
    ("ariss_2m", 145_800_000.0, 8_000.0),
)
VOICE_BANDS_HZ = (  # (low, high, name), inclusive; land mobile, marine and CB are DRAFT edges
    (26_960_000.0, 27_410_000.0, "land_mobile_cb27"),
    (68_000_000.0, 87_500_000.0, "land_mobile_vhf_low"),
    (117_975_000.0, 137_000_000.0, "aeronautical_mobile_r"),
    (144_000_000.0, 146_000_000.0, "amateur_2m"),
    (146_000_000.0, 174_000_000.0, "land_mobile_vhf_high"),
    (156_000_000.0, 162_050_000.0, "maritime_vhf"),
    (406_100_000.0, 430_000_000.0, "land_mobile_uhf_low"),
    (430_000_000.0, 440_000_000.0, "amateur_70cm"),
    (440_000_000.0, 470_000_000.0, "land_mobile_uhf"),
    (446_000_000.0, 446_200_000.0, "pmr446"),
)
AMATEUR_SATELLITE_HZ = ((145_800_000.0, 146_000_000.0), (435_000_000.0, 438_000_000.0))
DATA_MODES = frozenset(("LRPT", "HRPT", "AHRPT", "APT", "BPSK", "QPSK", "OQPSK", "GMSK", "GFSK", "FSK",
                        "MSK", "AFSK", "CW"))
DOPPLER_VELOCITY_M_S = 7_000.0  # STACK.md:977: 3.2 kHz at 137.1 MHz
LIGHT_M_S = 299_792_458.0
WINDOW_MARGIN_HZ = 20_000.0
WINDOW_MARGIN_S = 60.0
MAX_WINDOWS = 64
MASK_FFT_SIZE = 8192
TAPS = 1023
KAISER_BETA = 10.0
STOPBAND_DB = -80.0
MAX_BLOCK_SAMPLES = 1 << 26
_STATIC_HZ = tuple((centre - half, centre + half) for _, centre, half in STATIC_VOICE_MASKS)
_VOICE_HZ = tuple((low, high) for low, high, _ in VOICE_BANDS_HZ)


class VoiceMaskError(ValueError):
    """Stable refusal code; never embeds sample values or file content."""


class VoiceMaskDependencyError(RuntimeError):
    pass


def _numpy():
    if _np is None:
        raise VoiceMaskDependencyError("NumPy is required for IQ excision; install the optional numpy dependency")
    return _np


def _finite(value, code):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise VoiceMaskError(code)
    return float(value)


def _geometry(center_hz, rate_hz, fft_size):
    center, rate = _finite(center_hz, "CAPTURE_GEOMETRY"), _finite(rate_hz, "CAPTURE_GEOMETRY")
    if (center < 0 or rate <= 0 or type(fft_size) is not int or not 16 <= fft_size <= 1 << 20
            or fft_size & (fft_size - 1)):
        raise VoiceMaskError("CAPTURE_GEOMETRY")
    return center, rate, fft_size


def _windows(windows):
    if type(windows) not in (tuple, list) or len(windows) > MAX_WINDOWS:
        raise VoiceMaskError("WINDOW_LIST")
    spans = []
    for window in windows:
        if type(window) not in (tuple, list) or len(window) != 2:
            raise VoiceMaskError("WINDOW_LIST")
        low, high = _finite(window[0], "WINDOW_LIST"), _finite(window[1], "WINDOW_LIST")
        if not 0 <= low < high:
            raise VoiceMaskError("WINDOW_LIST")
        spans.append((low, high))
    return spans


def _touches(low, high, bands):
    # A real RF input also appears at -f in complex baseband, so |f| is judged too.
    return any(a <= upper and b >= lower for a, b in ((low, high), (-high, -low)) for lower, upper in bands)


def _inside(low, high, spans):
    return any(a <= low and high <= b for a, b in spans)


def _permitted(low, high, spans, bench):
    if _touches(low, high, MASKED_BANDS_HZ) or _touches(low, high, _STATIC_HZ):
        return False
    window = _inside(low, high, spans)
    if not (bench or window):
        return False
    if _touches(low, high, _VOICE_HZ):
        return window and _inside(low, high, AMATEUR_SATELLITE_HZ)
    return True


def bin_keep(center_hz, rate_hz, fft_size=MASK_FFT_SIZE, windows=(), *, bench=False):
    """Write permission per bin in fftshift order (relative (i - n//2) * rate/n), before the
    filter guard. A bin is judged over its full width; the even-FFT Nyquist bin also over
    its wrapped upper half. windows are (low_hz, high_hz) spans active now (active_windows)."""
    center, rate, size = _geometry(center_hz, rate_hz, fft_size)
    spans, width = _windows(windows), rate / size
    keep = []
    for index in range(size):
        low = center + (index - size // 2) * width - width / 2
        intervals = [(low, low + width)] + ([(center + rate / 2 - width / 2, center + rate / 2 + width / 2)] if index == 0 else [])
        keep.append(all(_permitted(a, b, spans, bench) for a, b in intervals))
    return keep


def guard_bins(fft_size=MASK_FFT_SIZE):
    """Kaiser transition width of the FIR (Kaiser 1974 design formula) in mask bins, plus one."""
    attenuation = KAISER_BETA / 0.1102 + 8.7
    return math.ceil(fft_size * (attenuation - 8.0) / (2.285 * (TAPS - 1) * 2 * math.pi)) + 1


def _utc(text):
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        raise VoiceMaskError("PASS_PLAN_SCHEMA") from None
    if moment.utcoffset() is None or moment.utcoffset().total_seconds() != 0:
        raise VoiceMaskError("PASS_PLAN_SCHEMA")
    return moment.astimezone(timezone.utc).timestamp()


def _downlinks(transmitters):
    if not isinstance(transmitters, dict):
        raise VoiceMaskError("TRANSMITTER_ALLOWLIST")
    table = {}
    for norad, entries in transmitters.items():
        if type(norad) is not int or norad <= 0 or type(entries) not in (tuple, list):
            raise VoiceMaskError("TRANSMITTER_ALLOWLIST")
        for entry in entries:
            if type(entry) is not dict or set(entry) != {"downlink_hz", "bandwidth_hz", "mode"}:
                raise VoiceMaskError("TRANSMITTER_ALLOWLIST")
            frequency = _finite(entry["downlink_hz"], "TRANSMITTER_ALLOWLIST")
            bandwidth = _finite(entry["bandwidth_hz"], "TRANSMITTER_ALLOWLIST")
            if frequency <= 0 or not 0 < bandwidth <= 2e6:
                raise VoiceMaskError("TRANSMITTER_ALLOWLIST")
            if type(entry["mode"]) is not str or entry["mode"] not in DATA_MODES:
                raise VoiceMaskError("TRANSMITTER_MODE_NOT_DATA")
            if _touches(frequency, frequency, _VOICE_HZ) and not _inside(frequency, frequency, AMATEUR_SATELLITE_HZ):
                raise VoiceMaskError("DOWNLINK_IN_VOICE_BAND")
            table.setdefault(norad, []).append((frequency, bandwidth))
    return table


def plan_windows(plan, transmitters):
    """(start_s, end_s, low_hz, high_hz) per pass of an allowlisted data downlink, UTC epoch seconds.

    plan is a srrx.passes plan (validate_plan output) whose UTC is verified; transmitters maps a
    NORAD id to its downlinks {downlink_hz, bandwidth_hz, mode}. A non-data mode, a downlink in a
    voice band outside the amateur-satellite segments or an unverified plan clock is refused.
    """
    if type(plan) is not dict or plan.get("time_verified") is not True or type(plan.get("passes")) is not list:
        raise VoiceMaskError("VERIFIED_PASS_PLAN_REQUIRED")
    table, windows = _downlinks(transmitters), []
    for entry in plan["passes"]:
        if type(entry) is not dict or type(entry.get("norad_id")) is not int:
            raise VoiceMaskError("PASS_PLAN_SCHEMA")
        start, end = _utc(entry.get("aos_utc")), _utc(entry.get("los_utc"))
        if end < start:
            raise VoiceMaskError("PASS_PLAN_SCHEMA")
        for frequency, bandwidth in table.get(entry["norad_id"], ()):
            half = bandwidth / 2 + frequency * DOPPLER_VELOCITY_M_S / LIGHT_M_S + WINDOW_MARGIN_HZ
            windows.append((start - WINDOW_MARGIN_S, end + WINDOW_MARGIN_S, frequency - half, frequency + half))
    if len(windows) > MAX_WINDOWS * 32:
        raise VoiceMaskError("WINDOW_LIST")
    return tuple(sorted(windows))


def active_windows(windows, utc_s):
    """The (low_hz, high_hz) spans of plan_windows whose time range contains utc_s."""
    moment = _finite(utc_s, "WINDOW_TIME")
    return tuple((low, high) for start, end, low, high in windows if start <= moment <= end)


def _kept(np, keep):
    """Kept bins eroded by the transition guard (circularly: the spectrum repeats every rate)."""
    cut = ~keep
    eroded = cut.copy()
    for shift in range(1, guard_bins(keep.size) + 1):
        eroded |= np.roll(cut, shift) | np.roll(cut, -shift)
    return ~eroded


def _fir(np, kept):
    """Kaiser-windowed sum of ideal band-pass responses, one per run of kept bins."""
    size, taps = kept.size, np.zeros(TAPS, np.complex128)
    n = np.arange(TAPS) - (TAPS - 1) // 2
    edges = np.flatnonzero(np.diff(np.concatenate(([0], kept.astype(np.int8), [0]))))
    for first, stop in zip(edges[::2], edges[1::2]):
        low, high = (first - size // 2 - 0.5) / size, (stop - 1 - size // 2 + 0.5) / size
        with np.errstate(divide="ignore", invalid="ignore"):
            band = (np.exp(2j * np.pi * high * n) - np.exp(2j * np.pi * low * n)) / (2j * np.pi * n)
        band[n == 0] = high - low
        taps += band
    return taps * np.kaiser(TAPS, KAISER_BETA)


class VoiceExcisor:
    """Streaming overlap-save filter: push() returns as many samples as it gets, DELAY samples late.

    Built for one capture geometry and one set of active windows; a window change needs a new
    excisor. The stopband over every cut bin is verified against STOPBAND_DB here (fail closed).
    """
    DELAY = (TAPS - 1) // 2
    BLOCK = 8192

    def __init__(self, center_hz, rate_hz, windows=(), *, bench=False, fft_size=MASK_FFT_SIZE):
        np = _numpy()
        keep = np.array(bin_keep(center_hz, rate_hz, fft_size, windows, bench=bench), bool)
        kept = _kept(np, keep)
        self.kept_bins = int(kept.sum())
        self.taps = _fir(np, kept)
        fine = 4 * keep.size
        response = np.abs(np.fft.fftshift(np.fft.fft(self.taps, fine))) ** 2
        rows = (4 * np.flatnonzero(~keep)[:, None] + np.arange(-2, 3)[None, :]) % fine
        if rows.size and response[rows].max() > 10 ** (STOPBAND_DB / 10):
            raise VoiceMaskError("FILTER_STOPBAND_NOT_MET")
        self._spectrum = np.fft.fft(self.taps, self.BLOCK)
        self._tail = np.zeros(TAPS - 1, np.complex128)

    def push(self, samples):
        np = _numpy()
        values = np.asarray(samples)
        if (values.ndim != 1 or not np.iscomplexobj(values) or values.size > MAX_BLOCK_SAMPLES
                or not np.all(np.isfinite(values))):
            raise VoiceMaskError("FINITE_COMPLEX_IQ_REQUIRED")
        buffer = np.concatenate((self._tail, values.astype(np.complex128)))
        self._tail = buffer[buffer.size - (TAPS - 1):]
        count, hop = values.size, self.BLOCK - TAPS + 1
        out = np.empty(count, np.complex128)
        for start in range(0, count, hop):
            segment = buffer[start:start + self.BLOCK]
            if segment.size < self.BLOCK:
                segment = np.concatenate((segment, np.zeros(self.BLOCK - segment.size, np.complex128)))
            valid = np.fft.ifft(np.fft.fft(segment) * self._spectrum)[TAPS - 1:]
            take = min(hop, count - start)
            out[start:start + take] = valid[:take]
        return out.astype(np.complex64)


def excise(samples, center_hz, rate_hz, windows=(), *, bench=False):
    """Whole-capture excision, delay-compensated: the result is aligned with and as long as samples."""
    np = _numpy()
    excisor = VoiceExcisor(center_hz, rate_hz, windows, bench=bench)
    values = np.asarray(samples)
    if values.ndim != 1 or not np.iscomplexobj(values):
        raise VoiceMaskError("FINITE_COMPLEX_IQ_REQUIRED")
    padded = np.concatenate((values.astype(np.complex128), np.zeros(VoiceExcisor.DELAY, np.complex128)))
    return excisor.push(padded)[VoiceExcisor.DELAY:]
