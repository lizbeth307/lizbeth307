"""Bounded SHTP and selected SH-2 reports, portable to MicroPython.

Source formats: CEVA BNO08X 1000-3927 v1.17, SH-2 1000-3625 v1.9,
CEVA sh2.c / sh2_SensorValue.c. No calibration, Euler or GNSS synthesis.
"""
MAX_PACKET_BYTES = 512
CONTROL = 2
INPUT_NORMAL = 3
ROTATION_VECTOR = 0x05
GAME_ROTATION_VECTOR = 0x08
REPORT_INTERVAL_US = 200000
FRESHNESS_MS = 500


class ImuError(ValueError):
    pass


def u16(data, at=0):
    return data[at] | data[at + 1] << 8


def i16(data, at=0):
    value = u16(data, at)
    return value - 65536 if value & 0x8000 else value


def u32(data, at=0):
    return data[at] | data[at + 1] << 8 | data[at + 2] << 16 | data[at + 3] << 24


def i32(data, at=0):
    value = u32(data, at)
    return value - 4294967296 if value & 0x80000000 else value


def put32(value):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ImuError("bad_u32")
    return bytes((value & 255, value >> 8 & 255, value >> 16 & 255, value >> 24 & 255))


def header_length(header):
    if len(header) != 4:
        raise ImuError("short_header")
    raw = u16(header)
    if raw == 0:
        return 0  # SPI no-packet indication; not identity or connection proof.
    if raw == 0xFFFF:
        raise ImuError("reserved_length")
    if raw & 0x8000:
        raise ImuError("continuation_unsupported")
    if raw < 4 or raw > MAX_PACKET_BYTES:
        raise ImuError("packet_length")
    if header[2] >= 6:
        raise ImuError("bad_channel")
    return raw


def make_packet(channel, sequence, payload):
    if type(channel) is not int or not 0 <= channel < 6:
        raise ImuError("bad_channel")
    if type(sequence) is not int or not 0 <= sequence <= 255:
        raise ImuError("bad_shtp_sequence")
    if not isinstance(payload, (bytes, bytearray)) or len(payload) + 4 > MAX_PACKET_BYTES:
        raise ImuError("packet_length")
    length = len(payload) + 4
    return bytes((length & 255, length >> 8, channel, sequence)) + bytes(payload)


class SHTPDecoder:
    """Incremental packet decoder; faults latch until reset, max buffer 512.

    No guessed scanning/resync inside an SPI cargo. A corrupt length, unexpected
    channel sequence or any continuation requires a sensor reset/re-handshake.
    SHTP's per-channel 8-bit counters DO wrap modulo 256 (unlike wire.q).
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self._buffer = bytearray()
        self._length = None
        self._next_sequence = [0] * 6
        self.fault = None

    @property
    def buffered_bytes(self):
        return len(self._buffer)

    def _fail(self, reason):
        self._buffer = bytearray()
        self._length = None
        self.fault = reason
        raise ImuError(reason)

    def feed(self, data):
        if self.fault:
            raise ImuError(self.fault)
        if not isinstance(data, (bytes, bytearray, memoryview)):
            self._fail("packet_type")
        result = []
        for byte in data:
            if type(byte) is not int or not 0 <= byte <= 255:
                self._fail("packet_type")
            self._buffer.append(byte)
            if len(self._buffer) == 4:
                try:
                    self._length = header_length(self._buffer)
                except ImuError as error:
                    self._fail(str(error))
                if self._length == 0:
                    self._buffer = bytearray()
                    self._length = None
                    continue
            if self._length is not None and len(self._buffer) == self._length:
                channel, sequence = self._buffer[2], self._buffer[3]
                if sequence != self._next_sequence[channel]:
                    self._fail("shtp_sequence")
                self._next_sequence[channel] = (sequence + 1) & 255
                result.append((channel, bytes(self._buffer[4:])))
                self._buffer = bytearray()
                self._length = None
        return result


def product_id_request():
    return b"\xF9\x00"


def parse_product_id(payload):
    if len(payload) != 16 or payload[0] != 0xF8:
        raise ImuError("product_id_length")
    part = u32(payload, 4)
    if part in (0, 0xFFFFFFFF):
        raise ImuError("product_id_invalid")
    return {"reset_cause": payload[1], "major": payload[2], "minor": payload[3],
            "part": part, "build": u32(payload, 8), "patch": u16(payload, 12)}


def set_feature(report_id=ROTATION_VECTOR, interval_us=REPORT_INTERVAL_US):
    if report_id not in (ROTATION_VECTOR, GAME_ROTATION_VECTOR):
        raise ImuError("unsupported_feature")
    if type(interval_us) is not int or not 20000 <= interval_us <= 200000:
        raise ImuError("feature_interval")
    # 17 bytes: FD, report, flags0, sensitivity0, report interval, batch0, config0.
    return bytes((0xFD, report_id, 0, 0, 0)) + put32(interval_us) + bytes(8)


def get_feature(report_id=ROTATION_VECTOR):
    if report_id not in (ROTATION_VECTOR, GAME_ROTATION_VECTOR):
        raise ImuError("unsupported_feature")
    return bytes((0xFE, report_id))


def validate_feature_response(payload, report_id=ROTATION_VECTOR,
                              interval_us=REPORT_INTERVAL_US):
    if len(payload) != 17 or payload[0] != 0xFC or payload[1] != report_id:
        raise ImuError("feature_response")
    if payload[2:5] != b"\x00\x00\x00" or u32(payload, 5) != interval_us:
        raise ImuError("feature_mismatch")
    if u32(payload, 9) != 0 or u32(payload, 13) != 0:
        raise ImuError("feature_mismatch")
    return True


def parse_sensor_cargo(payload):
    """Validate a complete normal-input cargo before returning any samples.

    Sample order [i,j,k,real] == [x,y,z,w], signed int16 Q14. Rotation-vector
    accuracy is signed Q12 radians; game rotation has no accuracy estimate.
    Base/rebase values and report delay are 100us ticks relative to H_INTN.
    """
    if not payload or payload[0] != 0xFB:
        raise ImuError("missing_timestamp")
    cursor, base, have_base = 0, 0, False
    samples = []
    while cursor < len(payload):
        report = payload[cursor]
        if report in (0xFB, 0xFA):
            if cursor + 5 > len(payload):
                raise ImuError("short_timestamp")
            delta = i32(payload, cursor + 1)
            if delta == 0x7FFFFFFF:
                raise ImuError("invalid_timestamp")
            if report == 0xFB:
                base, have_base = -delta, True
            elif not have_base:
                raise ImuError("missing_timestamp")
            else:
                base += delta
            cursor += 5
            continue
        length = 14 if report == ROTATION_VECTOR else 12 if report == GAME_ROTATION_VECTOR else 0
        if not length:
            raise ImuError("unexpected_report")
        if cursor + length > len(payload):
            raise ImuError("short_report")
        values = [i16(payload, cursor + offset) / 16384.0 for offset in (4, 6, 8, 10)]
        norm_sq = sum(value * value for value in values)
        if not 0.90 <= norm_sq <= 1.10:
            raise ImuError("quaternion_norm")
        status_byte = payload[cursor + 2]
        delay = ((status_byte & 0xFC) << 6) | payload[cursor + 3]
        age_us = -(base + delay) * 100
        if age_us < 0 or age_us >= FRESHNESS_MS * 1000:
            raise ImuError("stale_sensor_report")
        accuracy = i16(payload, cursor + 12) / 4096.0 if length == 14 else None
        if accuracy is not None and accuracy < 0:
            raise ImuError("invalid_accuracy")
        sample = {"quaternion": values, "report_id": report,
                  "sample_seq": payload[cursor + 1], "status": status_byte & 3,
                  "sensor_age_us": age_us}
        if accuracy is not None:
            sample["heading_accuracy_rad"] = accuracy
        samples.append(sample)
        cursor += length
    if not samples:
        raise ImuError("no_rotation_report")
    return samples
