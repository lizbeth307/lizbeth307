"""labd's attended LRPT pass scheduling (srrx.baseband_scheduler) and its verified-UTC source.

Host tests only: systemctl, the units, the store and SatDump are fakes; the decode step runs the real
satdump_pass.prepare_decode/finish_decode with srrx.satdump_unit.decode playing the unit. No pass,
no receiver and no Q6A timing is evidenced here (W-04/W-05 and the bench rows stay OPEN).
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zlib

from srrx import baseband as bb
from srrx import baseband_scheduler as bs
from srrx import decoder_policy, location, pass_jobs, passes, satdump_pass as sp
from srrx.engine import Engine, UTC_STALE_MS
from srrx.hardware import SimHardware
from srrx.link import SimLink
from srrx.scope_policy import ScopeLatch

ROOT = Path(__file__).resolve().parents[2]
START = 1_800_000_000.0
METEOR3, NOAA = 40001, 40003
ACCEPTED = {METEOR3: {"norad_id": METEOR3, "name": "Meteor-M N2-3", "role": "LRPT"},
            NOAA: {"norad_id": NOAA, "name": "NOAA 19", "role": "OTHER"}}
AOS = START + 3600
LOS = AOS + 720
OWNER = "uid:1000"


def text(moment):
    return datetime.fromtimestamp(moment, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def plan(verified=True):
    items = []
    for norad, name, aos in ((METEOR3, "Meteor-M N2-3", AOS), (NOAA, "NOAA 19", AOS + 3000)):
        items.append({"norad_id": norad, "name": name, "aos_utc": text(aos), "tca_utc": text(aos + 300),
                      "los_utc": text(aos + 720), "max_el_deg": 40.0, "aos_az_deg": 10.0, "tca_az_deg": 80.0,
                      "los_az_deg": 170.0, "duration_s": 720.0, "omm_epoch_utc": "2027-01-15T00:00:00.000000Z",
                      "omm_age_days": 0.2, "omm_age_warning": False, "time_verified": verified,
                      "observer_source": "last_good", "observer_age_ms": None, "v_dipole_hint": None,
                      "predictor": {"skyfield": "1.55", "sgp4": "2.27"}})
    return {"schema_version": 1, "kind": "srrx_pass_plan", "start_utc": text(START), "hours": 24.0, "min_el_deg": 0.0,
            "time_verified": verified,
            "observer": {"lat_rounded": 50.0, "lon_rounded": 10.0, "alt_rounded_m": 200.0, "rounding_deg": 0.1,
                         "source": "last_good", "age_ms": None, "qualified_fix": False,
                         "qualification_failures": ["NOT_A_GNSS_FIX"]},
            "predictor": {"skyfield": "1.55", "sgp4": "2.27"}, "passes": items, "skipped": [],
            "window_edge_partial_passes": 0, "truncated": False, "scope": passes.SCOPE}


def png():
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x80")) + chunk(b"IEND", b""))


class Planner:
    def __init__(self, value):
        self.value = value

    def current_plan(self):
        return None if self.value is None else {"plan": self.value, "request_id": "0123456789abcdef"}


class Systemctl:
    """Records every call in order; show() answers the configured ActiveState."""

    def __init__(self):
        self.calls, self.state, self.start_code = [], {}, 0

    def start(self, unit):
        self.calls.append(("start", unit))
        if self.start_code == 0:
            self.state[unit] = "activating"
        return self.start_code

    def stop(self, unit):
        self.calls.append(("stop", unit))
        self.state[unit] = "inactive"
        return 0

    def show(self, unit):
        self.calls.append(("show", unit))
        return {"ActiveState": self.state.get(unit, "inactive"), "SubState": "x", "exit": 0}


class Store:
    def __init__(self, events, meta=None):
        self.events, self.meta = events, meta

    def load(self, recording_id):
        self.events.append(("load", recording_id))
        return self.meta, (1, 2, 16)

    def identity(self, recording_id):
        return (1, 2, 16)

    def delete(self, recording_id):
        self.events.append(("delete", recording_id))
        return True

    def sweep(self):
        self.events.append(("sweep",))
        return {"deleted": 0}

    def data_path(self, recording_id):
        return "/data/raw/baseband-lrpt/" + recording_id + ".sigmf-data"


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


@unittest.skipUnless(os.name == "posix", "job directories (0700, euid) and the setgid work tree need POSIX")
class SchedulerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-sched-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.products = self.root / sp.PRODUCTS_DIR
        self.products.mkdir(parents=True)
        self.jobs = self.root / "run-satdump"
        patcher = mock.patch.object(sp, "DATA_ROOT", str(self.root))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.events, self.threads, self.utc = [], [], [True]
        self.systemctl = Systemctl()
        self.clock = Clock(AOS - 600)
        self.scope = ScopeLatch()
        self.lease = {"owner": OWNER, "valid": True, "armed": True, "rtla_on": True}
        self.store_opened = []
        self.scheduler = self.make()

    def make(self, **overrides):
        def store_factory(device):
            self.store_opened.append(device)
            return self.store, lambda: self.events.append(("close",))
        options = dict(planner=Planner(plan()), utc_verified=lambda: self.utc[0], systemctl=self.systemctl,
                       accepted_loader=lambda: ACCEPTED,
                       binding_loader=lambda: ("/dev/disk/by-uuid/0000-TEST", "/opt/srrx/evidence/rtla.json"),
                       installation_check=lambda: None, installation_loader=lambda: {"sha256": "c" * 64},
                       store_factory=store_factory, scope=self.scope, wall_clock=self.clock,
                       start_thread=lambda target: self.threads.append(target), job_root=self.jobs,
                       products_root=self.products)
        options.update(overrides)
        self.store = Store(self.events)
        return bs.BasebandScheduler(**options)

    def request(self, **change):
        value = dict({"aos_utc": text(AOS), "center_hz": 137_900_000, "symbol_rate": 72_000}, **change)
        return self.scheduler.request(value, OWNER, 0)

    def step(self, seconds=None, ticks=1, now_ms=None):
        """Advance the wall clock, tick and run the queued worker operations, ticks times."""
        if seconds is not None:
            self.clock.now = seconds
        for unused in range(ticks):
            self.now_ms = (getattr(self, "now_ms", 0) + 2500) if now_ms is None else now_ms
            self.scheduler.tick(self.now_ms, self.lease)
            self.scheduler.drain()

    def record_unit(self, job_id):
        return "srrx-baseband-record@" + job_id + ".service"

    def write_record_result(self, job_id, status="RECORDED", reason=None, recording_id="lrpt-" + "a" * 16):
        if status == "RECORDED":
            value = sp.result_value("record", job_id, "RECORDED", recording_id=recording_id, stop_reason="WINDOW_END",
                                    samples=1000, branch_off_confirmed=True)
        else:
            value = sp.result_value("record", job_id, status, reason)
        sp._write_new(self.jobs / job_id / sp.RESULT_FILE, value, 0o640)

    def start_recording(self):
        self.clock.now = AOS - 600
        accepted = self.request()
        self.assertTrue(accepted["ok"], accepted)
        job_id = accepted["job_id"]
        window = self.scheduler._job["window"]
        self.step(window["start_unix_s"] - bb.EARLY_START_S - 1)
        self.assertEqual(self.systemctl.calls, [])  # not before AOS-60 s - EARLY_START_S
        self.step(window["start_unix_s"] - bb.EARLY_START_S)
        self.assertEqual(self.systemctl.calls, [("start", self.record_unit(job_id))])
        self.systemctl.state[self.record_unit(job_id)] = "active"
        self.step()  # poll: running
        self.assertEqual(self.scheduler.status()["state"], "RECORDING")
        return job_id, window

    # ------------------------------------------------------------ refusals at the request

    def test_request_refuses_without_verified_utc_a_plan_or_a_future_meteor_pass(self):
        self.utc[0] = False
        self.assertEqual(self.request(), {"ok": False, "error": "UTC_NOT_VERIFIED"})
        self.utc[0] = True
        self.scheduler = self.make(planner=Planner(None))
        self.assertEqual(self.request()["error"], "NO_PLAN")
        self.scheduler = self.make(planner=Planner(plan(verified=False)))
        self.assertEqual(self.request()["error"], "UTC_NOT_VERIFIED")  # the plan's own UTC state (select_windows)
        self.scheduler = self.make()
        self.assertEqual(self.request(aos_utc=text(AOS + 3000))["error"], "BASEBAND_NO_SUCH_PASS")  # NOAA: no window
        self.assertEqual(self.request(center_hz=137_500_000)["error"], "LRPT_CENTER_NOT_ALLOWED")
        self.assertEqual(self.scheduler.request({"aos_utc": text(AOS)}, OWNER, 0)["error"], "BASEBAND_BAD_REQUEST")
        self.clock.now = AOS - 60 - bb.EARLY_START_S
        self.assertEqual(self.request()["error"], "BASEBAND_WINDOW_STARTED")
        self.clock.now = AOS - 600

        def unbound():
            raise bs.SchedulerRefused("BASEBAND_STORAGE_UNBOUND")
        self.scheduler = self.make(binding_loader=unbound)
        self.assertEqual(self.request()["error"], "BASEBAND_STORAGE_UNBOUND")
        self.assertEqual(self.systemctl.calls, [])

    def test_one_job_at_a_time_and_one_worker(self):
        first = self.request()
        self.assertTrue(first["ok"])
        self.assertTrue(first["job_id"].startswith("lrpt-") and sp.INSTANCE.match(first["job_id"]))
        self.assertEqual(self.request(), {"ok": False, "error": "BASEBAND_BUSY"})
        job_id, unused = first["job_id"], None
        window = self.scheduler._job["window"]
        self.step(window["start_unix_s"] - bb.EARLY_START_S)
        self.systemctl.state[self.record_unit(job_id)] = "active"
        self.step(ticks=3)
        self.assertEqual(len(self.threads), 1)  # every systemctl call goes through the one worker queue
        status = json.dumps(self.scheduler.status())
        for private in (str(self.root), "/run/", "/data", "lat", "lon"):
            self.assertNotIn(private, status)

    # ------------------------------------------------------------ recording

    def test_record_job_carries_only_the_window_and_starts_with_held_lease_and_utc(self):
        seen = {}
        start = self.systemctl.start

        def spy(unit):
            job_id = unit.split("@", 1)[1][:-len(".service")]
            path = self.jobs / job_id / sp.JOB_FILE
            seen["job"] = json.loads(path.read_text())
            seen["mode"] = os.stat(path).st_mode & 0o777
            return start(unit)
        self.systemctl.start = spy
        job_id, window = self.start_recording()
        self.assertEqual(seen["mode"], 0o600)
        self.assertEqual(set(seen["job"]), {"v", "kind", "instance", "window"})
        self.assertEqual(seen["job"]["window"], window)
        self.assertEqual(sp.check_record_job(seen["job"], job_id)["window"], window)
        import re
        self.assertRegex(self.record_unit(job_id), re.compile(bs.UNIT_PATTERN))

    def test_no_recording_without_utc_lease_arm_or_rtla_at_the_window_start(self):
        for change, reason in (({}, "UTC_NOT_VERIFIED"), ({"valid": False}, "LEASE_NOT_HELD"),
                               ({"owner": "uid:2000"}, "LEASE_NOT_HELD"), ({"armed": False}, "DISARMED"),
                               ({"rtla_on": False}, "RTLA_OFF")):
            with self.subTest(reason=reason):
                self.systemctl.calls.clear()
                self.utc[0] = True
                self.clock.now = AOS - 600
                self.scheduler = self.make()
                self.lease = dict({"owner": OWNER, "valid": True, "armed": True, "rtla_on": True}, **change)
                window = None
                self.assertTrue(self.request()["ok"])
                window = self.scheduler._job["window"]
                if reason == "UTC_NOT_VERIFIED":
                    self.utc[0] = False
                self.step(window["start_unix_s"] - bb.EARLY_START_S)
                self.assertEqual(self.systemctl.calls, [])
                self.assertEqual(self.scheduler.status()["last"]["error"], reason)
                self.assertEqual(self.scheduler.status()["state"], "IDLE")

    def test_lease_loss_stops_the_record_unit_and_sweeps_the_partial_file(self):
        job_id, window = self.start_recording()
        self.lease = dict(self.lease, valid=False)
        self.step()
        self.assertIn(("stop", self.record_unit(job_id)), self.systemctl.calls)
        self.step(ticks=3)
        self.assertEqual(self.scheduler.status()["last"]["error"], "LEASE_LOST")
        self.assertIn(("sweep",), self.events)  # incomplete files go (labrx deleted its partial on SIGTERM)
        self.assertFalse((self.jobs / job_id).exists())
        self.assertNotIn("start", [c[0] for c in self.systemctl.calls if "decode" in c[1]])

    def test_utc_loss_disarm_and_rtla_off_stop_the_recording_too(self):
        for change, reason in (("utc", "UTC_NOT_VERIFIED"), ({"armed": False}, "DISARMED"), ({"rtla_on": False}, "RTLA_OFF")):
            with self.subTest(reason=reason):
                self.systemctl.calls.clear()
                self.utc[0] = True
                self.lease = {"owner": OWNER, "valid": True, "armed": True, "rtla_on": True}
                self.scheduler = self.make()
                job_id, unused = self.start_recording()
                if change == "utc":
                    self.utc[0] = False
                else:
                    self.lease = dict(self.lease, **change)
                self.step(ticks=4)
                self.assertIn(("stop", self.record_unit(job_id)), self.systemctl.calls)
                self.assertEqual(self.scheduler.status()["last"]["error"], reason)

    def test_scope_stop_stops_the_recording_and_discards_it(self):
        job_id, window = self.start_recording()
        self.scope.stop(*bb.channel_span(137_900_000, 72_000))  # an operator or identification stop latches the span
        self.step()
        self.assertIn(("stop", self.record_unit(job_id)), self.systemctl.calls)
        self.step(ticks=3)
        self.assertEqual(self.scheduler.status()["last"]["error"], "OUT_OF_SCOPE")
        self.assertIn(("sweep",), self.events)
        # A finished recording that arrives after a scope stop is deleted, never decoded.
        self.scope = ScopeLatch()
        self.scheduler = self.make()
        self.events.clear()
        self.systemctl.calls.clear()
        job_id, window = self.start_recording()
        self.scheduler.cancel("uid:3000", 0, scope_stop=True)  # any local operator may stop
        self.write_record_result(job_id)
        self.step(ticks=4)
        self.assertEqual(self.scheduler.status()["last"]["error"], "CANCELLED")
        self.assertIn(("delete", "lrpt-" + "a" * 16), self.events)
        self.assertFalse(any("decode" in unit for unused, unit in self.systemctl.calls))

    def test_record_unit_that_ends_without_result_or_never_starts_fails_closed(self):
        job_id, window = self.start_recording()
        self.systemctl.state[self.record_unit(job_id)] = "failed"
        self.step(ticks=4)
        self.assertEqual(self.scheduler.status()["last"]["error"], "RECORD_UNIT_NO_RESULT")
        self.scheduler = self.make()
        self.systemctl.start_code = 4  # polkit refused, or the template is missing
        self.clock.now = AOS - 600
        self.assertTrue(self.request()["ok"])
        self.step(self.scheduler._job["window"]["start_unix_s"] - bb.EARLY_START_S)
        self.assertEqual(self.scheduler.status()["last"]["error"], "RECORD_UNIT_START_FAILED")
        self.assertEqual(list(self.jobs.iterdir()), [])

    # ------------------------------------------------------------ decode

    def run_to_decode(self):
        job_id, window = self.start_recording()
        self.write_record_result(job_id)
        self.step(ticks=2)  # the poll reads the result, the next tick acts on it
        self.assertEqual(self.scheduler.status()["state"], "DECODE_WAIT")
        return job_id, window

    def test_decode_starts_only_after_los_plus_60_s(self):
        job_id, window = self.run_to_decode()
        self.step(LOS + bb.MARGIN_S - 1, ticks=2)
        self.assertFalse(any("decode" in unit for unused, unit in self.systemctl.calls))
        self.assertEqual(self.scheduler.status()["state"], "DECODE_WAIT")
        rid = "lrpt-" + "a" * 16
        with mock.patch.object(sp, "prepare_decode", return_value={"recording_id": rid, "unit": sp.unit_name(
                sp.DECODE_TEMPLATE, rid), "work": self.products / (".satdump-" + rid)}) as prepare:
            self.step(LOS + bb.MARGIN_S)
        prepare.assert_called_once()
        self.assertIn(("start", "srrx-satdump-decode@" + rid + ".service"), self.systemctl.calls)
        self.assertEqual(self.scheduler.status()["state"], "DECODING")
        # A lease lost after the window does not touch a file decode: it needs no receiver.
        self.lease = dict(self.lease, valid=False)
        self.step()
        self.assertEqual(self.scheduler.status()["state"], "DECODING")

    def test_decode_reads_the_pngs_deletes_the_baseband_before_publishing_and_removes_the_tree(self):
        from srrx import satdump_unit
        job_id, window = self.run_to_decode()
        rid = "lrpt-" + "a" * 16
        meta_window = bb.validate_window(window)
        self.store.meta = bb.metadata(rid, meta_window, created_s=AOS - 60, first_block_s=AOS - 60, samples=4,
                                      sha512="b" * 128, clipped=0, gaps=0, joins=0, source="SIMULATION",
                                      group_delay=685, stop_reason="WINDOW_END")
        order = self.events
        publish = decoder_policy.satdump_publish

        def published(source, target, plan_value, **kwargs):
            order.append(("publish", sorted(p.name for p in Path(source).rglob("*.png"))))
            self.assertTrue(Path(source).is_dir())  # the PNGs are read from the work tree, which still exists
            return publish(source, target, plan_value, **kwargs)
        start = self.systemctl.start

        def decode_unit(unit):
            code = start(unit)
            if "decode" in unit:  # the unit itself: srrx.satdump_unit.decode with SatDump faked
                credentials = self.root / "credentials"
                credentials.mkdir()
                shutil.copyfile(self.jobs / rid / sp.JOB_FILE, credentials / "job")

                def run(argv, timeout_s, env=None, cwd=None):
                    if argv[-1] == "--help":
                        return 0, b"level input_file output_folder --samplerate --baseband_format"
                    out = Path(argv[5])
                    out.mkdir(parents=True)
                    (out / "rgb.png").write_bytes(png())
                    return 0, b"ok"
                value = satdump_unit.decode(rid, environ={"CREDENTIALS_DIRECTORY": str(credentials),
                                                          "HOME": "/run/srrx-satdump-" + rid}, runner=run,
                                            load_installation=lambda path: {"sha256": "c" * 64},
                                            executable_check=lambda installation: Path("/usr/bin/satdump"))
                sp._write_new(self.products / (".satdump-" + rid) / sp.UNIT_RESULT, value, 0o640)
                self.systemctl.state[unit] = "inactive"
            return code
        self.systemctl.start = decode_unit
        with mock.patch.object(decoder_policy, "_validate_satdump_installation", return_value=Path("/usr/bin/satdump")), \
                mock.patch.object(decoder_policy, "satdump_publish", published):
            self.step(LOS + bb.MARGIN_S, ticks=4)
        status = self.scheduler.status()
        self.assertEqual((status["state"], status["last"]["state"], status["last"]["error"]), ("IDLE", "DONE", None))
        self.assertEqual(status["last"]["products"], 1)
        kinds = [event[0] for event in order if event[0] in ("load", "delete", "publish")]
        self.assertEqual(kinds, ["load", "delete", "publish"])  # baseband deleted before the products appear
        self.assertEqual(sorted(p.name for p in self.products.iterdir()), [rid])  # work tree removed
        self.assertEqual(sorted(p.name for p in (self.products / rid).iterdir()), ["image-00.png", "report.json"])
        self.assertEqual(list(self.jobs.iterdir()), [])

    def test_a_refused_decode_still_deletes_the_baseband(self):
        job_id, window = self.run_to_decode()
        rid = "lrpt-" + "a" * 16
        with mock.patch.object(sp, "prepare_decode", side_effect=decoder_policy.DecoderRefused("SOURCE_NOT_APPROVED_LRPT_BASEBAND")):
            self.step(LOS + bb.MARGIN_S)
        self.assertEqual(self.scheduler.status()["last"]["error"], "SOURCE_NOT_APPROVED_LRPT_BASEBAND")
        self.assertIn(("delete", rid), self.events)
        self.assertFalse(any("decode" in unit for unused, unit in self.systemctl.calls))

    def test_cancel_while_waiting_for_the_decode_deletes_the_recording(self):
        job_id, window = self.run_to_decode()
        self.assertEqual(self.scheduler.cancel(OWNER, 0)["ok"], True)
        self.step(ticks=2)
        self.assertEqual(self.scheduler.status()["last"]["state"], "CANCELLED")
        self.assertIn(("delete", "lrpt-" + "a" * 16), self.events)
        self.assertEqual(self.scheduler.cancel(OWNER, 0), {"ok": False, "error": "BASEBAND_IDLE"})


class StagedTextTests(unittest.TestCase):
    def test_polkit_rule_allows_labd_start_and_stop_of_the_two_templates_only(self):
        import re
        rule = bs.polkit_rule()
        self.assertEqual(rule.count("polkit.addRule("), 1)
        self.assertEqual(rule.count("polkit.Result.YES"), 1)
        for needle in ('"org.freedesktop.systemd1.manage-units"', 'subject.user == "labd"', 'action.lookup("verb") == "start"',
                       'action.lookup("verb") == "stop"', "/" + bs.UNIT_PATTERN + "/.test(action.lookup(\"unit\"))"):
            self.assertIn(needle, rule)
        for word in ("restart", "reload", "Result.AUTH", "Result.NO", "isInGroup"):
            self.assertNotIn(word, rule)
        pattern = re.compile(bs.UNIT_PATTERN)
        for name in ("srrx-satdump-decode@lrpt-0123456789abcdef.service", "srrx-baseband-record@lrpt-0123456789abcdef.service"):
            self.assertTrue(pattern.match(name), name)
        for name in ("srrx-satdump-decode@.service", "srrx-satdump-decode@lrpt-0123456789ABCDEF.service", "srrx.service",
                     "srrx-satdump-live@lrpt-0123456789abcdef.service", "run-u1.service"):
            self.assertFalse(pattern.match(name), name)
        self.assertEqual(set(bs.staged_files()), {bs.POLKIT_RULE, bs.LABD_DROPIN})

    def test_labd_dropin_adds_only_the_satdump_group_and_the_data_mount(self):
        lines = [l for l in bs.labd_dropin().splitlines() if l and not l.startswith("#")]
        self.assertEqual(lines, ["[Service]", "SupplementaryGroups=srrx-satdump", "ReadWritePaths=-/data"])
        service = (ROOT / "software/systemd/srrx.service").read_text()
        self.assertNotIn("srrx-satdump", service)  # the guest's units stay as they are (guest_smoke)
        self.assertIn("TasksMax=8\n", service)  # unchanged: one worker thread and one systemctl child

    def test_storage_binding_is_strict(self):
        def reader(text):
            return lambda path, limit: None if text is None else text.encode()
        good = "# c\nSRRX_BB_DEVICE=/dev/disk/by-uuid/1234-ABCD\nSRRX_BB_DRIVER_RECORD=/opt/srrx/evidence/rtla.json\n"
        self.assertEqual(bs.load_binding(reader=reader(good)),
                         ("/dev/disk/by-uuid/1234-ABCD", "/opt/srrx/evidence/rtla.json"))
        for bad, code in ((None, "BASEBAND_STORAGE_UNBOUND"), ("SRRX_BB_DEVICE=\n", "BASEBAND_STORAGE_UNBOUND"),
                          (good.replace("by-uuid/1234-ABCD", "sda1"), "BASEBAND_STORAGE_UNBOUND"),
                          (good + "SRRX_BB_DEVICE=/dev/disk/by-uuid/x\n", "BASEBAND_STORAGE_UNBOUND"),
                          (good.replace("/opt/srrx/evidence/rtla.json", ""), "RTLA_DRIVER_RECORD_UNBOUND"),
                          (good.replace("/opt/srrx/evidence/rtla.json", "/tmp/x.json"), "RTLA_DRIVER_RECORD_UNBOUND"),
                          (good.replace("evidence/rtla.json", "../etc/x.json"), "RTLA_DRIVER_RECORD_UNBOUND")):
            with self.subTest(bad=bad), self.assertRaisesRegex(bs.SchedulerRefused, code):
                bs.load_binding(reader=reader(bad))

    def test_record_and_decode_results_have_a_fixed_schema(self):
        job = "lrpt-" + "1" * 16
        good = sp.result_value("record", job, "RECORDED", recording_id="lrpt-" + "2" * 16, stop_reason="WINDOW_END",
                               samples=10, branch_off_confirmed=None)
        self.assertEqual(sp.check_result(dict(good), "record", job), good)
        for change in ({"recording_id": None}, {"samples": 0}, {"stop_reason": "x"}, {"reason": "X"}, {"instance": "lrpt-" + "3" * 16},
                       {"extra": 1}, {"status": "REFUSED"}):
            with self.subTest(change=change), self.assertRaises(sp.PassRefused):
                sp.check_result(dict(good, **change), "record", job)
        refused = sp.result_value("decode", job, "REFUSED", "SATDUMP_CALCEPH_ERROR")
        self.assertEqual(refused["reason"], "SATDUMP_CALCEPH_ERROR")
        for reason in (None, "a path /etc/passwd", "x" * 80):
            with self.subTest(reason=reason), self.assertRaises(sp.PassRefused):
                sp.check_result(dict(refused, reason=reason), "decode", job)


class RecordUnitTests(unittest.TestCase):
    """srrx.satdump_unit record inside its unit, with labrx.run_baseband replaced."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-unit-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.job = "lrpt-" + "4" * 16
        window = sp.select_windows(plan(), ACCEPTED, 137_900_000, 72_000)["windows"][0]
        self.window = window
        (self.root / "job").write_text(json.dumps(sp.record_job(self.job, window)))
        self.environ = {"CREDENTIALS_DIRECTORY": str(self.root), "SRRX_BB_DEVICE": "/dev/disk/by-uuid/1234",
                        "SRRX_BB_DRIVER_RECORD": "/opt/srrx/evidence/rtla.json"}

    def test_record_runs_the_job_window_and_reports_the_recording(self):
        from srrx import satdump_unit
        seen = []

        def recorder(window, device, driver):
            seen.append((window, device, driver))
            return {"recording_id": "lrpt-" + "5" * 16, "stop_reason": "WINDOW_END", "samples": 99,
                    "branch_off_confirmed": True}
        value = satdump_unit.record(self.job, environ=self.environ, recorder=recorder, clock=lambda: AOS)
        self.assertEqual(seen, [(self.window, "/dev/disk/by-uuid/1234", "/opt/srrx/evidence/rtla.json")])
        self.assertEqual((value["status"], value["recording_id"], value["samples"]), ("RECORDED", "lrpt-" + "5" * 16, 99))
        for change, code in (({"SRRX_BB_DEVICE": ""}, "BASEBAND_STORAGE_UNBOUND"),
                             ({"SRRX_BB_DRIVER_RECORD": ""}, "RTLA_DRIVER_RECORD_UNBOUND"),
                             ({"CREDENTIALS_DIRECTORY": ""}, "JOB_CREDENTIAL_MISSING")):
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, code):
                satdump_unit.record(self.job, environ=dict(self.environ, **change), recorder=recorder, clock=lambda: AOS)
        with self.assertRaisesRegex(ValueError, "WINDOW_OVER"):
            satdump_unit.record(self.job, environ=self.environ, recorder=recorder, clock=lambda: LOS + 600)
        with self.assertRaisesRegex(ValueError, "JOB_INVALID"):
            satdump_unit.record("lrpt-" + "6" * 16, environ=self.environ, recorder=recorder, clock=lambda: AOS)

    def test_refusal_codes_never_carry_text(self):
        from srrx import satdump_unit
        self.assertEqual(satdump_unit._code(ValueError("UTC_NOT_VERIFIED")), "UTC_NOT_VERIFIED")
        self.assertEqual(satdump_unit._code(RuntimeError("RX blocked: labd is not fresh")), "UNIT_RUNTIMEERROR")
        self.assertEqual(satdump_unit._code(KeyboardInterrupt(143)), "STOPPED_BY_SIGNAL")
        self.assertEqual(satdump_unit.main(["record", "lrpt-x"]), 2)


class GnssStatus:
    def __init__(self, **fields):
        self.fields = dict({"pps_gate_open": True, "jamming_active": False, "jamming_visible": True,
                            "reset_required": False}, **fields)

    def status(self):
        return dict(self.fields)

    def tick(self, now_ms, reset_status, pulse):
        pass


SYNCED = {"state": 0, "status": 0x2001, "maxerror_us": 1500, "esterror_us": 10}


class UtcVerifiedTests(unittest.TestCase):
    """labd's utc_verified: the GNSS orchestrator's PPS gate and the kernel clock, both required."""

    def test_verified_only_with_the_pps_gate_and_a_synchronized_clock(self):
        gate = GnssStatus().status()
        self.assertEqual(location.system_utc_verified(gate, SYNCED), (True, None))
        cases = ((None, SYNCED, "UTC_GNSS_OFF"),
                 (dict(gate, pps_gate_open=False), SYNCED, "UTC_PPS_GATE_CLOSED"),
                 (dict(gate, jamming_active=True), SYNCED, "UTC_JAMMING"),
                 (dict(gate, jamming_active=None), SYNCED, "UTC_JAMMING"),
                 (dict(gate, jamming_visible=False), SYNCED, "UTC_JAMMING_NOT_VISIBLE"),
                 (dict(gate, reset_required=True), SYNCED, "UTC_RESET_REQUIRED"),
                 (gate, None, "UTC_CLOCK_UNREADABLE"),
                 (gate, dict(SYNCED, status=None), "UTC_CLOCK_UNREADABLE"),
                 (gate, dict(SYNCED, state=location.TIME_ERROR), "UTC_CLOCK_UNSYNCHRONIZED"),
                 (gate, dict(SYNCED, status=SYNCED["status"] | location.STA_UNSYNC), "UTC_CLOCK_UNSYNCHRONIZED"),
                 (gate, dict(SYNCED, status=location.STA_CLOCKERR), "UTC_CLOCK_UNSYNCHRONIZED"),
                 (gate, dict(SYNCED, maxerror_us=location.UTC_MAX_ERROR_US + 1), "UTC_CLOCK_MAXERROR"),
                 (gate, dict(SYNCED, maxerror_us=16_000_000), "UTC_CLOCK_MAXERROR"))
        for gnss, clock, reason in cases:
            with self.subTest(reason=reason, gnss=gnss, clock=clock):
                self.assertEqual(location.system_utc_verified(gnss, clock), (False, reason))
                self.assertIn(reason, location.UTC_REASONS)

    def engine(self, gnss=None, clock=lambda: dict(SYNCED)):
        return Engine(SimHardware(), SimLink(ROOT), simulated=True, gnss=gnss, clock_reader=clock)

    def test_engine_publishes_utc_verified_in_status_for_labrx(self):
        engine = self.engine(GnssStatus())
        engine.tick(1000)
        status = engine.status()
        self.assertIs(status["utc_verified"], True)
        self.assertIsNone(status["utc_reason"])
        self.assertTrue(engine.utc_verified())
        # labrx reads exactly this field from its ControlGuard status (labrx.run_baseband).
        engine.gnss.fields["pps_gate_open"] = False
        engine.tick(1500)  # re-evaluated at most once a second
        self.assertTrue(engine.utc_verified())
        engine.tick(2000)
        self.assertEqual((engine.status()["utc_verified"], engine.status()["utc_reason"]), (False, "UTC_PPS_GATE_CLOSED"))
        # Without the source (labd --gnss off, simulation) and with a failing clock read: never verified.
        for engine, reason in ((self.engine(None), "UTC_GNSS_OFF"), (Engine(SimHardware(), SimLink(ROOT)), "UTC_SOURCE_MISSING"),
                               (self.engine(GnssStatus(), clock=lambda: (_ for _ in ()).throw(OSError("x"))),
                                "UTC_CLOCK_UNREADABLE")):
            with self.subTest(reason=reason):
                engine.tick(1000)
                self.assertEqual((engine.utc_verified(), engine.status()["utc_reason"]), (False, reason))

    def test_a_stale_evaluation_is_not_verified(self):
        engine = self.engine(GnssStatus())
        engine.tick(1000)
        self.assertTrue(engine.utc_verified())
        engine.request({"op": "status"}, 1000 + UTC_STALE_MS + 1)  # the loop stood still; a request moves the clock
        self.assertFalse(engine.utc_verified())
        self.assertEqual(engine.status()["utc_reason"], "UTC_STALE")

    def test_pass_planner_takes_the_engine_source(self):
        engine = self.engine(GnssStatus())
        engine.tick(1000)
        planner = pass_jobs.PassPlanner(utc_verified=engine.utc_verified)
        self.assertTrue(planner.utc_verified())
        engine.gnss.fields["jamming_active"] = True
        engine.tick(2100)
        self.assertFalse(planner.utc_verified())
        daemon_source = (ROOT / "software/srrx/daemon.py").read_text()
        self.assertIn("PassPlanner(utc_verified=engine.utc_verified)", daemon_source)
        self.assertIn("BasebandScheduler(planner=engine.passes, utc_verified=engine.utc_verified)", daemon_source)
        self.assertIn("clock_reader=kernel_clock", daemon_source)

    @unittest.skipUnless(sys.platform == "linux" and sys.maxsize > 2 ** 32, "adjtimex(2) of 64-bit Linux")
    def test_kernel_clock_reads_adjtimex_without_privilege(self):
        from srrx import daemon
        clock = daemon.kernel_clock()
        self.assertEqual(set(clock), {"state", "status", "maxerror_us", "esterror_us"})
        self.assertIn(clock["state"], range(0, 6))
        self.assertGreaterEqual(clock["maxerror_us"], 0)
        verified, reason = location.system_utc_verified(None, clock)
        self.assertEqual((verified, reason), (False, "UTC_GNSS_OFF"))  # a host clock alone never verifies

        class Libc:
            def adjtimex(self, pointer):
                return -1
        with self.assertRaises(OSError):
            daemon.kernel_clock(libc=Libc())

    def test_engine_ops_need_the_scheduler_and_the_callers_lease(self):
        engine = self.engine(GnssStatus())
        self.assertEqual(engine.request({"op": "baseband_schedule", "value": {}, "_owner": OWNER}, 0),
                         {"ok": False, "error": "BASEBAND_DISABLED"})
        self.assertEqual(engine.status()["baseband"], {"enabled": False, "state": "DISABLED"})
        calls = []

        class Scheduler:
            def request(self, value, owner, now_ms):
                calls.append(("request", owner))
                return {"ok": True}

            def cancel(self, owner, now_ms, scope_stop=False):
                calls.append(("cancel", owner, scope_stop))
                return {"ok": True}

            def tick(self, now_ms, lease):
                calls.append(("tick", lease["owner"], lease["valid"]))

            def status(self):
                return {"enabled": True, "state": "IDLE"}
        engine.baseband = Scheduler()
        self.assertEqual(engine.request({"op": "baseband_schedule", "value": {}, "_owner": OWNER}, 0)["error"],
                         "BASEBAND_LEASE_REQUIRED")
        self.assertTrue(engine.request({"op": "lease", "value": {"ttl_ms": 5000}, "_owner": OWNER}, 0)["ok"])
        self.assertTrue(engine.request({"op": "baseband_schedule", "value": {}, "_owner": OWNER}, 10)["ok"])
        self.assertTrue(engine.request({"op": "baseband_cancel", "value": {"scope_stop": True}, "_owner": "uid:2"}, 20)["ok"])
        engine.tick(30)
        self.assertEqual(calls[:2], [("request", OWNER), ("cancel", "uid:2", True)])
        self.assertIn(("tick", OWNER, True), calls)
        engine.tick(6000)  # the 5 s lease ran out: the scheduler sees it lost
        self.assertIs(calls[-1][2], False)


class ScopeSessionTests(unittest.TestCase):
    """baseband_cancel {scope_stop: true} latches the span in labd's own ScopeLatch for the session (fail closed)."""

    LEASE = {"owner": OWNER, "valid": True, "armed": True, "rtla_on": True}

    def test_a_scope_stop_holds_until_a_pass_at_a_tuning_that_does_not_touch_it_starts(self):
        clock, threads = Clock(AOS - 600), []
        scheduler = bs.BasebandScheduler(
            planner=Planner(plan()), utc_verified=lambda: True, systemctl=Systemctl(), accepted_loader=lambda: ACCEPTED,
            binding_loader=lambda: ("/dev/disk/by-uuid/0000-TEST", "/opt/srrx/evidence/rtla.json"),
            installation_check=lambda: None, installation_loader=lambda: {"sha256": "c" * 64},
            store_factory=lambda device: (None, lambda: None), scope=ScopeLatch(), wall_clock=clock,
            start_thread=threads.append, job_root="/nonexistent-srrx-jobs", products_root="/nonexistent-srrx-products")
        value = {"aos_utc": text(AOS), "center_hz": 137_900_000, "symbol_rate": 72_000}
        self.assertTrue(scheduler.request(value, OWNER, 0)["ok"])
        self.assertIs(scheduler.status()["scope_stopped"], False)
        self.assertTrue(scheduler.cancel("uid:3000", 0, scope_stop=True)["ok"])  # e.g. the HMI's identification stop
        scheduler.tick(1000, self.LEASE)
        status = scheduler.status()
        self.assertEqual((status["state"], status["last"]["error"], status["scope_stopped"]), ("IDLE", "CANCELLED", True))
        for center in (137_900_000, 137_912_500):  # both touch the latched span: refused for the rest of the session
            with self.subTest(center=center):
                self.assertEqual(scheduler.request(dict(value, center_hz=center), OWNER, 0),
                                 {"ok": False, "error": "OUT_OF_SCOPE"})
        self.assertTrue(scheduler.request(dict(value, center_hz=137_100_000), OWNER, 0)["ok"])
        self.assertIs(scheduler.status()["scope_stopped"], True)  # a queued pass releases nothing
        clock.now = scheduler._job["window"]["start_unix_s"] - bb.EARLY_START_S
        scheduler.tick(2000, self.LEASE)
        self.assertEqual(scheduler.status()["state"], "RECORD_STARTING")
        self.assertIs(scheduler.status()["scope_stopped"], False)  # the retune to 137.1 MHz released the latch
        self.assertEqual(len(threads), 1)


@unittest.skipUnless(os.name == "posix", "job directories (0700, euid) and the setgid work tree need POSIX")
class UnitEndTests(unittest.TestCase):
    """A result read while the unit may still write is not final; a stopped decode unit is seen ended first."""

    setUp, make, request, step = SchedulerTests.setUp, SchedulerTests.make, SchedulerTests.request, SchedulerTests.step
    record_unit, write_record_result = SchedulerTests.record_unit, SchedulerTests.write_record_result
    start_recording, run_to_decode = SchedulerTests.start_recording, SchedulerTests.run_to_decode

    def test_an_unreadable_record_result_counts_only_once_the_unit_ended(self):
        job_id, window = self.start_recording()
        path = self.jobs / job_id / sp.RESULT_FILE
        path.write_bytes(b"")  # what a reader would see between open(O_CREAT) and write() of a non-atomic writer
        self.step(ticks=3)
        self.assertEqual(self.scheduler.status()["state"], "RECORDING")
        self.assertIsNone(self.scheduler._job["result"])
        path.unlink()
        self.write_record_result(job_id)
        self.step(ticks=2)
        self.assertEqual(self.scheduler.status()["state"], "DECODE_WAIT")  # the complete recording is kept
        # An ended unit's unreadable result is final: nothing is decoded and the store is swept.
        self.systemctl.calls.clear()
        self.scheduler = self.make()
        job_id, window = self.start_recording()
        (self.jobs / job_id / sp.RESULT_FILE).write_bytes(b"{")
        self.systemctl.state[self.record_unit(job_id)] = "failed"
        self.step(ticks=3)
        status = self.scheduler.status()
        self.assertEqual((status["state"], status["last"]["error"]), ("IDLE", "UNIT_RESULT_INVALID"))
        self.assertIn(("sweep",), self.events)
        self.assertFalse((self.jobs / job_id).exists())
        self.assertFalse(any("decode" in unit for unused, unit in self.systemctl.calls))

    def decoding(self):
        self.run_to_decode()
        rid = "lrpt-" + "a" * 16
        unit = sp.unit_name(sp.DECODE_TEMPLATE, rid)
        with mock.patch.object(sp, "prepare_decode", return_value={"recording_id": rid, "unit": unit,
                                                                   "work": self.products / (".satdump-" + rid)}):
            self.step(LOS + bb.MARGIN_S)
        self.step()  # poll: the unit is activating
        self.assertEqual(self.scheduler.status()["state"], "DECODING")
        return unit

    def test_a_cancelled_decode_unit_is_seen_ended_before_its_work_tree_goes(self):
        unit = self.decoding()

        def stop(name):  # SIGTERM, then at most TimeoutStopSec=15: the unit takes its time to end
            self.systemctl.calls.append(("stop", name))
            self.systemctl.state[name] = "deactivating"
            return 0
        self.systemctl.stop = stop
        finished = []

        def finish(store, job, **kwargs):
            finished.append(self.systemctl.state[unit])
            raise decoder_policy.DecoderRefused("DECODE_UNIT_NO_RESULT")
        with mock.patch.object(sp, "finish_decode", side_effect=finish):
            self.assertTrue(self.scheduler.cancel(OWNER, 0)["ok"])
            self.step(ticks=3)
            self.assertIn(("stop", unit), self.systemctl.calls)
            self.assertEqual((self.scheduler.status()["state"], finished), ("DECODE_STOPPING", []))
            self.systemctl.state[unit] = "inactive"
            self.step(ticks=3)
        self.assertEqual(finished, ["inactive"])  # the work tree and the baseband go only after the unit ended
        status = self.scheduler.status()
        self.assertEqual((status["state"], status["last"]["error"]), ("IDLE", "CANCELLED"))

    def test_a_decode_unit_that_never_ends_is_finished_after_the_grace(self):
        unit = self.decoding()
        self.systemctl.state[unit] = "active"
        self.systemctl.stop = lambda name: self.systemctl.calls.append(("stop", name)) or 0  # stays active
        with mock.patch.object(sp, "finish_decode", side_effect=decoder_policy.DecoderRefused("DECODE_UNIT_NO_RESULT")) as finish:
            self.step(now_ms=self.now_ms + bs.DECODE_OVERRUN_S * 1000 + 1)  # overrun: stop
            self.assertIn(("stop", unit), self.systemctl.calls)
            self.step(ticks=bs.START_GRACE_MS // 2500 - 1)
            self.assertEqual((self.scheduler.status()["state"], finish.call_count), ("DECODE_STOPPING", 0))
            self.step(ticks=3)
        finish.assert_called_once()
        self.assertEqual(self.scheduler.status()["last"]["error"], "DECODE_UNIT_NO_RESULT")


if __name__ == "__main__":
    unittest.main()
