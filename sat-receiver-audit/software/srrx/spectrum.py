"""Bounded RAM-only IQ processing and mandatory no-data spectrum boundaries.

All public spectrum/export consumers must use mask_frame before use. No raw-IQ
persistence, emitter tracking, GNSS-position logging or content decoding exists.
"""
from collections import deque
import json
import math
from pathlib import Path

try:
    import numpy as _np
except ImportError:  # Metadata sanitization remains usable without NumPy.
    _np = None

MAX_RING_BYTES = 4 * 1024**3
DEFAULT_RING_BYTES = 8 * 1024**2
MAX_FFT_SIZE = 1024**2
MAX_RING_CHUNKS = 8192
MASKED_BANDS_HZ = ((3_000.0, 30_000.0), (225_000_000.0, 400_000_000.0),
                   (1_530_000_000.0, 1_660_000_000.0))
FRAME_FIELDS = frozenset(('v', 'kind', 'center_hz', 'sample_rate_hz', 'fft_size',
                         'power_dbfs', 'valid', 'relative_frequency_hz', 'source', 'sample_count'))


class SpectrumError(ValueError):
    pass


class SpectrumDependencyError(RuntimeError):
    pass


def _numpy():
    if _np is None:
        raise SpectrumDependencyError('NumPy is required for FFT/IQ buffers; install the optional numpy dependency')
    return _np


def _integer(value, minimum, maximum, label):
    if type(value) is not int or not minimum <= value <= maximum:
        raise SpectrumError(label + ' must be an in-range integer, not boolean')
    return value


def _finite(value, label):
    if type(value) not in (int, float):
        raise SpectrumError(label + ' must be a finite number, not boolean')
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise SpectrumError(label + ' must be finite') from exc
    if not math.isfinite(number):
        raise SpectrumError(label + ' must be finite')
    return number


def _fft_size(value):
    value = _integer(value, 16, MAX_FFT_SIZE, 'fft_size')
    if value & (value - 1):
        raise SpectrumError('fft_size must be a power of two')
    return value


def _geometry(center_hz, sample_rate_hz, fft_size):
    center = _finite(center_hz, 'center_hz')
    rate = _finite(sample_rate_hz, 'sample_rate_hz')
    size = _fft_size(fft_size)
    width = rate / size
    if center < 0 or rate <= 0 or width == 0:
        raise SpectrumError('center must be nonnegative and sample rate/bin width positive')
    if not all(math.isfinite(x) for x in (center - rate, center + rate)):
        raise SpectrumError('frequency geometry overflows finite values')
    return center, rate, size, width


def _touches_mask(center, relative, width):
    frequency = center + relative
    low, high = frequency - width / 2, frequency + width / 2
    return any(low <= upper and high >= lower for lower, upper in MASKED_BANDS_HZ)


def _checked_frame(frame, enforce_masks):
    if type(frame) is not dict or set(frame) != FRAME_FIELDS:
        raise SpectrumError('spectrum frame has missing or extra fields')
    if type(frame['v']) is not int or frame['v'] != 1 or frame['kind'] != 'spectrum':
        raise SpectrumError('unsupported spectrum version/kind')
    if type(frame['source']) is not str or frame['source'] not in ('SIMULATION', 'HARDWARE'):
        raise SpectrumError('source must explicitly identify SIMULATION or HARDWARE')
    center, rate, size, width = _geometry(frame['center_hz'], frame['sample_rate_hz'], frame['fft_size'])
    count = _integer(frame['sample_count'], 0, size, 'sample_count')
    for name in ('power_dbfs', 'valid', 'relative_frequency_hz'):
        if type(frame[name]) is not list or len(frame[name]) != size:
            raise SpectrumError(name + ' must be an fft_size-length JSON array')
    frequencies, powers, valid = [], [], []
    for index, (relative, power, flag) in enumerate(zip(frame['relative_frequency_hz'], frame['power_dbfs'], frame['valid'])):
        expected = (index - size // 2) * width
        if _finite(relative, 'relative frequency') != expected:
            raise SpectrumError('relative frequency array does not match the sorted fftshift grid')
        if type(flag) is not bool:
            raise SpectrumError('valid entries must be boolean')
        number = None if power is None else _finite(power, 'power_dbfs')
        # The even-FFT Nyquist bin also spans the upper wrapped half-bin.
        wrapped_mask = index == 0 and any(
            center + rate / 2 >= lower and center + rate / 2 - width / 2 <= upper
            for lower, upper in MASKED_BANDS_HZ)
        permitted = flag and number is not None and count == size and not (
            _touches_mask(center, expected, width) or wrapped_mask)
        canonical_power = number if permitted else None
        if enforce_masks and (flag != permitted or power != canonical_power):
            raise SpectrumError('frame violates mandatory no-data masks or invalid-bin null representation')
        frequencies.append(expected)
        powers.append(canonical_power)
        valid.append(permitted)
    return {'v': 1, 'kind': 'spectrum', 'center_hz': center, 'sample_rate_hz': rate,
            'fft_size': size, 'power_dbfs': powers, 'valid': valid,
            'relative_frequency_hz': frequencies, 'source': frame['source'], 'sample_count': count}


def mask_frame(frame):
    """Return a new sanitized frame; never trust caller-valid flags or mutate input.

    Structural geometry/types must be valid. Every prohibited/touching bin,
    caller-invalid bin or incomplete FFT becomes valid=False,power_dbfs=None.
    A caller-invalid bin is never re-enabled. Use BEFORE annotation/training/UI.
    """
    return _checked_frame(frame, False)


def validate_frame(frame):
    """Return a canonical copy, or raise SpectrumError for any schema/mask defect."""
    return _checked_frame(frame, True)


def append_survey(path, frame, *, storage_guard=None):
    """Append only a re-masked spectrum JSON line, never raw IQ or extra fields."""
    safe = validate_frame(mask_frame(frame))
    if storage_guard is not None:
        storage_guard.append_jsonl(path, safe)
        return safe
    line = json.dumps(safe, allow_nan=False, separators=(',', ':')) + '\n'
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('a', encoding='utf-8') as stream:
        stream.write(line)
    return safe


class SampleRing:
    """Lazy bounded deque of owned complex64 chunks; never creates a file.

    capacity_bytes bounds retained IQ payload. One conversion chunk and FFT
    scratch arrays are additional bounded working memory. No mmap/memmap/swap
    file is created. OS swap/core-dump policy belongs to deployment. Single writer.
    """
    def __init__(self, capacity_bytes=DEFAULT_RING_BYTES, chunk_samples=65536):
        _numpy()
        _integer(capacity_bytes, 8, MAX_RING_BYTES, 'capacity_bytes')
        _integer(chunk_samples, 1, MAX_FFT_SIZE, 'chunk_samples')
        if capacity_bytes % 8:
            raise SpectrumError('capacity_bytes must be a multiple of complex64 sample size8')
        self._capacity_bytes = capacity_bytes
        self._capacity_samples = capacity_bytes // 8
        self._chunk_samples = min(chunk_samples, self._capacity_samples)
        self._chunks, self._count = deque(), 0

    @property
    def capacity_bytes(self):
        return self._capacity_bytes

    @property
    def allocated_bytes(self):
        return sum(chunk.nbytes for chunk in self._chunks)

    @property
    def chunk_count(self):
        return len(self._chunks)

    def __len__(self):
        return self._count

    def clear(self):
        for chunk in self._chunks:
            chunk.fill(0)
        self._chunks.clear()
        self._count = 0

    def append(self, samples):
        np = _numpy()
        try:
            if isinstance(samples, np.ndarray):
                if samples.ndim != 1 or samples.dtype.kind not in 'iufc':
                    raise SpectrumError('samples must be a one-dimensional real/complex numeric array')
            elif type(samples) not in (list, tuple):
                raise SpectrumError('samples must be a bounded-indexable array/list/tuple, not a stream/object')
            for offset in range(0, len(samples), self._chunk_samples):
                source = np.asarray(samples[offset:offset + self._chunk_samples])
                if source.ndim != 1 or source.dtype.kind not in 'iufc':
                    raise SpectrumError('samples must be one-dimensional numeric values')
                with np.errstate(over='ignore', invalid='ignore'):
                    chunk = np.array(source, dtype=np.complex64, copy=True)
                if not bool(np.isfinite(chunk).all()):
                    chunk.fill(0)
                    raise SpectrumError('samples contain nonfinite or complex64-overflow values')
                # Bound Python/ndarray metadata too, even for endless1-sample appends.
                while len(self._chunks) >= MAX_RING_CHUNKS:
                    removed_chunk = self._chunks.popleft()
                    self._count -= len(removed_chunk)
                    removed_chunk.fill(0)
                excess = self._count + len(chunk) - self._capacity_samples
                while excess > 0:
                    first = self._chunks.popleft()
                    removed = min(excess, len(first))
                    if removed < len(first):
                        self._chunks.appendleft(first[removed:].copy())  # no oversized backing array retained
                    first.fill(0)
                    self._count -= removed
                    excess -= removed
                self._chunks.append(chunk)
                self._count += len(chunk)
            return len(samples)
        except (SpectrumError, TypeError, ValueError, OverflowError) as exc:
            self.clear()  # Failed samples never leave a partly accepted history.
            if isinstance(exc, SpectrumError):
                raise
            raise SpectrumError('invalid samples: ' + str(exc)) from exc

    def tail(self, count):
        np = _numpy()
        _integer(count, 0, self._count, 'tail sample count')
        result = np.empty(count, dtype=np.complex64)
        remaining = count
        for chunk in reversed(self._chunks):
            copied = min(remaining, len(chunk))
            if copied:
                result[remaining - copied:remaining] = chunk[-copied:]
                remaining -= copied
            if not remaining:
                break
        return result


class SpectrumProcessor:
    """Periodic-Hann FFT; coherent complex tone amplitude1 corresponds to0dBFS."""
    def __init__(self, fft_size=1024, *, capacity_bytes=DEFAULT_RING_BYTES, chunk_samples=65536):
        np = _numpy()
        self._fft_size = _fft_size(fft_size)
        self.ring = SampleRing(capacity_bytes, chunk_samples)
        if capacity_bytes < self._fft_size * 8:
            raise SpectrumError('ring capacity must hold at least one FFT of complex64 IQ')
        self._window = np.hanning(self._fft_size + 1)[:-1]
        self._coherent_gain = float(self._window.sum())
        self._context = None

    @property
    def fft_size(self):
        return self._fft_size

    def clear(self):
        self.ring.clear()
        self._context = None

    def process(self, samples, center_hz, sample_rate_hz, source='SIMULATION'):
        np = _numpy()
        center, rate, size, width = _geometry(center_hz, sample_rate_hz, self._fft_size)
        if type(source) is not str or source not in ('SIMULATION', 'HARDWARE'):
            raise SpectrumError('explicit SIMULATION or HARDWARE source required')
        context = (center, rate, source)
        if context != self._context:
            self.ring.clear()  # Never combine different tunings, clocks or sources.
            self._context = context
        added = self.ring.append(samples)
        count = min(len(self.ring), size) if added else 0
        if count == size:
            iq = self.ring.tail(size)
            transformed = np.fft.fftshift(np.fft.fft(iq * self._window))
            amplitude = np.abs(transformed) / self._coherent_gain
            # Explicit finite floor; masked/no-data bins become null below.
            power = (20 * np.log10(np.maximum(amplitude, 1e-15))).tolist()
        else:
            power = [None] * size
        frame = {'v': 1, 'kind': 'spectrum', 'center_hz': center, 'sample_rate_hz': rate,
                 'fft_size': size, 'power_dbfs': power, 'valid': [count == size] * size,
                 'relative_frequency_hz': [(i - size // 2) * width for i in range(size)],
                 'source': source, 'sample_count': count}
        return validate_frame(mask_frame(frame))
