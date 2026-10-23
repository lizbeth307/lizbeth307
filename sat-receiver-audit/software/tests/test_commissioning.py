"""Synthetic acceptance exists only in a TemporaryDirectory for validator tests."""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zlib

from srrx.commissioning import (BRANCH_CAPS, CAL_FIELDS, GATE_IDS, RUNTIME_SOURCES,
                                ValidationError, acceptance_template, load_acceptance)
from srrx.provision import provision

PICO_CALIBRATION = Path(__file__).resolve().parents[2] / "firmware/pico/calibration.py"


class ClockBehind(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2025, 6, 1, tzinfo=timezone.utc)


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("design", "software/srrx", "firmware/pico", "firmware/imu", "measurements", "deployment"):
            (self.root / directory).mkdir(parents=True)
        for i in range(1, 6):
            (self.root / f"design/E{i}.json").write_text('{"test_fixture":true}')
        (self.root / "design/readiness-contract.json").write_text(json.dumps({"gate_results": dict.fromkeys(GATE_IDS, "OPEN")}))
        for filename in ("software/srrx/model.py", "firmware/pico/main.py", "firmware/imu/main.py"):
            (self.root / filename).write_text("# synthetic fixture source\n")
        shutil.copyfile(PICO_CALIBRATION, self.root / "firmware/pico/calibration.py")  # provision validator
        (self.root / "deployment/guard.sh").write_text("# synthetic deployment guard fixture\n")
        (self.root / "measurements/bench.log").write_text("Synthetic validator fixture: not a hardware measurement.\n")
        self.manifest = acceptance_template(self.root)
        self.path = self.root / "acceptance.json"

    def artifact(self, name):
        return {"path": name, "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}

    def evidence(self):
        return {"date": "2026-01-02T12:00:00Z", "instrument": "DMM-FIXTURE-42",
                "notes": "Synthetic validator fixture; never valid bench evidence.",
                "artifacts": [self.artifact("measurements/bench.log")]}

    def complete_fixture(self):
        data = self.manifest
        data.update(hardware_unit_id="FIXTURE-0042", pico_serial="e6616407e35b8d29",
                    accepted_at="2026-01-03T12:00:00Z")
        data["lab5_budget"] = {"always_on_a": .6, "max_lab5_a": 3.2, "evidence": self.evidence()}
        for gate in data["gates"].values():
            gate.update(status="PASS", evidence=self.evidence())
        record = {"v": 1, "revision": "E3-v2.1", "serial": data["pico_serial"],
                  "scale_nv_per_count": 280000, "offset_uv": 0,
                  "panel_offset_mc": 0, "case_offset_mc": 0,
                  "reference_id": "DMM-FIXTURE-42"}
        values = []
        for key in CAL_FIELDS:
            value = record[key]
            values.append(key + "=" + (str(value) if type(value) is int else value))
        record["crc32"] = "%08x" % (zlib.crc32(("\n".join(values) + "\n").encode()) & 0xffffffff)
        data["battery_adc"] = {"status": "PASS", "record": record, "evidence": self.evidence(),
            "points": [{"raw_count": 40000, "reference_v": 11.2}, {"raw_count": 50000, "reference_v": 14.0}]}
        for role, firmware in data["firmware"].items():
            firmware.update(status="PASS", artifact=self.artifact(f"firmware/{role}/main.py"), evidence=self.evidence())
        for branch, (cap, vcap) in BRANCH_CAPS.items():
            data["branch_limits"][branch] = {"baseline_a": cap / 2, "max_current_a": cap / 2 * 1.1,
                "min_voltage_v": vcap * .8, "max_voltage_v": vcap * .9, "evidence": self.evidence(),
                "calibration": {"status": "PASS", "unit_id": data["hardware_unit_id"],
                    "source": RUNTIME_SOURCES.get(branch, "bench_only_no_runtime_sensor"), "units": "SI",
                    "current_gain": 1.0, "current_offset_a": 0.0, "voltage_gain": 1.0, "voltage_offset_v": 0.0}}
        return data

    def save(self, data=None):
        self.path.write_text(json.dumps(self.manifest if data is None else data))

    def test_template_never_manufactures_pass_or_coefficients(self):
        self.assertEqual(len(self.manifest["gates"]), 36)
        self.assertTrue(all(g["status"] == "OPEN" for g in self.manifest["gates"].values()))
        self.assertEqual(self.manifest["battery_adc"]["record"], {})
        self.save()
        with self.assertRaises(ValidationError):
            load_acceptance(self.path, self.root)
        with self.assertRaises(ValidationError):
            load_acceptance(None, self.root)

    def test_complete_synthetic_fixture_round_trip(self):
        self.complete_fixture()
        self.save()
        self.assertEqual(load_acceptance(self.path, self.root)["hardware_unit_id"], "FIXTURE-0042")
        # The checked-in readiness contract stays OPEN, independent of the unit.
        self.assertEqual(json.loads((self.root / "design/readiness-contract.json").read_text())["gate_results"]["E1-01"], "OPEN")

    def test_fake_pass_without_measurement_evidence_rejected(self):
        self.complete_fixture()
        for change in (lambda d: d["gates"]["E1-01"].update(evidence={}),
                       lambda d: d["gates"]["E1-02"]["evidence"].update(notes="All passed"),
                       lambda d: d["gates"]["E2-01"]["evidence"].update(instrument="TBD"),
                       lambda d: d["gates"]["E3-01"]["evidence"].update(artifacts=[]),
                       lambda d: d.update(hardware_unit_id="example"),
                       lambda d: d["gates"].pop("E5-09")):
            with self.subTest(change=change):
                data = copy.deepcopy(self.manifest)
                change(data)
                self.save(data)
                with self.assertRaises(ValidationError):
                    load_acceptance(self.path, self.root)

    def test_graph_source_and_evidence_changes_revoke_acceptance(self):
        self.complete_fixture()
        self.save()
        for filename in ("design/E1.json", "software/srrx/model.py", "firmware/imu/main.py", "deployment/guard.sh", "measurements/bench.log"):
            with self.subTest(filename=filename):
                path = self.root / filename
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaises(ValidationError):
                    load_acceptance(self.path, self.root)
                path.write_bytes(original)

    def test_adc_not_nominal_or_wrong_unit_or_fake_points(self):
        self.complete_fixture()
        for change in (lambda d: d["battery_adc"].update(status="OPEN"),
                       lambda d: d["battery_adc"]["record"].update(serial="e661000000000000"),
                       lambda d: d["battery_adc"]["record"].update(scale_nv_per_count=300000),
                       lambda d: d["battery_adc"]["record"].update(scale_nv_per_count=280000.0),
                       lambda d: d["battery_adc"]["record"].update(offset_uv=False),
                       lambda d: d["battery_adc"]["record"].update(scale_mv_per_count=.28),
                       lambda d: d["battery_adc"]["points"][0].update(reference_v=12.0),
                       lambda d: d["battery_adc"]["points"][1].update(raw_count=True)):
            data = copy.deepcopy(self.manifest)
            change(data)
            self.save(data)
            with self.assertRaises(ValidationError):
                load_acceptance(self.path, self.root)

    def test_branch_limit_caps_unit_source_finite_and_baseline(self):
        self.complete_fixture()
        for change in (lambda d: d["branch_limits"]["LNA1"].update(max_current_a=.26),
                       lambda d: d["branch_limits"]["BONI"].update(baseline_a=.01),
                       lambda d: d["branch_limits"]["LNB"].update(max_current_a=float("nan")),
                       lambda d: d["branch_limits"]["LNA2"]["calibration"].update(source="INA3221:0x43:3"),
                       lambda d: d["branch_limits"]["LNA2"]["calibration"].update(unit_id="OTHER-UNIT")):
            data = copy.deepcopy(self.manifest)
            change(data)
            self.save(data)
            with self.assertRaises(ValidationError):
                load_acceptance(self.path, self.root)

    def test_unknown_keys_duplicate_keys_traversal_and_future_dates(self):
        self.complete_fixture()
        for change in (lambda d: d.update(force=True),
                       lambda d: d.update(accepted_at="2099-01-01T00:00:00Z"),
                       lambda d: d["firmware"]["pico"]["artifact"].update(path="../outside.py"),
                       lambda d: d["firmware"]["pico"].update(status="OPEN")):
            data = copy.deepcopy(self.manifest)
            change(data)
            self.save(data)
            with self.assertRaises(ValidationError):
                load_acceptance(self.path, self.root)
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ValidationError):
            load_acceptance(self.path, self.root)

    def test_clock_behind_acceptance_is_distinct_and_runtime_tolerant(self):
        self.complete_fixture()
        self.save()
        with patch("srrx.commissioning.datetime", ClockBehind):
            with self.assertRaisesRegex(ValidationError, "system clock"):
                load_acceptance(self.path, self.root)
            self.assertEqual(load_acceptance(self.path, self.root, clock_check=False)["hardware_unit_id"], "FIXTURE-0042")
            # Only the wall-clock bound is relaxed; floor and ordering still apply.
            for change in (lambda d: d.update(accepted_at="2025-12-31T00:00:00Z"),
                           lambda d: d["gates"]["E1-01"]["evidence"].update(date="2026-01-04T00:00:00Z")):
                data = copy.deepcopy(self.manifest)
                change(data)
                self.save(data)
                with self.assertRaises(ValidationError):
                    load_acceptance(self.path, self.root, clock_check=False)

    def pico(self):
        spec = importlib.util.spec_from_file_location("srrx_test_pico_calibration", PICO_CALIBRATION)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_provision_binds_exactly_the_validated_bytes(self):
        self.complete_fixture()
        self.save()
        original = self.path.read_bytes()

        def concurrent_rewrite(*args, **kwargs):
            result = load_acceptance(*args, **kwargs)
            self.path.write_bytes(original.replace(b"FIXTURE-0042", b"FIXTURE-0043"))
            return result
        output = self.root / "provisioned"
        with patch("srrx.provision.load_acceptance", side_effect=concurrent_rewrite):
            summary = provision(self.path, self.root, output)
        digest = hashlib.sha256(original).hexdigest()
        cal = json.loads((output / "calibration.json").read_text())
        record = json.loads((output / "commissioning.json").read_text())
        self.assertEqual((summary["acceptance_sha256"], record["qualification_record"]), (digest, digest))
        pico = self.pico()
        pico.validate(cal, "e6616407e35b8d29")
        self.assertTrue(pico.commissioning_valid(record, cal, "e6616407e35b8d29"))
        self.assertEqual(sorted(p.name for p in output.iterdir()), ["calibration.json", "commissioning.json"])

    def test_provision_failure_keeps_previous_pair(self):
        self.complete_fixture()
        self.save()
        output = self.root / "provisioned"
        output.mkdir()
        for name in ("calibration.json", "commissioning.json"):
            (output / name).write_text("previous " + name)
        with patch("srrx.provision.os.fsync", side_effect=[None, OSError(28, "No space left on device")]):
            with self.assertRaises(OSError):
                provision(self.path, self.root, output)
        self.assertEqual({p.name: p.read_text() for p in output.iterdir()},
                         {name: "previous " + name for name in ("calibration.json", "commissioning.json")})

    def test_lab5_budget_requires_measured_evidence_and_bound(self):
        self.complete_fixture()
        for change in (lambda d: d["lab5_budget"].update(always_on_a=0),
                       lambda d: d["lab5_budget"].update(max_lab5_a=4),
                       lambda d: d["lab5_budget"].update(always_on_a=2.5, max_lab5_a=2.55),
                       lambda d: d["lab5_budget"].update(evidence={})):
            data = copy.deepcopy(self.manifest)
            change(data)
            self.save(data)
            with self.assertRaises(ValidationError):
                load_acceptance(self.path, self.root)


if __name__ == "__main__":
    unittest.main()
