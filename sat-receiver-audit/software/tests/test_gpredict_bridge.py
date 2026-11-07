"""srrx.gpredict_bridge: TLE text, five-digit aliases and the Gpredict files (W2 SW-GPREDICT).

Host tests only. Element sets, NORAD ids (also those above 99999) and the observer are
synthetic. Equality with sgp4 2.27's exporter and the sgp4 round trip need sgp4 (the CI host
regression pins it, sr-rx-verify PY_PINS); Gpredict's acceptance rules are re-implemented from
v2.7 src/sgpsdp/sgp_in.c:52-147. No GUI and no receiver: the Doppler loop with SDR++ stays a
device row.
"""
from contextlib import redirect_stdout
import fnmatch
import importlib.util
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

from srrx import gpredict_bridge as gb, orbits, pass_jobs

ROOT = Path(__file__).resolve().parents[2]
RECIPE = ROOT / "deployment/recipes/gpredict"
HAVE_SGP4 = importlib.util.find_spec("sgp4") is not None
EPOCH = "2026-11-05T11:23:45.123456"


def raw(norad, **changes):
    value = {"OBJECT_NAME": "SYNTHETIC LEO %d" % norad, "OBJECT_ID": "2026-123A", "EPOCH": EPOCH,
             "MEAN_MOTION": 15.50123456, "ECCENTRICITY": 0.0004567, "INCLINATION": 51.6416, "RA_OF_ASC_NODE": 123.4567,
             "ARG_OF_PERICENTER": 89.1234, "MEAN_ANOMALY": 270.9876, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
             "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 12345, "BSTAR": 0.00012345,
             "MEAN_MOTION_DOT": 0.00001234, "MEAN_MOTION_DDOT": 0.0}
    value.update(changes)
    return value


def record(norad, name=None, **changes):
    normal = orbits.elements(raw(norad, **changes))
    target = {"norad_id": norad, "name": name or "SYNTH %d" % norad, "role": "OTHER"}
    return orbits._record(normal, target, None, False)


def location(**changes):
    status = {"available": True, "source": "nmea", "origin": "nmea", "fresh": True, "live_fix": True, "mode": 3,
              "satellites": 9, "lat": 50.0432109, "lon": 10.0123456, "age_ms": 300, "alt_hae_m": 263.4,
              "reason": None, "hdop": 0.8, "device": "/dev/lab/gnss"}
    status.update(changes)
    return status


def random_elements(rng):
    """Synthetic element sets with TLE-representable values (TLE digits, exponents >= -9)."""
    return raw(rng.randint(1, 999999),
               EPOCH="2026-%02d-%02dT%02d:%02d:%02d.%06d" % (rng.randint(1, 12), rng.randint(1, 28), rng.randint(0, 23),
                                                             rng.randint(0, 59), rng.randint(0, 59), rng.randint(0, 999999)),
               MEAN_MOTION=round(rng.uniform(0.9, 16.5), 8), ECCENTRICITY=round(rng.uniform(0.0, 0.7), 7),
               INCLINATION=round(rng.uniform(0.0, 180.0), 4), RA_OF_ASC_NODE=round(rng.uniform(0.0, 359.9999), 4),
               ARG_OF_PERICENTER=round(rng.uniform(0.0, 359.9999), 4), MEAN_ANOMALY=round(rng.uniform(0.0, 359.9999), 4),
               BSTAR=rng.choice([0.0, 1.2345e-5, round(rng.uniform(-1e-3, 1e-3), 9)]),
               MEAN_MOTION_DOT=rng.choice([0.0, round(rng.uniform(-1e-4, 1e-4), 8)]),
               MEAN_MOTION_DDOT=rng.choice([0.0, 1.2345e-6, -3.1e-9, round(rng.uniform(-1e-5, 1e-5), 10)]),
               REV_AT_EPOCH=rng.randint(0, 99999), ELEMENT_SET_NO=rng.randint(0, 9999))


def gpredict_accepts(line1, line2):
    """Good_Elements of Gpredict 2.7 (src/sgpsdp/sgp_in.c:122-147) with Checksum_Good and
    Epoch_Good, on the two lines concatenated the way gtk_sat_data_read_sat does."""
    tle = line1 + line2

    def checksum_good(start):
        total = sum(int(c) if c.isdigit() else 1 if c == "-" else 0 for c in tle[start:start + 68])
        return total % 10 == ord(tle[start + 68]) - ord("0")

    def epoch_good():
        if not (tle[18].isdigit() and tle[19].isdigit()):
            return False
        if any(not (tle[i].isdigit() or tle[i] == " ") for i in (20, 21)) or (tle[20] != " " and tle[21] == " "):
            return False
        if not tle[22].isdigit() or not tle[24].isdigit():
            return False
        i = 25
        while i < 32 and tle[i] != " ":
            if not tle[i].isdigit():
                return False
            i += 1
        return all(c == " " for c in tle[i:32])
    return (len(line1) == 69 and len(line2) == 69 and checksum_good(0) and checksum_good(69) and tle[0] == "1" and tle[69] == "2"
            and tle[2:7] == tle[71:76] and all(tle[i] == "." for i in (23, 34, 80, 89, 106, 115, 123)) and tle[61:64] == " 0 "
            and epoch_good())


def ini(text):
    """[group] -> {key: [values]} with the parsing rules of selftest.py _ini (keys lower case)."""
    sections, section = {}, ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        key, sep, value = line.partition("=")
        if sep:
            sections.setdefault(section, {}).setdefault(key.strip().lower(), []).append(value.strip())
    return sections


class TleTextTests(unittest.TestCase):
    def test_lines_have_valid_checksums_and_gpredict_accepts_them(self):
        line1, line2 = gb.tle_lines(orbits.elements(raw(25544)), 25544)
        self.assertEqual(line1, "1 25544U 26123A   26309.47482782  .00001234  00000-0  12345-3 0  9994")
        self.assertEqual(line2, "2 25544  51.6416 123.4567 0004567  89.1234 270.9876 15.50123456123458")
        for line in (line1, line2):
            self.assertEqual(int(line[68]), gb.checksum(line))
        self.assertTrue(gpredict_accepts(line1, line2))
        rng = random.Random(20261107)
        for unused in range(300):
            elements = orbits.elements(random_elements(rng))
            self.assertTrue(gpredict_accepts(*gb.tle_lines(elements, rng.randint(1, 99999))), elements)

    def test_fields_read_back_to_the_omm_values(self):
        elements = orbits.elements(raw(123456, INCLINATION=98.7123, ECCENTRICITY=0.1234567, MEAN_MOTION=1.00271234,
                                       REV_AT_EPOCH=4321, ELEMENT_SET_NO=7, BSTAR=-0.000312, MEAN_MOTION_DOT=-0.00000042))
        line1, line2 = gb.tle_lines(elements, 4242)
        self.assertEqual((line1[2:7], line2[2:7], line1[7], line1[9:17].strip()), ("04242", "04242", "U", "26123A"))
        self.assertAlmostEqual(float(line2[8:16]), 98.7123, places=9)
        self.assertEqual(float("0." + line2[26:33]), 0.1234567)
        self.assertAlmostEqual(float(line2[52:63]), 1.00271234, places=9)
        self.assertEqual((int(line2[63:68]), int(line1[64:68]), line1[62]), (4321, 7, "0"))
        self.assertEqual(line1[53:61], "-31200-3")  # BSTAR -0.312e-3
        self.assertEqual(line1[33:43], "-.00000042")
        day = float(line1[20:32])  # day of year 309 (2026-11-05) plus the fraction of 11:23:45.123456
        self.assertLess(abs(day - (309 + (11 * 3600 + 23 * 60 + 45.123456) / 86400)), 0.5e-8)

    def test_out_of_format_values_and_numbers_are_refused(self):
        elements = orbits.elements(raw(25544))
        for catalog in (0, 100000, 123456, True, "25544"):
            with self.assertRaises(gb.BridgeError):
                gb.tle_lines(elements, catalog)
        with self.assertRaisesRegex(gb.BridgeError, "69-column"):
            gb.tle_lines(orbits.elements(raw(25544, MEAN_MOTION_DDOT=1e-12)), 25544)  # two-digit exponent
        with self.assertRaises(orbits.OrbitError):
            gb.tle_lines(dict(elements, EPHEMERIS_TYPE=2), 25544)


@unittest.skipUnless(HAVE_SGP4, "sgp4 not installed (the CI host regression pins sgp4 2.27)")
class Sgp4ExporterTests(unittest.TestCase):
    def satrec(self, elements, catalog):
        from sgp4 import omm
        from sgp4.api import Satrec
        satellite = Satrec()
        omm.initialize(satellite, dict(elements, NORAD_CAT_ID=catalog))
        return satellite

    def test_lines_equal_the_sgp4_exporter(self):
        from sgp4 import exporter
        rng = random.Random(371)
        for unused in range(500):
            elements, catalog = orbits.elements(random_elements(rng)), rng.randint(1, 99999)
            self.assertEqual(gb.tle_lines(elements, catalog), tuple(exporter.export_tle(self.satrec(elements, catalog))), elements)

    def test_round_trip_through_sgp4(self):
        from sgp4.api import Satrec
        from sgp4.conveniences import sat_epoch_datetime
        elements = orbits.elements(raw(123456))
        line1, line2 = gb.tle_lines(elements, 4242)
        parsed, direct = Satrec.twoline2rv(line1, line2), self.satrec(elements, 4242)
        self.assertEqual(parsed.satnum, 4242)
        for field in ("inclo", "nodeo", "argpo", "mo", "ecco", "no_kozai", "bstar", "ndot", "nddot"):
            self.assertAlmostEqual(getattr(parsed, field), getattr(direct, field), places=12, msg=field)
        self.assertEqual((parsed.elnum, parsed.revnum, parsed.ephtype, parsed.classification, parsed.intldesg),
                         (999, 12345, 0, "U", "26123A"))
        self.assertLess(abs((sat_epoch_datetime(parsed).replace(tzinfo=None)
                             - sat_epoch_datetime(direct).replace(tzinfo=None)).total_seconds()), 0.001)
        for minutes in (0.0, 90.0, 1440.0):  # same absolute time: the TLE epoch is rounded to 1e-8 day
            jd, fr = direct.jdsatepoch, direct.jdsatepochF + minutes / 1440.0
            error1, r1, unused = direct.sgp4(jd, fr)
            error2, r2, unused = parsed.sgp4(jd, fr)
            self.assertEqual((error1, error2), (0, 0))
            self.assertLess(max(abs(a - b) for a, b in zip(r1, r2)), 0.01)  # km


class AliasTests(unittest.TestCase):
    def test_five_digit_ids_keep_their_number_and_larger_ids_get_free_aliases(self):
        ids = [25544, 99999, 100000, 123456, 999999]
        mapping = gb.assign_aliases(ids)
        self.assertEqual((mapping[25544], mapping[99999]), (25544, 99999))
        aliases = [mapping[n] for n in (100000, 123456, 999999)]
        self.assertTrue(all(1 <= a <= 99999 for a in aliases))
        self.assertEqual(len(set(mapping.values())), len(ids))
        self.assertFalse(set(aliases) & {25544, 99999})
        self.assertEqual(gb.assign_aliases(list(reversed(ids))), mapping)  # order-independent
        self.assertEqual(gb.assign_aliases(ids), mapping)  # deterministic without a store

    def test_stored_aliases_stay_when_the_set_changes(self):
        first = gb.assign_aliases([123456, 234567, 25544])
        store = gb.parse_aliases(gb.alias_document(first))
        self.assertEqual(store, {123456: first[123456], 234567: first[234567]})
        grown = gb.assign_aliases([123456, 234567, 25544, 345678, 456789, 40069], store)
        self.assertEqual((grown[123456], grown[234567]), (first[123456], first[234567]))
        # A stored alias that a newly allowlisted real five-digit id now uses has to move; the others stay.
        moved = gb.assign_aliases([123456, 234567, first[123456]], store)
        self.assertEqual(moved[first[123456]], first[123456])
        self.assertNotEqual(moved[123456], first[123456])
        self.assertEqual(moved[234567], first[234567])

    def test_a_taken_first_candidate_probes_the_ids_own_sequence(self):
        first = gb._candidate(500000, 0)
        mapping = gb.assign_aliases([500000, first])
        self.assertEqual(mapping[first], first)
        self.assertEqual(mapping[500000], gb._candidate(500000, 1) if gb._candidate(500000, 1) != first else gb._candidate(500000, 2))

    def test_alias_store_is_strict(self):
        good = {"schema_version": 1, "kind": "srrx_gpredict_aliases", "aliases": [{"norad_id": 123456, "catalog": 54321}]}
        self.assertEqual(gb.parse_aliases(good), {123456: 54321})
        for broken in (dict(good, kind="other"), dict(good, schema_version=True), dict(good, extra=1),
                       dict(good, aliases=[{"norad_id": 99999, "catalog": 1}]), dict(good, aliases=[{"norad_id": 123456, "catalog": 0}]),
                       dict(good, aliases=[{"norad_id": 123456, "catalog": 100000}]),
                       dict(good, aliases=[{"norad_id": 123456, "catalog": True}]),
                       dict(good, aliases=[{"norad_id": 123456, "catalog": 1}, {"norad_id": 123457, "catalog": 1}]),
                       dict(good, aliases=[{"norad_id": 123456, "catalog": 1}, {"norad_id": 123456, "catalog": 2}]),
                       dict(good, aliases=[{"norad_id": 123456, "catalog": 1, "x": 0}])):
            with self.assertRaises(gb.BridgeError):
                gb.parse_aliases(broken)
        with self.assertRaises(gb.BridgeError):
            gb.assign_aliases([0])
        with self.assertRaises(gb.BridgeError):
            gb.assign_aliases([1000000])


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-gpredict-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config, self.aliases = self.root / "home/lab/.config/Gpredict", self.root / "var/lib/srrx/gpredict/aliases.json"
        self.stored = pass_jobs.stored_location(location())

    def test_write_leaves_only_the_bridge_satdata_and_rx_only_files(self):
        (self.config / "satdata").mkdir(parents=True)
        for name in ("25544.sat", "amateur.cat", "notes.txt"):
            (self.config / "satdata" / name).write_text("stale\n", encoding="ascii")
        (self.config / "gpredict.cfg").write_text("[GLOBAL]\nWINDOW_WIDTH=900\n[TLE]\nAUTO_UPDATE_FREQ=3\n", encoding="ascii")
        records = [record(25544, "ISS"), record(123456, "NEW OBJECT")]
        result = gb.write(self.config, records, self.stored, self.aliases)
        alias = gb.load_aliases(self.aliases)[123456]
        self.assertEqual(result["aliases"], {"123456": alias})
        self.assertEqual(sorted(p.name for p in (self.config / "satdata").iterdir()),
                         sorted(["25544.sat", "%d.sat" % alias, "srrx.cat", "notes.txt", "cache"]))
        self.assertEqual(result["removed"], ["amateur.cat"])  # 25544.sat was rewritten with labd's elements
        sat = ini((self.config / ("satdata/%d.sat" % alias)).read_text(encoding="ascii"))["satellite"]
        self.assertEqual(sat["name"], ["NEW OBJECT (NORAD 123456, alias %05d)" % alias])
        self.assertEqual(sat["nickname"], ["NEW OBJECT #123456"])
        self.assertEqual((sat["tle1"][0][2:7], sat["tle2"][0][2:7]), ("%05d" % alias, "%05d" % alias))
        self.assertTrue(gpredict_accepts(sat["tle1"][0], sat["tle2"][0]))
        self.assertEqual(ini((self.config / "satdata/25544.sat").read_text(encoding="ascii"))["satellite"]["name"], ["ISS"])
        self.assertEqual((self.config / "satdata/srrx.cat").read_text(encoding="ascii").splitlines(),
                         ["SR-RX (labd OMM)"] + [str(n) for n in sorted([25544, alias])])
        module = ini((self.config / "modules/SR-RX.mod").read_text(encoding="ascii"))["global"]
        self.assertEqual(module["satellites"], ["".join("%d;" % n for n in sorted([25544, alias]))])
        self.assertEqual(module["qthfile"], ["srrx.qth"])
        config = ini((self.config / "gpredict.cfg").read_text(encoding="ascii"))
        self.assertEqual((config["global"]["window_width"], config["tle"]["auto_update_freq"], config["tle"]["urls"]),
                         (["900"], ["0"], [""]))
        self.assertEqual(result["status"], "GPREDICT_FILES_WRITTEN")
        self.assertNotIn("50.0", json.dumps(result))  # the summary carries no coordinates
        # A second run with the store keeps the alias and the files.
        before = {p: p.read_bytes() for p in self.config.rglob("*") if p.is_file()}
        self.assertEqual(gb.write(self.config, records, self.stored, self.aliases)["removed"], [])
        self.assertEqual({p: p.read_bytes() for p in self.config.rglob("*") if p.is_file()}, before)

    def test_qth_is_the_stored_rounded_location_only(self):
        files, unused, skipped = gb.plan([record(25544)], self.stored)
        self.assertEqual(skipped, [])
        qth = ini(files["srrx.qth"])["qth"]
        self.assertEqual((qth["lat"], qth["lon"], qth["alt"], qth["qth_type"]), (["50.0"], ["10.0"], ["300"], ["0"]))
        no_height = pass_jobs.stored_location(location(mode=2))
        self.assertIn("ALT=0\n", gb.plan([record(25544)], no_height)[0]["srrx.qth"])
        for bad in (location(), dict(self.stored, lat=50.04), dict(self.stored, live_fix=True), None,
                    dict(self.stored, alt_hae_m=263.4)):
            with self.assertRaises(gb.BridgeError):
                gb.qth_text(bad)
        self.assertIsNone(pass_jobs.stored_location(location(available=False, lat=None, lon=None, reason="NO_FIX")))

    def test_radio_is_rx_only_at_the_sdrpp_rigctl_server(self):
        radio = ini(gb.RADIO_CONFIG)["radio"]
        self.assertEqual((radio["host"], radio["port"], radio["type"], radio["ptt"]), (["127.0.0.1"], ["4532"], ["0"], ["0"]))
        for key in ("signal_aos", "signal_los", "signal_aoiq", "signal_loiq"):
            self.assertEqual(radio[key], ["false"])
        self.assertNotIn("IQRECORD", gb.RADIO_CONFIG)

    def test_config_merge_enforces_updates_off_and_keeps_user_settings(self):
        user = "# mine\n[GLOBAL]\nOPEN_MODULES=Amateur;SR-RX\nDEFAULT_QTH=home.qth\n\n[TLE]\nAUTO_UPDATE_FREQ=2\nURLS=https://example.invalid/x\n"
        merged = gb.merge_config(user)
        parsed = ini(merged)
        self.assertTrue(merged.startswith("# mine\n"))
        self.assertEqual(parsed["global"]["open_modules"], ["Amateur;SR-RX"])  # a default, not enforced
        self.assertEqual(parsed["global"]["default_qth"], ["srrx.qth"])
        self.assertEqual((parsed["tle"]["auto_update_freq"], parsed["tle"]["urls"], parsed["tle"]["server"]), (["0"], [""], [""]))
        self.assertEqual((parsed["trsp"]["server"], parsed["version"]["major"], parsed["version"]["minor"]), ([""], ["1"], ["4"]))
        self.assertEqual(gb.merge_config(merged), merged)  # idempotent
        self.assertEqual(ini(gb.merge_config(""))["global"]["open_modules"], ["SR-RX"])
        for bad in ("KEY=1\n", "[TLE]\nnot a key\n", "[TLE\nX=1\n"):
            with self.assertRaises(gb.BridgeError):
                gb.merge_config(bad)

    def test_unrepresentable_records_are_listed_not_written(self):
        files, mapping, skipped = gb.plan([record(25544), record(40069, MEAN_MOTION_DDOT=1e-12)], self.stored)
        self.assertEqual(list(mapping), [25544])
        self.assertEqual([s["norad_id"] for s in skipped], [40069])
        self.assertNotIn("satdata/40069.sat", files)
        with self.assertRaises(gb.BridgeError):
            gb.plan([record(40069, MEAN_MOTION_DDOT=1e-12)], self.stored)

    def test_package_skeleton_equals_the_bridge_files(self):
        self.assertEqual((RECIPE / "files/gpredict.cfg").read_text(encoding="ascii"), gb.merge_config(""))
        self.assertEqual((RECIPE / "files/SDRPP-RX.rig").read_text(encoding="ascii"), gb.RADIO_CONFIG)

    def test_written_files_satisfy_the_rx_10_policy_rules(self):
        policy = json.loads((ROOT / "deployment/receive-only-policy.json").read_text(encoding="utf-8"))["components"]["gpredict"]
        gb.write(self.config, [record(25544)], self.stored, self.aliases)
        home = self.config.relative_to(self.root).as_posix()
        radios = [p for p in self.config.rglob("*.rig") if any(fnmatch.fnmatchcase(p.relative_to(self.root).as_posix(), g)
                                                                for g in policy["radio_config_globs"])]
        self.assertEqual([p.name for p in radios], ["SDRPP-RX.rig"])
        self.assertEqual(ini(radios[0].read_text(encoding="ascii"))["radio"]["type"], [policy["rx_only_radio_type"]])
        tle = policy["tle_update"]
        self.assertTrue(any(fnmatch.fnmatchcase(home + "/gpredict.cfg", g) for g in tle["file_globs"]))
        values = ini((self.config / "gpredict.cfg").read_text(encoding="ascii"))[tle["section"].lower()][tle["key"].lower()]
        self.assertEqual(values[-1], tle["required"])
        skel = [(RECIPE / "files/SDRPP-RX.rig", "etc/skel/.config/Gpredict/hwconf/SDRPP-RX.rig"),
                (RECIPE / "files/gpredict.cfg", "etc/skel/.config/Gpredict/gpredict.cfg")]
        self.assertTrue(any(fnmatch.fnmatchcase(skel[0][1], g) for g in policy["radio_config_globs"]))
        self.assertTrue(any(fnmatch.fnmatchcase(skel[1][1], g) for g in tle["file_globs"]))

    def test_cli_writes_from_files_and_blocks_without_a_location(self):
        omm = self.root / "gp.json"
        omm.write_text(json.dumps([raw(25544), raw(123456), raw(40069)]), encoding="ascii")
        allowlist = self.root / "allow.json"
        allowlist.write_text(json.dumps({"schema_version": 1, "kind": "srrx_orbit_allowlist", "targets": [
            {"norad_id": 25544, "name": "ISS", "role": "ISS"}, {"norad_id": 123456, "name": "NEW", "role": "OTHER"}]}), encoding="ascii")
        status = self.root / "location.json"
        status.write_text(json.dumps(location()), encoding="ascii")
        args = ["write", "--omm", str(omm), "--allowlist", str(allowlist), "--location", str(status),
                "--config-dir", str(self.config), "--aliases", str(self.aliases)]
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(gb.main(args), 0)
        report = json.loads(out.getvalue())
        self.assertEqual((report["satellites"], report["aliased"]), (2, 1))  # 40069 is not allowlisted
        self.assertFalse((self.config / "satdata/40069.sat").exists())
        status.write_text(json.dumps(location(available=False, lat=None, lon=None, reason="NO_FIX")), encoding="ascii")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(gb.main(args), 2)
        self.assertEqual(json.loads(out.getvalue())["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
