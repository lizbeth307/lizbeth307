"""Sealed Pico calibration must verify identically on CPython and float32 MicroPython."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

PICO = Path(__file__).resolve().parents[2] / "firmware" / "pico"
sys.path.insert(0, str(PICO))
import calibration as pico
from srrx.commissioning import CAL_FIELDS, ValidationError, _calibration

SERIAL = "e6616407e35b8d29"


def float32(text):
    # RP2040 MicroPython (MICROPY_FLOAT_IMPL_FLOAT) parses every JSON float as binary32.
    return struct.unpack("<f", struct.pack("<f", float(text)))[0]


def bench():
    # Uneven bench fit whose float coefficients have 9..12 significant digits.
    return pico.from_two_points(SERIAL, 40217, 11203.0, 50133, 14012.0, 0.4, -0.3, "DMM-17/log-0042")


class FixedPointCalibrationTests(unittest.TestCase):
    def test_host_and_pico_share_exact_integer_schema(self):
        self.assertEqual(pico.CAL_FIELDS, CAL_FIELDS)
        record = bench()
        self.assertEqual(set(record), set(CAL_FIELDS) | {"crc32"})
        for key in ("scale_nv_per_count", "offset_uv", "panel_offset_mc", "case_offset_mc"):
            self.assertIs(type(record[key]), int, key)
        self.assertEqual((record["panel_offset_mc"], record["case_offset_mc"]), (400, -300))
        self.assertNotIn(".", json.dumps({k: record[k] for k in CAL_FIELDS if type(record[k]) is int}))

    def test_single_precision_parse_keeps_crc_and_battery_values(self):
        record = bench()
        text = json.dumps(record)
        device = json.loads(text, parse_float=float32)
        self.assertEqual(device, record)
        self.assertEqual(pico._canonical(device, pico.CAL_FIELDS), pico._canonical(record, pico.CAL_FIELDS))
        host, cal = pico.validate(record, SERIAL), pico.validate(device, SERIAL)
        for raw in (40217, 45000, 50133, 60000):
            expected = (raw * record["scale_nv_per_count"] + record["offset_uv"] * 1000 + 500000) // 1000000
            self.assertEqual(cal.battery_mv(raw), expected)
            self.assertEqual(host.battery_mv(raw), expected)
        self.assertEqual(cal.battery_mv(40217), 11203)
        self.assertEqual(cal.battery_mv(50133), 14012)
        self.assertAlmostEqual(cal.temperature_c(32768, "panel"), 25.4, delta=0.01)

    def test_known_canonical_crc_vector_matches_zlib_and_host(self):
        record = {"v": 1, "revision": "E3-v2.1", "serial": SERIAL, "scale_nv_per_count": 280000,
                  "offset_uv": -24474, "panel_offset_mc": 200, "case_offset_mc": -100,
                  "reference_id": "DMM-01/log-01"}
        canonical = ("v=1\nrevision=E3-v2.1\nserial=e6616407e35b8d29\nscale_nv_per_count=280000\n"
                     "offset_uv=-24474\npanel_offset_mc=200\ncase_offset_mc=-100\n"
                     "reference_id=DMM-01/log-01\n").encode()
        self.assertEqual(pico._canonical(record, pico.CAL_FIELDS), canonical)
        sealed = pico.seal(record)
        self.assertEqual(sealed["crc32"], "%08x" % (zlib.crc32(canonical) & 0xffffffff))
        _calibration(sealed, SERIAL)  # host validator agrees with the Pico seal
        pico.validate(sealed, SERIAL)

    def test_float_or_legacy_records_cannot_be_sealed_or_accepted(self):
        record = bench()
        for key, value in (("scale_nv_per_count", 283279.0), ("offset_uv", float32("-189653.6")),
                           ("panel_offset_mc", True)):
            with self.subTest(key=key):
                changed = dict(record, **{key: value})
                if type(value) is float:
                    with self.assertRaises(ValueError):
                        pico.seal({k: changed[k] for k in CAL_FIELDS})
                with self.assertRaises(ValueError):
                    pico.validate(changed, SERIAL)
                with self.assertRaises(ValidationError):
                    _calibration(changed, SERIAL)
        legacy = {"v": 1, "revision": "E3-v2.1", "serial": SERIAL, "scale_mv_per_count": 0.28,
                  "offset_mv": 0.0, "panel_offset_c": 0.0, "case_offset_c": 0.0,
                  "reference_id": "DMM-01/log-01", "crc32": "00000000"}
        with self.assertRaises(ValueError):
            pico.validate(legacy, SERIAL)
        with self.assertRaises(ValueError):
            pico.validate(dict(record, scale_mv_per_count=0.28), SERIAL)  # unsealed extra key
        with self.assertRaises(ValidationError):
            _calibration(dict(record, scale_mv_per_count=0.28), SERIAL)

    def test_integer_ranges_match_on_host_and_pico(self):
        for key, low, high in (("scale_nv_per_count", 220000, 340000), ("offset_uv", -1000000, 1000000),
                               ("panel_offset_mc", -10000, 10000), ("case_offset_mc", -10000, 10000)):
            for value, accepted in ((low, True), (high, True), (low - 1, False), (high + 1, False)):
                with self.subTest(key=key, value=value):
                    base = {"v": 1, "revision": "E3-v2.1", "serial": SERIAL, "scale_nv_per_count": 280000,
                            "offset_uv": 0, "panel_offset_mc": 0, "case_offset_mc": 0, "reference_id": "DMM-01"}
                    record = pico.seal(dict(base, **{key: value}))
                    if accepted:
                        pico.validate(record, SERIAL)
                        _calibration(record, SERIAL)
                    else:
                        with self.assertRaises(ValueError):
                            pico.validate(record, SERIAL)
                        with self.assertRaises(ValidationError):
                            _calibration(record, SERIAL)

    def test_bench_offsets_must_be_finite_degrees(self):
        for offset in (float("nan"), float("inf"), 10.5, None):
            with self.assertRaises(ValueError):
                pico.from_two_points(SERIAL, 40217, 11203.0, 50133, 14012.0, offset, 0, "DMM-17")


if __name__ == "__main__":
    unittest.main()
