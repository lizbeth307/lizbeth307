"""v2.1 bounded baseband recorder and live cf32 path: Meteor-M N2-3/N2-4 LRPT only.

Owner decision 24.10.2026 (STACK.md:977, build/12-revision-v2.1.md "Політика baseband/IQ",
build/15-rishennia-komplektu.md decision 6). Implemented here, and only here:

- Input: RTL 1.024 MS/s complex samples at 137.1, 137.9 or 137.9125 MHz. A recording or
  live stream needs one LRPT window: a complete pass of an allowlisted Meteor-M target from
  srrx.passes.baseband_windows (verified UTC only) widened to AOS-60 s .. LOS+60 s and cut
  to 20 min (srrx.satdump_pass builds it; validate_window re-checks every field here).
- Masks before anything is written or sent: srrx.voice_mask.VoiceExcisor (static voice
  masks, voice bands outside windows, spectrum no-data bands) with the window as its only
  active span, then the channel filter: a Kaiser low-pass FIR applied by overlap-save
  (exact linear convolution) whose passband is Rs*1.6/2 + Doppler and whose stopband
  starts at the window edge Rs*1.6/2 + Doppler + 20 kHz (about +-81/+-87 kHz for 72k/80k).
  The response is verified at construction: <= STOPBAND_DB beyond the window, so bins
  outside it reach the ci16 output below 1/2 LSB (rounded to zero) for any input <= 0 dBFS.
  Decimation by 4 gives 256 kS/s.
- File: SigMF v1.2.6 ci16_le (I, Q int16 little-endian, value = round(x * 32767), the inverse
  of SatDump 1aedd60's cs16 reader volk_16i_s32f_convert_32f(..., 32767)), with a strict
  srrx: metadata record. Store: <StorageGuard root>/raw/baseband-lrpt, under the guard's
  mount checks at every step. Class cap 1.5 GiB inside the rolling raw quota of 30 GiB
  over <root>/raw; a start is refused when the planned size x 1.1 does not fit in the
  class, the quota or the free space. The planned size is preallocated and never exceeded.
- Lifetime: a stop, an error, a scope stop, a storage revocation or a lost UTC deletes the
  partial file; a recording is deleted after its decode (srrx.satdump_pass) and never
  later than 24 h after it was made (sweep(), also run before every recording). There is
  no pinning, no export, no copy command and no RPC: this module has no read API other
  than the decoder path (data_path/load).
- Live: LiveUdpSink sends the same masked, quantized 256 kS/s stream as little-endian cf32
  to 127.0.0.1 only (a fixed address, no parameter), <= 8188 complex samples per datagram:
  8192 x 8 B = 65 536 B exceed the IPv4 UDP payload limit of 65 507 B, and SatDump 1aedd60
  net_source reads one datagram into an 8192 x 8 B buffer without reassembly.

Not evidence of RF performance: filter numbers are computed, recordings in CI are synthetic.
"""
from __future__ import annotations

from datetime import datetime, timezone
import errno
import hashlib
import json
import math
import os
import re
import secrets
import socket
import stat
import time

from . import voice_mask

try:
    import numpy as _np
except ImportError:  # the metadata and store helpers stay importable without NumPy
    _np = None

POLICY_ID = "v2.1-meteor-lrpt"
INPUT_RATE_HZ = 1_024_000
DECIMATION = 4
OUTPUT_RATE_HZ = INPUT_RATE_HZ // DECIMATION
CENTERS_HZ = (137_100_000, 137_900_000, 137_912_500)
# SatDump 1aedd60 resources/pipelines/Meteor-M.json: psk_demod symbolrate 72e3 / 80e3.
PIPELINES = {72_000: "meteor_m2-x_lrpt", 80_000: "meteor_m2-x_lrpt_80k"}
# Display names of the reviewed targets (software/config/orbit-targets.json); never NORAD ids.
METEOR_TARGETS = ("Meteor-M N2-3", "Meteor-M N2-4")
BASEBAND_ROLE = "LRPT"
BAND_HZ = (137_000_000.0, 138_000_000.0)
OCCUPIED_SPAN = 1.6  # Rs * 1.6 / 2 each side (STACK.md:977)
GUARD_HZ = voice_mask.WINDOW_MARGIN_HZ
MARGIN_S = voice_mask.WINDOW_MARGIN_S
MAX_FILE_S = 20 * 60
EARLY_START_S = 5.0
BYTES_PER_SAMPLE = 4
CLASS_CAP_BYTES = 3 * 512 * 1024 * 1024  # 1.5 GiB
RAW_QUOTA_BYTES = 30 * 1024 * 1024 * 1024
RESERVE_FACTOR = 1.1
RETENTION_S = 24 * 3600
FUTURE_TOLERANCE_S = 3600.0
CI16_SCALE = 32767
STOPBAND_DB = -100.0
DESIGN_ATTENUATION_DB = 105.0
PASSBAND_RIPPLE_DB = 0.01
FFT_SIZE = 8192
LIVE_HOST = "127.0.0.1"
LIVE_MAX_SAMPLES = 8188
LIVE_PORT_RANGE = (1024, 65535)
SIGMF_VERSION = "1.2.6"
EXTENSION = {"name": "srrx", "version": "1.0.0", "optional": True}
RAW_DIR = "raw"
CLASS_DIR = "raw/baseband-lrpt"
LOCK_NAME = ".lock"
DATA_SUFFIX, META_SUFFIX, PARTIAL_SUFFIX = ".sigmf-data", ".sigmf-meta", ".sigmf-data.partial"
MAX_META_BYTES = 16 * 1024
MAX_RAW_ENTRIES = 10_000
STOP_REASONS = ("WINDOW_END", "RESERVED_SIZE", "BLOCK_LIMIT")
SOURCES = ("HARDWARE", "SIMULATION")
_ID = re.compile(r"lrpt-[0-9a-f]{16}\Z")
_ENTRY = re.compile(r"(lrpt-[0-9a-f]{16})(\.sigmf-data|\.sigmf-meta|\.sigmf-data\.partial|\.sigmf-meta\.tmp)\Z")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\Z")
WINDOW_FIELDS = ("v", "kind", "policy", "norad_id", "target", "pipeline", "center_hz", "symbol_rate", "aos_utc",
                 "los_utc", "start_unix_s", "end_unix_s", "clipped", "half_width_hz")
GLOBAL_CORE = ("core:datatype", "core:sample_rate", "core:version", "core:sha512", "core:recorder",
               "core:num_channels", "core:description", "core:extensions")
GLOBAL_SRRX = ("srrx:kind", "srrx:policy", "srrx:recording_id", "srrx:norad_id", "srrx:target", "srrx:pipeline",
               "srrx:symbol_rate", "srrx:center_hz", "srrx:half_width_hz", "srrx:pass_half_width_hz",
               "srrx:input_rate_hz", "srrx:decimation", "srrx:ci16_scale", "srrx:window_start_utc",
               "srrx:window_end_utc", "srrx:created_utc", "srrx:delete_after_utc", "srrx:samples",
               "srrx:clipped_samples", "srrx:gaps", "srrx:unproven_joins", "srrx:source", "srrx:utc_verified",
               "srrx:masks", "srrx:group_delay_samples", "srrx:stop_reason", "srrx:pinned", "srrx:export")
CAPTURE_FIELDS = ("core:sample_start", "core:frequency", "core:datetime")
MASKS = ("voice_mask.VoiceExcisor", "baseband.ChannelDecimator")


class BasebandRefused(ValueError):
    """Stable refusal code; never embeds sample values, paths or file content."""


class BasebandDependencyError(RuntimeError):
    pass


def _refuse(code):
    raise BasebandRefused(code)


def _numpy():
    if _np is None:
        raise BasebandDependencyError("NumPy is required for the baseband channel filter")
    return _np


def _finite(value, low, high):
    return type(value) in (int, float) and low <= value <= high and math.isfinite(value)


def iso_utc(seconds):
    if not _finite(seconds, 0, 4.2e9):
        _refuse("UTC_TIME_REQUIRED")
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _unix(text):
    if type(text) is not str or not _TIME.match(text):
        _refuse("UTC_TIME_REQUIRED")
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()


# ---------------------------------------------------------------- window and channel geometry

def doppler_hz(center_hz):
    """LEO Doppler bound of srrx.voice_mask (7 km/s): about 3.2 kHz at 137 MHz (STACK.md:977)."""
    return center_hz * voice_mask.DOPPLER_VELOCITY_M_S / voice_mask.LIGHT_M_S


def pass_half_width_hz(center_hz, symbol_rate):
    """Occupied half-band plus Doppler: the channel filter's passband edge."""
    return symbol_rate * OCCUPIED_SPAN / 2 + doppler_hz(center_hz)


def half_width_hz(center_hz, symbol_rate):
    """Window half-width Rs*1.6/2 + Doppler + 20 kHz; the same formula as voice_mask.plan_windows."""
    return pass_half_width_hz(center_hz, symbol_rate) + GUARD_HZ


def _tuning(center_hz, symbol_rate):
    if type(center_hz) is not int or center_hz not in CENTERS_HZ:
        _refuse("LRPT_CENTER_NOT_ALLOWED")
    if type(symbol_rate) is not int or symbol_rate not in PIPELINES:
        _refuse("LRPT_SYMBOL_RATE_NOT_ALLOWED")
    half = half_width_hz(center_hz, symbol_rate)
    low, high = center_hz - half, center_hz + half
    if not (BAND_HZ[0] < low and high < BAND_HZ[1]) or half >= OUTPUT_RATE_HZ / 2:
        _refuse("LRPT_WINDOW_OUTSIDE_137_138_MHZ")
    return half, (low, high)


def channel_span(center_hz, symbol_rate):
    """(low_hz, high_hz) of the recorded window; ScopeLatch and the voice mask use exactly this span."""
    return _tuning(center_hz, symbol_rate)[1]


def window(norad_id, target, center_hz, symbol_rate, aos_unix_s, los_unix_s, aos_utc, los_utc):
    """One recording window: AOS-60 s .. LOS+60 s of a complete pass, cut to MAX_FILE_S."""
    half, unused = _tuning(center_hz, symbol_rate)
    if type(norad_id) is not int or not 1 <= norad_id <= 999999:
        _refuse("WINDOW_SCHEMA")
    if target not in METEOR_TARGETS:
        _refuse("TARGET_NOT_METEOR_LRPT")
    if not _finite(aos_unix_s, 0, 4.2e9) or not _finite(los_unix_s, 0, 4.2e9) or los_unix_s < aos_unix_s:
        _refuse("WINDOW_SCHEMA")
    start = float(aos_unix_s) - MARGIN_S
    end = float(los_unix_s) + MARGIN_S
    clipped = end - start > MAX_FILE_S
    return validate_window({"v": 1, "kind": "srrx_lrpt_window", "policy": POLICY_ID, "norad_id": norad_id,
                            "target": target, "pipeline": PIPELINES[symbol_rate], "center_hz": center_hz,
                            "symbol_rate": symbol_rate, "aos_utc": aos_utc, "los_utc": los_utc,
                            "start_unix_s": start, "end_unix_s": min(end, start + MAX_FILE_S),
                            "clipped": clipped, "half_width_hz": half})


def validate_window(value):
    """Exact-schema check of a window record; every derived field must equal its recomputation."""
    if type(value) is not dict or set(value) != set(WINDOW_FIELDS):
        _refuse("WINDOW_SCHEMA")
    if value["v"] != 1 or type(value["v"]) is not int or value["kind"] != "srrx_lrpt_window" or value["policy"] != POLICY_ID:
        _refuse("WINDOW_SCHEMA")
    half, unused = _tuning(value["center_hz"], value["symbol_rate"])
    if value["target"] not in METEOR_TARGETS:
        _refuse("TARGET_NOT_METEOR_LRPT")
    if type(value["norad_id"]) is not int or not 1 <= value["norad_id"] <= 999999:
        _refuse("WINDOW_SCHEMA")
    aos, los = _unix(value["aos_utc"]), _unix(value["los_utc"])
    start, end = value["start_unix_s"], value["end_unix_s"]
    if (value["pipeline"] != PIPELINES[value["symbol_rate"]] or type(value["clipped"]) is not bool
            or not _finite(start, 0, 4.2e9) or not _finite(end, 0, 4.2e9) or value["half_width_hz"] != half
            or los < aos or abs(start - (aos - MARGIN_S)) > 1e-3
            or abs(end - min(los + MARGIN_S, start + MAX_FILE_S)) > 1e-3
            or value["clipped"] is not (los + MARGIN_S - start > MAX_FILE_S) or not 0 < end - start <= MAX_FILE_S):
        _refuse("WINDOW_SCHEMA")
    return dict(value)


def planned_bytes(window_value):
    seconds = window_value["end_unix_s"] - window_value["start_unix_s"]
    return int(math.ceil(seconds * OUTPUT_RATE_HZ)) * BYTES_PER_SAMPLE


def reserve_bytes(planned):
    return int(math.ceil(planned * RESERVE_FACTOR))


# ---------------------------------------------------------------- channel filter

def design_taps(center_hz, symbol_rate):
    """Kaiser-windowed low-pass (Kaiser 1974 formula): passband pass_half_width, stopband half_width."""
    np = _numpy()
    half, unused = _tuning(center_hz, symbol_rate)
    passband = pass_half_width_hz(center_hz, symbol_rate)
    beta = 0.1102 * (DESIGN_ATTENUATION_DB - 8.7)
    delta = 2 * math.pi * (half - passband) / INPUT_RATE_HZ
    count = math.ceil((DESIGN_ATTENUATION_DB - 7.95) / (2.285 * delta)) + 1
    count += 1 - count % 2  # odd: linear phase, integer group delay
    cutoff = (passband + half) / 2 / INPUT_RATE_HZ
    index = np.arange(count) - (count - 1) / 2
    taps = 2 * cutoff * np.sinc(2 * cutoff * index) * np.kaiser(count, beta)
    return taps / taps.sum()


def verify_taps(taps, center_hz, symbol_rate, grid=1 << 18):
    """(stopband_db, ripple_db); BasebandRefused unless both meet STOPBAND_DB and PASSBAND_RIPPLE_DB."""
    np = _numpy()
    half, unused = _tuning(center_hz, symbol_rate)
    passband = pass_half_width_hz(center_hz, symbol_rate)
    response = np.abs(np.fft.fftshift(np.fft.fft(taps, grid)))
    frequency = (np.arange(grid) - grid // 2) * INPUT_RATE_HZ / grid
    stop = 20 * math.log10(max(float(response[np.abs(frequency) >= half].max()), 1e-300))
    level = 20 * np.log10(response[np.abs(frequency) <= passband])
    ripple = float(max(abs(level.max()), abs(level.min())))
    if stop > STOPBAND_DB or ripple > PASSBAND_RIPPLE_DB:
        _refuse("CHANNEL_FILTER_SPEC_NOT_MET")
    return stop, ripple


class ChannelDecimator:
    """Overlap-save channel filter at 1.024 MS/s, then every 4th sample (256 kS/s).

    push() takes any number of complex samples and returns the decimated output that is
    complete so far; flush() returns the rest (an incomplete group of 4 is dropped).
    Output lags the input by group_delay_samples input samples.
    """

    def __init__(self, center_hz, symbol_rate):
        np = _numpy()
        self.taps = design_taps(center_hz, symbol_rate)
        self.stopband_db, self.ripple_db = verify_taps(self.taps, center_hz, symbol_rate)
        self.history = self.taps.size - 1
        self.hop = (FFT_SIZE - self.history) // DECIMATION * DECIMATION
        if self.hop <= 0:
            _refuse("CHANNEL_FILTER_SPEC_NOT_MET")
        self.group_delay_samples = self.history // 2
        self._spectrum = np.fft.fft(self.taps, FFT_SIZE)
        self._buffer = np.zeros(self.history, np.complex128)

    def _block(self, segment, count):
        np = _numpy()
        padded = np.zeros(FFT_SIZE, np.complex128)
        padded[:segment.size] = segment
        filtered = np.fft.ifft(np.fft.fft(padded) * self._spectrum)[self.history:self.history + count]
        return filtered[::DECIMATION]

    def push(self, samples):
        np = _numpy()
        values = np.asarray(samples)
        if values.ndim != 1 or not np.iscomplexobj(values) or not np.all(np.isfinite(values)):
            _refuse("FINITE_COMPLEX_IQ_REQUIRED")
        self._buffer = np.concatenate((self._buffer, values.astype(np.complex128)))
        out = []
        while self._buffer.size - self.history >= self.hop:
            out.append(self._block(self._buffer[:self.history + self.hop], self.hop))
            self._buffer = self._buffer[self.hop:]
        return np.concatenate(out) if out else np.zeros(0, np.complex128)

    def flush(self):
        np = _numpy()
        count = (self._buffer.size - self.history) // DECIMATION * DECIMATION
        out = self._block(self._buffer[:self.history + count], count) if count > 0 else np.zeros(0, np.complex128)
        self._buffer = np.zeros(self.history, np.complex128)
        return out


def quantize_ci16(values):
    """(interleaved little-endian int16 array, clipped sample count): round(x * 32767), clipped to +-32767."""
    np = _numpy()
    scaled = np.asarray(values, np.complex128) * CI16_SCALE
    parts = np.empty(scaled.size * 2, np.float64)
    parts[0::2], parts[1::2] = np.rint(scaled.real), np.rint(scaled.imag)
    over = np.abs(parts) > CI16_SCALE
    clipped = int(np.count_nonzero(over[0::2] | over[1::2]))
    return np.clip(parts, -CI16_SCALE, CI16_SCALE).astype("<i2"), clipped


def ci16_to_cf32(interleaved):
    """The live stream: exactly the stored values as SatDump's cs16 reader sees them, little-endian cf32."""
    np = _numpy()
    return (np.asarray(interleaved, "<i2").astype("<f4") / np.float32(CI16_SCALE)).view("<c8")


class ChannelChain:
    """voice_mask.VoiceExcisor (window as the only active span) -> ChannelDecimator -> ci16.

    The first warmup_samples outputs (both filters' impulse responses, about 1.3 ms) are
    dropped: they hold the switch-on transient of the stream start, not a filtered signal.
    """

    def __init__(self, window_value):
        checked = validate_window(window_value)
        low, high = channel_span(checked["center_hz"], checked["symbol_rate"])
        self.excisor = voice_mask.VoiceExcisor(float(checked["center_hz"]), float(INPUT_RATE_HZ), [(low, high)])
        self.channel = ChannelDecimator(checked["center_hz"], checked["symbol_rate"])
        self.group_delay_samples = voice_mask.VoiceExcisor.DELAY + self.channel.group_delay_samples
        self.warmup_samples = -(-(voice_mask.TAPS + self.channel.taps.size) // DECIMATION)
        self._skip = self.warmup_samples
        self.clipped = 0

    def _out(self, values):
        if self._skip:
            dropped = min(self._skip, values.size)
            values, self._skip = values[dropped:], self._skip - dropped
        interleaved, clipped = quantize_ci16(values)
        self.clipped += clipped
        return interleaved

    def push(self, samples):
        return self._out(self.channel.push(self.excisor.push(samples)))

    def flush(self):
        return self._out(self.channel.flush())


# ---------------------------------------------------------------- live path

class LiveUdpSink:
    """cf32 datagrams to 127.0.0.1:port only, <= LIVE_MAX_SAMPLES samples each; never blocks the recorder."""

    def __init__(self, port, *, socket_factory=socket.socket):
        if type(port) is not int or not LIVE_PORT_RANGE[0] <= port <= LIVE_PORT_RANGE[1]:
            _refuse("LIVE_PORT_RANGE")
        self.port = port
        self.sent_datagrams = self.sent_samples = self.dropped_datagrams = 0
        self._socket = socket_factory(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self._socket.setblocking(False)
            self._socket.connect((LIVE_HOST, port))  # a fixed loopback peer: no address parameter exists
        except BaseException:
            self._socket.close()
            raise

    def send(self, cf32):
        data = memoryview(bytes(cf32) if not isinstance(cf32, (bytes, bytearray, memoryview)) else cf32).cast("B")
        if len(data) % 8:
            _refuse("CF32_ALIGNMENT")
        step = LIVE_MAX_SAMPLES * 8
        for offset in range(0, len(data), step):
            chunk = data[offset:offset + step]
            try:
                sent = self._socket.send(chunk)
            except OSError:  # EAGAIN, ECONNREFUSED (no listener), ENOBUFS: drop, never stall
                self.dropped_datagrams += 1
                continue
            if sent != len(chunk):
                self.dropped_datagrams += 1
                continue
            self.sent_datagrams += 1
            self.sent_samples += len(chunk) // 8

    def status(self):
        return {"host": LIVE_HOST, "port": self.port, "max_samples_per_datagram": LIVE_MAX_SAMPLES,
                "sent_datagrams": self.sent_datagrams, "sent_samples": self.sent_samples,
                "dropped_datagrams": self.dropped_datagrams}

    def close(self):
        self._socket.close()


# ---------------------------------------------------------------- metadata

def metadata(recording_id, window_value, *, created_s, first_block_s, samples, sha512, clipped, gaps, joins,
             source, group_delay, stop_reason):
    checked = validate_window(window_value)
    created = iso_utc(created_s)
    value = {
        "global": {
            "core:datatype": "ci16_le", "core:sample_rate": OUTPUT_RATE_HZ, "core:version": SIGMF_VERSION,
            "core:sha512": sha512, "core:recorder": "srrx.baseband", "core:num_channels": 1,
            "core:description": "Meteor-M LRPT narrow baseband (v2.1 policy); deleted after decode or 24 h; never exported",
            "core:extensions": [dict(EXTENSION)],
            "srrx:kind": "srrx_lrpt_baseband", "srrx:policy": POLICY_ID, "srrx:recording_id": recording_id,
            "srrx:norad_id": checked["norad_id"], "srrx:target": checked["target"], "srrx:pipeline": checked["pipeline"],
            "srrx:symbol_rate": checked["symbol_rate"], "srrx:center_hz": checked["center_hz"],
            "srrx:half_width_hz": checked["half_width_hz"],
            "srrx:pass_half_width_hz": pass_half_width_hz(checked["center_hz"], checked["symbol_rate"]),
            "srrx:input_rate_hz": INPUT_RATE_HZ, "srrx:decimation": DECIMATION, "srrx:ci16_scale": CI16_SCALE,
            "srrx:window_start_utc": iso_utc(checked["start_unix_s"]), "srrx:window_end_utc": iso_utc(checked["end_unix_s"]),
            "srrx:created_utc": created, "srrx:delete_after_utc": iso_utc(_unix(created) + RETENTION_S),
            "srrx:samples": samples, "srrx:clipped_samples": clipped, "srrx:gaps": gaps, "srrx:unproven_joins": joins,
            "srrx:source": source, "srrx:utc_verified": True, "srrx:masks": list(MASKS),
            "srrx:group_delay_samples": group_delay, "srrx:stop_reason": stop_reason, "srrx:pinned": False,
            "srrx:export": False},
        "captures": [{"core:sample_start": 0, "core:frequency": checked["center_hz"],
                      "core:datetime": iso_utc(first_block_s)}],
        "annotations": []}
    return validate_metadata(value)


def validate_metadata(value):
    """Exact SigMF + srrx schema of one recording; anything else is not a recording of this store."""
    if type(value) is not dict or set(value) != {"global", "captures", "annotations"}:
        _refuse("RECORDING_METADATA_SCHEMA")
    meta, captures = value["global"], value["captures"]
    if type(meta) is not dict or set(meta) != set(GLOBAL_CORE) | set(GLOBAL_SRRX) or value["annotations"] != []:
        _refuse("RECORDING_METADATA_SCHEMA")
    if (meta["core:datatype"] != "ci16_le" or meta["core:sample_rate"] != OUTPUT_RATE_HZ
            or meta["core:version"] != SIGMF_VERSION or meta["core:recorder"] != "srrx.baseband"
            or meta["core:num_channels"] != 1 or meta["core:extensions"] != [EXTENSION]
            or type(meta["core:sha512"]) is not str or not re.fullmatch(r"[0-9a-f]{128}", meta["core:sha512"])
            or meta["srrx:kind"] != "srrx_lrpt_baseband" or meta["srrx:policy"] != POLICY_ID
            or type(meta["srrx:recording_id"]) is not str or not _ID.match(meta["srrx:recording_id"])
            or meta["srrx:target"] not in METEOR_TARGETS or meta["srrx:source"] not in SOURCES
            or meta["srrx:utc_verified"] is not True or meta["srrx:pinned"] is not False
            or meta["srrx:export"] is not False or meta["srrx:masks"] != list(MASKS)
            or meta["srrx:stop_reason"] not in STOP_REASONS or meta["srrx:input_rate_hz"] != INPUT_RATE_HZ
            or meta["srrx:decimation"] != DECIMATION or meta["srrx:ci16_scale"] != CI16_SCALE):
        _refuse("RECORDING_METADATA_SCHEMA")
    half, unused = _tuning(meta["srrx:center_hz"], meta["srrx:symbol_rate"])
    if (meta["srrx:pipeline"] != PIPELINES[meta["srrx:symbol_rate"]] or meta["srrx:half_width_hz"] != half
            or meta["srrx:pass_half_width_hz"] != pass_half_width_hz(meta["srrx:center_hz"], meta["srrx:symbol_rate"])
            or type(meta["srrx:norad_id"]) is not int or not 1 <= meta["srrx:norad_id"] <= 999999):
        _refuse("RECORDING_METADATA_SCHEMA")
    for key in ("srrx:samples", "srrx:clipped_samples", "srrx:gaps", "srrx:unproven_joins", "srrx:group_delay_samples"):
        if type(meta[key]) is not int or meta[key] < 0:
            _refuse("RECORDING_METADATA_SCHEMA")
    start, end = _unix(meta["srrx:window_start_utc"]), _unix(meta["srrx:window_end_utc"])
    created = _unix(meta["srrx:created_utc"])
    if (not 0 < end - start <= MAX_FILE_S + 1e-3 or abs(_unix(meta["srrx:delete_after_utc"]) - created - RETENTION_S) > 1e-3
            or meta["srrx:samples"] * BYTES_PER_SAMPLE > reserve_bytes(int(math.ceil((end - start) * OUTPUT_RATE_HZ))
                                                                       * BYTES_PER_SAMPLE)):
        _refuse("RECORDING_METADATA_SCHEMA")
    if (type(captures) is not list or len(captures) != 1 or type(captures[0]) is not dict
            or set(captures[0]) != set(CAPTURE_FIELDS) or captures[0]["core:sample_start"] != 0
            or captures[0]["core:frequency"] != meta["srrx:center_hz"]):
        _refuse("RECORDING_METADATA_SCHEMA")
    _unix(captures[0]["core:datetime"])
    return value


# ---------------------------------------------------------------- store

def _flags(*names):
    value = 0
    for name in names:
        value |= getattr(os, name, 0)
    return value


_DIR_FLAGS = os.O_RDONLY | _flags("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
_NEW_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _flags("O_NOFOLLOW", "O_CLOEXEC")
_READ_FLAGS = os.O_RDONLY | _flags("O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK")


def _write_all(descriptor, data):
    view = memoryview(data).cast("B")
    while view:
        count = os.write(descriptor, view[:1 << 20])
        if count <= 0:
            raise OSError(errno.EIO, "Baseband write made no progress")
        view = view[count:]


def _size(info):
    return max(info.st_size, getattr(info, "st_blocks", 0) * 512)


_preallocate = getattr(os, "posix_fallocate", None)  # module-level: tests replace it


class Recording:
    """One partial recording owned by the store's lock; finish() publishes it, abort() deletes it."""

    def __init__(self, store, directory, recording_id, window_value, reserved):
        self.store, self.directory, self.id, self.window = store, directory, recording_id, window_value
        self.reserved, self.written, self.done = reserved, 0, False
        self._digest = hashlib.sha512()
        self.preallocated = False
        self.fd = os.open(recording_id + PARTIAL_SUFFIX, _NEW_FLAGS, 0o640, dir_fd=directory)
        try:
            if _preallocate is not None:
                try:
                    _preallocate(self.fd, 0, reserved)
                    self.preallocated = True
                except OSError as error:
                    if error.errno in (errno.ENOSPC, getattr(errno, "EDQUOT", errno.ENOSPC)):
                        raise BasebandRefused("STORAGE_FULL") from None
                    if error.errno not in (errno.EOPNOTSUPP, errno.EINVAL, getattr(errno, "ENOTSUP", errno.EOPNOTSUPP)):
                        raise  # no preallocation on this filesystem: the size cap below still holds
        except BaseException:
            self.abort()
            raise

    @property
    def full(self):
        return self.written + BYTES_PER_SAMPLE > self.reserved

    def write(self, interleaved):
        """Append ci16 bytes up to the reserved size; returns the samples written (the rest is cut)."""
        data = memoryview(interleaved).cast("B")
        room = (self.reserved - self.written) // BYTES_PER_SAMPLE * BYTES_PER_SAMPLE
        data = data[:min(len(data) // BYTES_PER_SAMPLE * BYTES_PER_SAMPLE, room)]
        if data:
            _write_all(self.fd, data)
            self._digest.update(data)
            self.written += len(data)
        return len(data) // BYTES_PER_SAMPLE

    def finish(self, **fields):
        """Truncate to the data written, fsync, publish data then metadata; returns the metadata."""
        if self.done:
            _refuse("RECORDING_CLOSED")
        try:
            os.ftruncate(self.fd, self.written)
            os.fsync(self.fd)
            value = metadata(self.id, self.window, samples=self.written // BYTES_PER_SAMPLE,
                             sha512=self._digest.hexdigest(), **fields)
            encoded = (json.dumps(value, indent=1, sort_keys=True, allow_nan=False) + "\n").encode("ascii")
            temporary = self.id + ".sigmf-meta.tmp"
            meta = os.open(temporary, _NEW_FLAGS, 0o640, dir_fd=self.directory)
            try:
                _write_all(meta, encoded)
                os.fsync(meta)
            finally:
                os.close(meta)
            for name in (self.id + DATA_SUFFIX, self.id + META_SUFFIX):
                try:
                    os.stat(name, dir_fd=self.directory, follow_symlinks=False)
                    _refuse("RECORDING_NAME_EXISTS")
                except FileNotFoundError:
                    pass
            os.rename(self.id + PARTIAL_SUFFIX, self.id + DATA_SUFFIX, src_dir_fd=self.directory,
                      dst_dir_fd=self.directory)
            os.rename(temporary, self.id + META_SUFFIX, src_dir_fd=self.directory, dst_dir_fd=self.directory)
            os.fsync(self.directory)
            self.done = True
            return value
        except BaseException:
            self.abort()
            raise
        finally:
            self._close()

    def _close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def abort(self):
        """Delete every file of this recording (partial, temporary metadata, published names); idempotent."""
        self._close()
        if self.done:
            return
        self.done = True
        for suffix in (PARTIAL_SUFFIX, ".sigmf-meta.tmp", DATA_SUFFIX, META_SUFFIX):
            try:
                os.unlink(self.id + suffix, dir_fd=self.directory)
            except FileNotFoundError:
                pass
            except OSError:
                pass  # e.g. the mount is gone; sweep() deletes it later
        try:
            os.fsync(self.directory)
        except OSError:
            pass


class BasebandStore:
    """<guard root>/raw/baseband-lrpt under a StorageGuard (check() + open_directory())."""

    def __init__(self, guard, *, clock=time.time):
        if guard is None or not callable(getattr(guard, "check", None)) or not callable(getattr(guard, "open_directory", None)):
            _refuse("STORAGE_GUARD_REQUIRED")
        self.guard, self.clock = guard, clock
        self._lock = None
        self._directory = None

    # -- locking: one recorder or sweep at a time per class directory
    def _acquire(self):
        import fcntl  # Linux only, as StorageGuard
        self.guard.check()
        directory = self.guard.open_directory(CLASS_DIR)
        try:
            lock = os.open(LOCK_NAME, os.O_RDWR | os.O_CREAT | _flags("O_NOFOLLOW", "O_CLOEXEC"), 0o600, dir_fd=directory)
        except BaseException:
            os.close(directory)
            raise
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(lock)
            os.close(directory)
            _refuse("RECORDER_BUSY")
        except BaseException:
            os.close(lock)
            os.close(directory)
            raise
        self._lock, self._directory = lock, directory
        return directory

    def _release(self):
        for name in ("_lock", "_directory"):
            descriptor = getattr(self, name)
            if descriptor is not None:
                os.close(descriptor)
                setattr(self, name, None)

    def usage(self):
        """Allocated bytes of the class directory and of the whole raw tree (two levels, bounded)."""
        self.guard.check()
        raw = self.guard.open_directory(RAW_DIR)
        total = mine = entries = 0
        try:
            stack = [(raw, False, 0)]
            opened = []
            try:
                while stack:
                    descriptor, in_class, depth = stack.pop()
                    with os.scandir(descriptor) as listing:
                        for entry in listing:
                            entries += 1
                            if entries > MAX_RAW_ENTRIES:
                                _refuse("RAW_INVENTORY_LIMIT")
                            info = entry.stat(follow_symlinks=False)
                            if stat.S_ISREG(info.st_mode):
                                total += _size(info)
                                mine += _size(info) if in_class else 0
                            elif stat.S_ISDIR(info.st_mode):
                                if depth >= 2:
                                    _refuse("RAW_INVENTORY_DEPTH")
                                child = os.open(entry.name, _DIR_FLAGS, dir_fd=descriptor)
                                opened.append(child)
                                stack.append((child, in_class or (depth == 0 and entry.name == CLASS_DIR.split("/")[1]),
                                              depth + 1))
            finally:
                for descriptor in opened:
                    os.close(descriptor)
        finally:
            os.close(raw)
        return {"class_bytes": mine, "raw_bytes": total, "class_cap_bytes": CLASS_CAP_BYTES,
                "raw_quota_bytes": RAW_QUOTA_BYTES}

    def _check_room(self, directory, reserve):
        use = self.usage()
        if use["class_bytes"] + reserve > CLASS_CAP_BYTES:
            _refuse("CLASS_CAP_1_5_GIB")
        if use["raw_bytes"] + reserve > RAW_QUOTA_BYTES:
            _refuse("RAW_QUOTA_30_GIB")
        info = os.fstatvfs(directory)
        if info.f_bavail * info.f_frsize < reserve:
            _refuse("STORAGE_FREE_SPACE")
        return use

    def begin(self, window_value):
        """Sweep, check the room for planned x 1.1, preallocate and return the Recording (lock held)."""
        checked = validate_window(window_value)
        directory = self._acquire()
        try:
            self._sweep_locked(directory, self.clock())
            reserved = reserve_bytes(planned_bytes(checked))
            self._check_room(directory, reserved)
            self.guard.check()
            return Recording(self, directory, "lrpt-" + secrets.token_hex(8), checked, planned_bytes(checked))
        except BaseException:
            self._release()
            raise

    def end(self):
        self._release()

    def _remove(self, directory, recording_id):
        removed = 0
        for suffix in (META_SUFFIX, DATA_SUFFIX, PARTIAL_SUFFIX, ".sigmf-meta.tmp"):
            try:
                os.unlink(recording_id + suffix, dir_fd=directory)
                removed += 1
            except FileNotFoundError:
                pass
        os.fsync(directory)
        return removed

    def delete(self, recording_id):
        """Delete one recording (after its decode). Waits for no lock: a sweep may already have removed it."""
        if type(recording_id) is not str or not _ID.match(recording_id):
            _refuse("RECORDING_ID")
        self.guard.check()
        directory = self.guard.open_directory(CLASS_DIR)
        try:
            return self._remove(directory, recording_id) > 0
        finally:
            os.close(directory)

    def _read_meta(self, directory, recording_id):
        descriptor = os.open(recording_id + META_SUFFIX, _READ_FLAGS, dir_fd=directory)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_META_BYTES:
                _refuse("RECORDING_METADATA_SCHEMA")
            data = os.read(descriptor, MAX_META_BYTES + 1)
        finally:
            os.close(descriptor)

        def unique(pairs):
            keys = [key for key, unused in pairs]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate key")
            return dict(pairs)
        try:
            value = json.loads(data.decode("ascii"), object_pairs_hook=unique,
                               parse_constant=lambda unused: (_ for _ in ()).throw(ValueError("constant")))
        except (UnicodeError, ValueError):
            _refuse("RECORDING_METADATA_SCHEMA")
        value = validate_metadata(value)
        if value["global"]["srrx:recording_id"] != recording_id:
            _refuse("RECORDING_METADATA_SCHEMA")
        return value

    def _keep(self, directory, recording_id, now):
        try:
            value = self._read_meta(directory, recording_id)
            data = os.stat(recording_id + DATA_SUFFIX, dir_fd=directory, follow_symlinks=False)
        except (BasebandRefused, OSError):
            return False
        created = _unix(value["global"]["srrx:created_utc"])
        if (not stat.S_ISREG(data.st_mode) or data.st_size != value["global"]["srrx:samples"] * BYTES_PER_SAMPLE
                or not _finite(now, 0, 4.2e9) or now - created >= RETENTION_S or created - now > FUTURE_TOLERANCE_S
                or now - data.st_mtime >= RETENTION_S or data.st_mtime - now > FUTURE_TOLERANCE_S):
            return False
        return True

    def _sweep_locked(self, directory, now):
        groups, foreign = {}, 0
        with os.scandir(directory) as listing:
            names = [entry.name for entry in listing]
        for name in names:
            if name == LOCK_NAME:
                continue
            match = _ENTRY.match(name)
            if match is None:
                try:
                    os.unlink(name, dir_fd=directory)  # a file, link or FIFO nobody may keep here
                except IsADirectoryError:
                    foreign += 1
                except PermissionError:
                    foreign += 1  # a directory on Linux gives EISDIR/EPERM: never recursed into
                continue
            groups.setdefault(match.group(1), set()).add(match.group(2))
        deleted = kept = 0
        for recording_id, kinds in sorted(groups.items()):
            if kinds == {DATA_SUFFIX, META_SUFFIX} and self._keep(directory, recording_id, now):
                kept += 1
                continue
            self._remove(directory, recording_id)
            deleted += 1
        os.fsync(directory)
        return {"deleted": deleted, "kept": kept, "foreign_directories": foreign}

    def sweep(self, now=None):
        """Delete what may not stay: incomplete, invalid, >= 24 h old or future-dated recordings."""
        try:
            directory = self._acquire()
        except BasebandRefused as error:
            if str(error) == "RECORDER_BUSY":
                return {"deleted": 0, "kept": None, "skipped": "RECORDER_BUSY"}
            raise
        try:
            return dict(self._sweep_locked(directory, self.clock() if now is None else now), skipped=None)
        finally:
            self._release()

    def load(self, recording_id):
        """Metadata of one complete recording for its decode; checks the data size and SHA512."""
        if type(recording_id) is not str or not _ID.match(recording_id):
            _refuse("RECORDING_ID")
        self.guard.check()
        directory = self.guard.open_directory(CLASS_DIR)
        try:
            value = self._read_meta(directory, recording_id)
            descriptor = os.open(recording_id + DATA_SUFFIX, _READ_FLAGS, dir_fd=directory)
            try:
                info = os.fstat(descriptor)
                expected = value["global"]["srrx:samples"] * BYTES_PER_SAMPLE
                if not stat.S_ISREG(info.st_mode) or info.st_size != expected:
                    _refuse("RECORDING_DATA_SIZE")
                digest, count = hashlib.sha512(), 0
                for block in iter(lambda: os.read(descriptor, 1 << 20), b""):
                    count += len(block)
                    if count > expected:
                        _refuse("RECORDING_DATA_SIZE")
                    digest.update(block)
                if count != expected or digest.hexdigest() != value["global"]["core:sha512"]:
                    _refuse("RECORDING_DATA_DIGEST")
                identity = (info.st_dev, info.st_ino, info.st_size)
            finally:
                os.close(descriptor)
        finally:
            os.close(directory)
        return value, identity

    def data_path(self, recording_id):
        """Path the decoder unit reads; srrx.satdump_pass binds it read-only into the unit."""
        if type(recording_id) is not str or not _ID.match(recording_id):
            _refuse("RECORDING_ID")
        return str(self.guard.root) + "/" + CLASS_DIR + "/" + recording_id + DATA_SUFFIX

    def identity(self, recording_id):
        info = os.stat(self.data_path(recording_id), follow_symlinks=False)
        return info.st_dev, info.st_ino, info.st_size


def tmpfiles(root="/data", owner="labd", group="srrx-bb"):
    """tmpfiles.d text for the class directory: setgid group srrx-bb (the decode unit reads), no world access.

    The age 24h is a second layer only (systemd-tmpfiles-clean runs daily); sweep() is the rule.
    """
    return ("# SR-RX v2.1 LRPT baseband (srrx.baseband.tmpfiles); recordings 0640, deleted after decode or 24 h.\n"
            "d " + root + "/" + RAW_DIR + " 0750 " + owner + " " + group + " -\n"
            "d " + root + "/" + CLASS_DIR + " 2750 " + owner + " " + group + " 24h\n")


def _guard(args):
    from .storage import StorageGuard
    return StorageGuard(args.storage_root, args.storage_device)


def main(argv=None):
    import argparse
    import sys
    parser = argparse.ArgumentParser(prog="python3 -m srrx.baseband",
                                     description="LRPT baseband store maintenance (no export, no copy)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("sweep", "usage"):
        command = commands.add_parser(name)
        command.add_argument("--storage-root", required=True)
        command.add_argument("--storage-device", required=True)
    args = parser.parse_args(argv)
    guard = None
    try:
        guard = _guard(args)
        store = BasebandStore(guard)
        result = store.sweep() if args.command == "sweep" else store.usage()
    except (BasebandRefused, OSError, ValueError) as error:
        print("srrx.baseband: refused: " + (str(error) if isinstance(error, BasebandRefused) else type(error).__name__),
              file=sys.stderr)
        return 2
    finally:
        if guard is not None:
            guard.close()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
