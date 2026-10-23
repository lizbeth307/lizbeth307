"""CRC-protected, device-bound ADC coefficients; also a CPython bench helper.

There are deliberately no valid nominal coefficients. A CRC detects corruption,
not malicious edits. These locally provisioned records are not accepted on UART.
"""
try:
    import json
except ImportError:
    import ujson as json
import math

REVISION = "E3-v2.1"
# Integer fixed point: nV/count, uV and milli-degC. No float is ever sealed.
CAL_FIELDS = ("v", "revision", "serial", "scale_nv_per_count", "offset_uv",
              "panel_offset_mc", "case_offset_mc", "reference_id")
COMMISSION_FIELDS = ("v", "revision", "serial", "calibration_crc32",
                     "hardware_commissioned", "qualification_record")


def crc32(data):
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for unused in range(8):
            crc = (crc >> 1) ^ (0xedb88320 if crc & 1 else 0)
    return crc ^ 0xffffffff


def _canonical(record, fields):
    # A fixed field list avoids reliance on JSON sort_keys in MicroPython.
    # Floats are rejected: RP2040 MicroPython is single precision, so float
    # text cannot reproduce a CPython-sealed CRC. int/str/bool text is exact.
    values = []
    for key in fields:
        value = record[key]
        if type(value) is int:
            value = str(value)
        elif type(value) is bool:
            value = "true" if value else "false"
        if not isinstance(value, str) or "\n" in value or "\r" in value:
            raise ValueError("invalid record field: " + key)
        values.append(key + "=" + value)
    return ("\n".join(values) + "\n").encode()


def seal(record, commissioning=False):
    fields = COMMISSION_FIELDS if commissioning else CAL_FIELDS
    result = dict(record)
    result["crc32"] = "%08x" % crc32(_canonical(result, fields))
    return result


def _valid_crc(record, fields):
    try:
        return record.get("crc32") == "%08x" % crc32(_canonical(record, fields))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def _finite(value, low, high):
    return type(value) in (int, float) and value == value and low <= value <= high


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def validate(record, serial, revision=REVISION):
    if (not isinstance(record, dict) or set(record) != set(CAL_FIELDS + ("crc32",))
            or not _valid_crc(record, CAL_FIELDS)):
        raise ValueError("calibration CRC or fields invalid")
    if (type(record["v"]) is not int or record["v"] != 1
            or record["revision"] != revision or record["serial"] != serial):
        raise ValueError("calibration revision or device mismatch")
    if not _integer(record["scale_nv_per_count"], 220000, 340000):
        raise ValueError("ADC scale outside plausible 1:6/3.0V range")
    if not _integer(record["offset_uv"], -1000000, 1000000):
        raise ValueError("ADC offset invalid")
    for field in ("panel_offset_mc", "case_offset_mc"):
        if not _integer(record[field], -10000, 10000):
            raise ValueError("NTC offset invalid")
    if not record["reference_id"]:
        raise ValueError("reference instrument/log ID required")
    return Calibration(record)


def commissioning_valid(record, calibration_record, serial, revision=REVISION):
    return (isinstance(record, dict) and _valid_crc(record, COMMISSION_FIELDS)
            and type(record.get("v")) is int and record["v"] == 1
            and record.get("revision") == revision and record.get("serial") == serial
            and record.get("calibration_crc32") == calibration_record.get("crc32")
            and record.get("hardware_commissioned") is True
            and isinstance(record.get("qualification_record"), str)
            and bool(record["qualification_record"].strip()))


def load(path):
    with open(path, "r") as handle:
        return json.load(handle)


# Selected manufacturer R/T points, kohm, within the -20..120 C operating range.
# Semiware MF52A103F3950 Rev A2.0, pp3-4; include exact 60/68 C gate points.
# https://semiware.com/uploads/datasheet/MF52A103F3950.pdf
NTC_RT = ((-20, 97.8396), (-15, 73.4018), (-10, 55.5953), (-5, 42.4906),
          (0, 32.7547), (5, 25.4562), (10, 19.9380), (15, 15.7317),
          (20, 12.5005), (25, 10.0000), (30, 8.0512), (35, 6.5221),
          (40, 5.3146), (45, 4.3551), (50, 3.5882), (55, 2.9717),
          (60, 2.4734), (65, 2.0686), (68, 1.8623), (70, 1.7380),
          (75, 1.4667), (80, 1.2431), (85, 1.0580), (90, 0.9040),
          (95, 0.7754), (100, 0.6676), (105, 0.5769), (110, 0.5002),
          (115, 0.4352), (120, 0.3799))


def ntc_temperature(raw_u16, offset_c=0):
    # Rtop=10k, NTC to GND, both ADC and divider referenced to E3_ADC3V0.
    if type(raw_u16) is not int or not 16 < raw_u16 < 65519:
        return None
    resistance_kohm = 10.0 * raw_u16 / (65535 - raw_u16)
    if not NTC_RT[-1][1] <= resistance_kohm <= NTC_RT[0][1]:
        return None
    for index in range(len(NTC_RT) - 1):
        t0, r0 = NTC_RT[index]
        t1, r1 = NTC_RT[index + 1]
        if r1 <= resistance_kohm <= r0:
            fraction = math.log(resistance_kohm / r0) / math.log(r1 / r0)
            result = t0 + fraction * (t1 - t0) + offset_c
            return result if -20 <= result <= 120 else None
    return None


class Calibration:
    def __init__(self, record):
        self.record = record

    def battery_mv(self, raw_u16):
        if type(raw_u16) is not int or not 16 < raw_u16 < 65519:
            return None
        # Exact integer nV, identical on CPython and single-precision Pico.
        nv = raw_u16 * self.record["scale_nv_per_count"] + self.record["offset_uv"] * 1000
        return (nv + 500000) // 1000000 if 8000000000 <= nv <= 17500000000 else None

    def temperature_c(self, raw_u16, sensor):
        if sensor not in ("panel", "case"):
            raise ValueError("unknown NTC")
        return ntc_temperature(raw_u16, self.record[sensor + "_offset_mc"] / 1000)


def from_two_points(serial, raw_low, mv_low, raw_high, mv_high,
                    panel_offset_c, case_offset_c, reference_id):
    if (type(raw_low) is not int or type(raw_high) is not int
            or not 16 < raw_low < raw_high < 65519
            or not _finite(mv_low, 10000, 16000)
            or not _finite(mv_high, 13000, 17000)
            or mv_high - mv_low < 2000):
        raise ValueError("two measured points must span at least 2000mV")
    if not _finite(panel_offset_c, -10, 10) or not _finite(case_offset_c, -10, 10):
        raise ValueError("NTC offset invalid")
    scale = int(round((mv_high - mv_low) * 1000000 / (raw_high - raw_low)))
    record = seal({"v": 1, "revision": REVISION, "serial": serial,
                   "scale_nv_per_count": scale,
                   "offset_uv": int(round(mv_low * 1000 - raw_low * scale / 1000)),
                   "panel_offset_mc": int(round(panel_offset_c * 1000)),
                   "case_offset_mc": int(round(case_offset_c * 1000)),
                   "reference_id": reference_id})
    validate(record, serial)
    return record


def main():
    # CPython-only bench CLI. Importing this module on Pico is portable.
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="Pico machine.unique_id().hex()")
    parser.add_argument("--raw-low", type=int, required=True)
    parser.add_argument("--mv-low", type=float, required=True)
    parser.add_argument("--raw-high", type=int, required=True)
    parser.add_argument("--mv-high", type=float, required=True)
    parser.add_argument("--panel-offset-c", type=float, required=True)
    parser.add_argument("--case-offset-c", type=float, required=True)
    parser.add_argument("--reference-id", required=True, help="instrument ID and measurement log")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = from_two_points(args.serial, args.raw_low, args.mv_low,
                             args.raw_high, args.mv_high, args.panel_offset_c,
                             args.case_offset_c, args.reference_id)
    with open(args.output, "w") as handle:
        json.dump(result, handle)
        handle.write("\n")
    print("Calibration written; hardware commissioning remains disabled.")


if __name__ == "__main__":
    main()
