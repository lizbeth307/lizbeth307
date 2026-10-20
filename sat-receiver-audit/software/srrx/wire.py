"""Bounded UART framing shared by CPython host and MicroPython Pico.

Framing is integrity/error detection, not authentication. Session and sequence
ordering belong to the controllers. No hardware or serial dependency lives here.
"""
try:
    import json
except ImportError:  # Older MicroPython builds expose only ujson.
    import ujson as json

MAX_FRAME_BYTES = 512
UINT32_MAX = 0xFFFFFFFF
FRAME_TYPES = ("HELLO", "HB", "ARM", "CONFIGURED", "TRIP", "SHUTDOWN", "STATUS", "EVENT")
_FIELDS = ("v", "t", "s", "q", "p")
_HEX = b"0123456789ABCDEF"


def crc16_ccitt_false(data):
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xffff, no reflect/xorout."""
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _validate_outer(frame):
    if type(frame) is not dict or len(frame) != 5:
        raise ValueError("frame must have exactly v,t,s,q,p")
    for key in _FIELDS:
        if key not in frame:
            raise ValueError("missing frame field")
    if type(frame["v"]) is not int or frame["v"] != 1:
        raise ValueError("unsupported version")
    if type(frame["t"]) is not str or frame["t"] not in FRAME_TYPES:
        raise ValueError("unsupported message type")
    for key in ("s", "q"):
        value = frame[key]
        if type(value) is not int or value < 0 or value > UINT32_MAX:
            raise ValueError("session and sequence must be uint32, not bool")
    if type(frame["p"]) is not dict:
        raise ValueError("payload must be an object")


def _validate_json_values(value):
    """Reject non-JSON values/nonfinite floats and bound encoder traversal.

    The conservative lower size bound stops cyclic or huge caller-owned objects
    before json.dumps; the exact encoded UTF-8 size is checked afterwards.
    """
    pending = [value]
    lower_size = 0
    while pending:
        obj = pending.pop()
        kind = type(obj)
        if kind is dict:
            if len(obj) > MAX_FRAME_BYTES:
                raise ValueError("object is too large")
            lower_size += 2 + max(0, len(obj) - 1)
            for key in obj:
                if type(key) is not str or len(key) > MAX_FRAME_BYTES:
                    raise ValueError("JSON object keys must be bounded strings")
                lower_size += len(key) + 3  # quotes and colon
                pending.append(obj[key])
        elif kind is list:
            if len(obj) > MAX_FRAME_BYTES:
                raise ValueError("array is too large")
            lower_size += 2 + max(0, len(obj) - 1)
            pending.extend(obj)
        elif kind is str:
            lower_size += len(obj) + 2
        elif obj is None:
            lower_size += 4
        elif kind is bool:
            lower_size += 4 if obj else 5
        elif kind is int:
            # A huge bigint must not allocate a huge decimal string in dumps.
            if obj > 10 ** MAX_FRAME_BYTES or obj < -(10 ** MAX_FRAME_BYTES):
                raise ValueError("integer is too large")
            lower_size += len(str(obj))
        elif kind is float:
            if obj != obj or obj == float("inf") or obj == -float("inf"):
                raise ValueError("nonfinite JSON number")
            lower_size += 1
        else:
            raise ValueError("unsupported JSON value")
        if lower_size > MAX_FRAME_BYTES - 7 or len(pending) > MAX_FRAME_BYTES:
            raise ValueError("frame is too large or cyclic")


def _reject_duplicate_keys(text):
    """Check decoded key names without CPython-only object_pairs_hook.

    json.loads is still responsible for JSON grammar. A small lexical walk lets
    both runtimes reject duplicate keys, including escaped-name aliases, before
    the JSON module can silently overwrite them. Applies at every object level.
    """
    stack = []  # object: [dict of keys, expecting key]; array: None
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if char == '"':
            start = i
            i += 1
            while i < length:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    break
                else:
                    i += 1
            if i >= length:
                raise ValueError("unterminated JSON string")
            if stack and stack[-1] is not None and stack[-1][1]:
                key = json.loads(text[start:i + 1])
                keys = stack[-1][0]
                if key in keys:
                    raise ValueError("duplicate JSON object key")
                keys[key] = True
                stack[-1][1] = False
        elif char == "{":
            stack.append([{}, True])
        elif char == "[":
            stack.append(None)
        elif char in "}]":
            if not stack:
                raise ValueError("unbalanced JSON container")
            stack.pop()
        elif char == "," and stack and stack[-1] is not None:
            stack[-1][1] = True
        i += 1


def encode_frame(frame):
    """Return an at-most-512-byte frame; invalid caller input raises ValueError."""
    try:
        _validate_outer(frame)
        _validate_json_values(frame)
        body = json.dumps(frame, separators=(",", ":")).encode("utf-8")
        if len(body) + 7 > MAX_FRAME_BYTES:
            raise ValueError("encoded frame exceeds 512 bytes")
        # Newlines in JSON strings are escaped by json.dumps, never raw LF.
        crc = crc16_ccitt_false(body)
        trailer = bytes((_HEX[(crc >> 12) & 15], _HEX[(crc >> 8) & 15],
                         _HEX[(crc >> 4) & 15], _HEX[crc & 15]))
        return b"@" + body + b"|" + trailer + b"\n"
    except Exception as exc:
        # Normalize serializer/runtime-specific errors for the caller.
        raise ValueError("invalid UART frame: " + str(exc))


def _require_utf8(data):
    """Validate scalar UTF-8 explicitly, independent of runtime decoder strictness."""
    i = 0
    while i < len(data):
        first = data[i]
        if first < 0x80:
            i += 1
            continue
        low, high = 0x80, 0xBF
        if 0xC2 <= first <= 0xDF:
            count = 2
        elif 0xE0 <= first <= 0xEF:
            count = 3
            if first == 0xE0:
                low = 0xA0
            elif first == 0xED:
                high = 0x9F  # UTF-16 surrogate code points are not Unicode scalars.
        elif 0xF0 <= first <= 0xF4:
            count = 4
            if first == 0xF0:
                low = 0x90
            elif first == 0xF4:
                high = 0x8F
        else:
            raise ValueError("invalid UTF-8 lead byte")
        if i + count > len(data) or not low <= data[i + 1] <= high:
            raise ValueError("invalid UTF-8 sequence")
        for offset in range(2, count):
            if not 0x80 <= data[i + offset] <= 0xBF:
                raise ValueError("invalid UTF-8 continuation")
        i += count


def _parse_candidate(candidate):
    if len(candidate) < 7 or candidate[0] != 64 or candidate[-5] != 124:
        raise ValueError("bad UART framing")
    check = 0
    for byte in candidate[-4:]:
        if 48 <= byte <= 57:
            nibble = byte - 48
        elif 65 <= byte <= 70:
            nibble = byte - 55
        elif 97 <= byte <= 102:
            nibble = byte - 87
        else:
            raise ValueError("CRC must have exactly four hex digits")
        check = (check << 4) | nibble
    body = bytes(candidate[1:-5])
    if check != crc16_ccitt_false(body):
        raise ValueError("CRC mismatch")
    _require_utf8(body)
    text = body.decode("utf-8")
    _reject_duplicate_keys(text)
    frame = json.loads(text)
    _validate_outer(frame)
    _validate_json_values(frame)
    return frame


class FrameDecoder:
    """Incremental decoder with at most 511 retained bytes.

    feed returns valid frames and drops malformed input. errors counts rejected
    candidates, oversize candidates, invalid feed arguments, and noise runs,
    saturating at uint32 max. No sequence/session tracking occurs in this class.
    """
    def __init__(self):
        self._buffer = bytearray()
        self.errors = 0
        self._noise = False

    @property
    def buffered_bytes(self):
        return len(self._buffer)

    def reset(self):
        """Drop any partial frame; preserve lifetime error count."""
        self._buffer = bytearray()
        self._noise = False

    def _error(self):
        if self.errors < UINT32_MAX:
            self.errors += 1

    def _line(self):
        candidate = self._buffer
        try:
            return _parse_candidate(candidate)
        except Exception:
            self._error()
        # Recover a valid suffix after malformed/truncated prefix, without
        # mistaking '@' in a valid payload string for an unconditional reset.
        for start in range(len(candidate) - 1, 0, -1):
            if candidate[start] == 64:
                try:
                    return _parse_candidate(candidate[start:])
                except Exception:
                    pass
        return None

    def feed(self, data):
        frames = []
        if data is None:  # machine.UART.read() returns None on timeout.
            return frames
        if not isinstance(data, (bytes, bytearray, memoryview)):
            self._error()
            return frames
        for byte in data:
            if type(byte) is not int or byte < 0 or byte > 255:
                self._error()
                self.reset()
                continue
            if not self._buffer:
                if byte == 64:  # '@'
                    self._buffer.append(byte)
                    self._noise = False
                elif byte == 10:
                    self._noise = False
                elif not self._noise:
                    self._error()
                    self._noise = True
                continue
            if byte == 10:
                frame = self._line()
                self._buffer = bytearray()
                self._noise = False
                if frame is not None:
                    frames.append(frame)
            elif len(self._buffer) < MAX_FRAME_BYTES - 1:
                self._buffer.append(byte)
            else:
                self._error()
                self._buffer = bytearray()
                self._noise = True
                if byte == 64:
                    self._buffer.append(byte)
                    self._noise = False
        return frames
