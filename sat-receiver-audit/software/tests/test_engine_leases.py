"""Exclusive engine leases (srrx.engine_leases, STACK.md C7 mode 2): templates, polkit rule, labd op.

Fake systemctl and device checks and temporary trees only: no unit is started, no receiver is
opened and no polkitd runs. The node evaluation of the staged rules is a CI model of polkitd's
JavaScript rules; DevicePolicy/DeviceAllow enforcement on a Q6A stays the RX-12-runtime row.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from srrx import engine_leases
from srrx.engine import Engine
from srrx.engine_leases import EngineLeases
from srrx.hardware import SimHardware
from srrx.link import SimLink

PROJECT = Path(__file__).resolve().parents[2]
UNITS = PROJECT / "software/systemd"
CASES = PROJECT / "deployment/tests/polkit_cases/lease.json"
BINARIES = {"readsb": "readsb", "aiscatcher": "AIS-catcher", "sdrangelsrv": "sdrangelsrv"}
sys.path.insert(0, str(PROJECT / "deployment"))
sys.path.insert(0, str(PROJECT / "deployment/system"))
import deploy  # noqa: E402
import system_files  # noqa: E402


def sections(text):
    """{section: [(key, value), ...]} of a unit file, comments skipped (no continuation lines used)."""
    result, section = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = result.setdefault(line[1:-1], [])
            continue
        key, sep, value = line.partition("=")
        assert sep, line
        section.append((key.strip(), value.strip()))
    return result


def stage_root(test):
    temp = tempfile.TemporaryDirectory(prefix="srrx-lease-test-")
    test.addCleanup(temp.cleanup)
    deploy.stage(Path(temp.name) / "stage")
    return Path(temp.name) / "stage/rootfs"


class FakeSystemctl:
    def __init__(self, log, codes=None):
        self.log, self.codes = log, dict(codes or {})

    def __call__(self, args, timeout_s):
        assert 0 < timeout_s <= 60
        self.log.append(("systemctl",) + tuple(args))
        return self.codes.get(tuple(args), 0)


class TemplateTests(unittest.TestCase):
    def test_three_templates_with_the_lease_sandbox_and_no_install(self):
        self.assertEqual(sorted(p.name for p in UNITS.glob("srrx-lease-*@.service")), sorted(engine_leases.TEMPLATES))
        self.assertEqual(deploy.LEASE_TEMPLATES, frozenset(engine_leases.TEMPLATES))
        self.assertTrue(deploy.LEASE_TEMPLATES <= deploy.RELEASE_GUARD_EXEMPT)
        for engine in engine_leases.ENGINES:
            unit = sections((UNITS / ("srrx-lease-" + engine + "@.service")).read_text(encoding="utf-8"))
            self.assertNotIn("Install", unit)  # never enabled, never wanted
            service = dict(unit["Service"])
            # The sandbox keys stay single assignments; engine packages may add other lines (arguments, Environment=).
            once = ("User", "DevicePolicy", "DeviceAllow", "ProtectSystem", "ReadOnlyPaths", "ReadWritePaths",
                    "IPAddressDeny", "IPAddressAllow", "RestrictAddressFamilies", "ExecStart")
            self.assertEqual([k for k in once if [key for key, _ in unit["Service"]].count(k) != 1], [], engine)
            expected = {"Type": "simple", "User": "lab", "Group": "lab", "DevicePolicy": "closed",
                        "DeviceAllow": "/dev/lab/%i rw", "ProtectSystem": "strict", "ProtectHome": "yes",
                        "ReadOnlyPaths": "/data", "ReadWritePaths": "/data/products/" + engine + "-%i",
                        "RuntimeDirectory": "srrx-lease-" + engine + "-%i", "RuntimeDirectoryMode": "0700",
                        "IPAddressDeny": "any", "IPAddressAllow": "localhost", "NoNewPrivileges": "yes",
                        "CapabilityBoundingSet": "", "PrivateTmp": "yes", "OOMScoreAdjust": "500",
                        "RuntimeMaxSec": "12h", "TimeoutStopSec": "10s", "Restart": "no"}
            self.assertEqual({k: service.get(k) for k in expected}, expected, engine)
            self.assertNotIn("PrivateDevices", service)  # it would hide /dev/bus/usb from the engine
            head = dict(unit["Unit"])
            self.assertEqual((head["BindsTo"], head["After"], head["AssertPathExists"]),
                             ("srrx.service", "srrx.service", "/dev/lab/%i"))
            self.assertEqual(service["ExecStart"].split()[:2], ["/usr/bin/env", BINARIES[engine]])
            self.assertEqual(engine_leases.products_dir(engine, "rtla"), "/data/products/" + engine + "-rtla")

    @unittest.skipUnless(os.name == "posix", "guest_smoke imports pwd/grp")
    def test_every_lease_exec_start_in_the_guest_verify_selection_goes_through_env(self):
        # F8: the lab guest runs systemd-analyze verify on guest_smoke.verify_units() without the
        # +lab engine packages, so an ExecStart naming /usr/bin/readsb would fail only in that run.
        sys.path.insert(0, str(PROJECT / "deployment/linux_lab"))
        import guest_smoke
        rootfs = stage_root(self)
        selected = guest_smoke.verify_units(rootfs, system_files.masks("gpsd"))
        leases = [p for p in selected if p.name.startswith("srrx-lease-")]
        self.assertEqual(sorted(p.name for p in leases), sorted(engine_leases.TEMPLATES))
        for path in leases:
            starts = [v for k, v in sections(path.read_text(encoding="utf-8"))["Service"] if k == "ExecStart"]
            self.assertEqual(len(starts), 1, path.name)
            self.assertTrue(starts[0].startswith("/usr/bin/env "), path.name)
            self.assertFalse((rootfs / "etc/systemd/system" / (path.name + ".d")).exists())  # no release guard drop-in
        self.assertEqual((rootfs / engine_leases.POLKIT_RULE).read_text(encoding="utf-8"), engine_leases.polkit_rule())

    @unittest.skipUnless(os.name == "posix" and shutil.which("systemd-analyze"), "systemd-analyze not installed")
    def test_systemd_analyze_verify_accepts_the_staged_templates(self):
        # CI model of the guest step on the runner's systemd: the templates and the unit they bind to.
        rootfs = stage_root(self)
        units = Path(tempfile.mkdtemp(prefix="srrx-lease-units-"))
        self.addCleanup(shutil.rmtree, units, True)
        for name in engine_leases.TEMPLATES + ("srrx.service",):
            shutil.copyfile(rootfs / "etc/systemd/system" / name, units / name)
        env = dict(os.environ, SYSTEMD_UNIT_PATH=str(units) + ":", SYSTEMD_LOG_COLOR="0")
        done = subprocess.run(["systemd-analyze", "verify", "--man=no", *(str(units / n) for n in engine_leases.TEMPLATES)],
                              capture_output=True, text=True, env=env, timeout=60)
        lease_lines = [line for line in (done.stdout + done.stderr).splitlines() if "srrx-lease" in line]
        self.assertEqual((done.returncode, lease_lines), (0, []), done.stdout + done.stderr)

    def test_tmpfiles_create_every_lease_products_directory_for_lab_and_labd(self):
        self.assertEqual(system_files.LEASE_ENGINES, engine_leases.ENGINES)
        self.assertEqual(system_files.LEASE_RECEIVERS, engine_leases.RECEIVERS)
        lines = [line for line in system_files.tmpfiles().splitlines() if line.startswith("d /data/products/")]
        expected = ["d %s 2750 lab labd -" % engine_leases.products_dir(e, r)
                    for e in engine_leases.ENGINES for r in engine_leases.RECEIVERS]
        self.assertEqual(lines, expected)
        users, groups = system_files.accounts()
        self.assertTrue({"lab", "labd"} <= users and {"lab", "labd"} <= groups)
        self.assertNotIn("srrx-lease", system_files.system_preset("gpsd"))  # no preset enables a lease

    def test_receiver_aliases_are_the_udev_symlinks(self):
        config = deploy.load(PROJECT / "deployment/devices.template.json")
        self.assertEqual({engine_leases.DEVICE_KEYS[r]: "/dev/lab/" + r for r in engine_leases.RECEIVERS},
                         {key: device["path"] for key, device in config["usb"].items()})
        with self.assertRaises(ValueError):
            engine_leases.unit_name("readsb", "hfp")
        with self.assertRaises(ValueError):
            engine_leases.unit_name("dump1090", "rtla")


class PolkitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def test_rule_allows_exactly_start_and_stop_of_the_nine_instances_for_labd(self):
        rule = engine_leases.polkit_rule()
        self.assertIn("/^srrx-lease-(readsb|aiscatcher|sdrangelsrv)@(rtla|rtlb|hfplus)\\.service$/", rule)
        self.assertIn('subject.user == "labd"', rule)
        self.assertIn('action.lookup("verb") == "start" || action.lookup("verb") == "stop"', rule)
        self.assertEqual(rule.count("polkit.Result.YES"), 1)
        self.assertNotIn("Result.AUTH", rule)
        self.assertEqual(engine_leases.staged_files(), {engine_leases.POLKIT_RULE: rule})

    def test_case_file_covers_every_instance_and_its_refusals(self):
        self.assertEqual((self.cases["schema_version"], self.cases["kind"], self.cases["rule"]),
                         (1, "srrx_polkit_cases", engine_leases.POLKIT_RULE))
        allowed = {(c["details"]["unit"], c["details"]["verb"]) for c in self.cases["cases"] if c["expect"] == "yes"}
        self.assertEqual(allowed, {(engine_leases.unit_name(e, r), v) for e in engine_leases.ENGINES
                                   for r in engine_leases.RECEIVERS for v in ("start", "stop")})
        ids = [c["id"] for c in self.cases["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(sum(c["expect"] is None for c in self.cases["cases"]), 30)
        pattern = re.compile(engine_leases.UNIT_PATTERN[1:-1])  # the JS ^...$ without the multiline flag
        for case in self.cases["cases"]:
            details, unit = case["details"], case["details"].get("unit")
            decided = (case["action"] == "org.freedesktop.systemd1.manage-units" and case["subject"]["user"] == "labd"
                       and details.get("verb") in ("start", "stop") and type(unit) is str and pattern.fullmatch(unit))
            self.assertEqual("yes" if decided else None, case["expect"], case["id"])

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_node_evaluates_every_staged_rule_against_the_cases(self):
        # CI model of polkitd: each staged rule file runs with a polkit object; the first result decides.
        rootfs = stage_root(self)
        rules = rootfs / "etc/polkit-1/rules.d"
        self.assertTrue((rules / Path(engine_leases.POLKIT_RULE).name).is_file())
        script = Path(tempfile.mkdtemp(prefix="srrx-polkit-")) / "harness.js"
        self.addCleanup(shutil.rmtree, script.parent, True)
        script.write_text(NODE_HARNESS, encoding="utf-8")
        done = subprocess.run([shutil.which("node"), str(script), str(rules), str(CASES)], capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        results = {r["id"]: r["result"] for r in json.loads(done.stdout)}
        self.assertEqual(results, {c["id"]: c["expect"] for c in self.cases["cases"]})


NODE_HARNESS = r"""
const fs = require("fs");
const [dir, casesPath] = process.argv.slice(2);
const rules = [];
const polkit = {Result: {NO: "no", YES: "yes", AUTH_SELF: "auth_self", AUTH_SELF_KEEP: "auth_self_keep",
                         AUTH_ADMIN: "auth_admin", AUTH_ADMIN_KEEP: "auth_admin_keep", NOT_HANDLED: null},
                addRule: (f) => rules.push(f), addAdminRule: () => {}, log: () => {},
                spawn: () => { throw new Error("spawn is not modelled"); }};
for (const name of fs.readdirSync(dir).filter((n) => n.endsWith(".rules")).sort()) {
  new Function("polkit", fs.readFileSync(dir + "/" + name, "utf8"))(polkit);
}
const out = JSON.parse(fs.readFileSync(casesPath, "utf8")).cases.map((c) => {
  const groups = c.subject.groups || [];
  const action = {id: c.action, lookup: (key) => c.details[key]};
  const subject = {user: c.subject.user, groups: groups, isInGroup: (g) => groups.includes(g),
                   isInNetGroup: () => false, local: true, active: true, session: "", pid: 1};
  let result = null;
  for (const rule of rules) {
    const r = rule(action, subject);
    if (r !== undefined && r !== null) { result = r; break; }
  }
  return {id: c.id, result: result};
});
process.stdout.write(JSON.stringify(out));
"""


class EngineLeasesTests(unittest.TestCase):
    def setUp(self):
        self.log, self.node_codes, self.deferred = [], {}, []
        self.fake = FakeSystemctl(self.log)
        self.leases = EngineLeases(systemctl=self.fake, check_node=self.node, start_thread=self.run_now)

    def node(self, receiver):
        self.log.append(("check", receiver))
        return self.node_codes.get(receiver)

    def run_now(self, target):
        target()

    def slot(self, receiver):
        return self.leases.status()["receivers"][receiver]

    def test_handover_is_stop_release_check_start(self):
        reply = self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)
        self.assertEqual((reply["ok"], reply["unit"]), (True, "srrx-lease-readsb@rtla.service"))
        self.assertEqual(self.log, [("systemctl", "stop", "srrx-lease-readsb@rtla.service"),
                                    ("systemctl", "stop", "srrx-lease-aiscatcher@rtla.service"),
                                    ("systemctl", "stop", "srrx-lease-sdrangelsrv@rtla.service"),
                                    ("check", "rtla"), ("systemctl", "start", "srrx-lease-readsb@rtla.service")])
        slot = self.slot("rtla")
        self.assertEqual((slot["state"], slot["mode"], slot["engine"], slot["owner"], slot["products"]),
                         ("ACTIVE", "engine", "readsb", "uid:1000", "/data/products/readsb-rtla"))
        self.assertEqual(self.slot("rtlb")["mode"], "labrx")

    def test_one_engine_per_receiver(self):
        self.assertTrue(self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)["ok"])
        count = len(self.log)
        self.assertEqual(self.leases.request({"engine": "aiscatcher", "receiver": "rtla"}, "uid:1000", 10)["error"],
                         "ENGINE_LEASE_BUSY")
        again = self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 20)
        self.assertEqual((again["ok"], again["state"]), (True, "ACTIVE"))  # idempotent, no second start
        self.assertEqual(len(self.log), count)
        self.assertTrue(self.leases.request({"engine": "aiscatcher", "receiver": "rtlb"}, "uid:1000", 30)["ok"])
        self.assertEqual(self.slot("rtlb")["unit"], "srrx-lease-aiscatcher@rtlb.service")

    def test_labrx_holder_and_engine_lease_exclude_each_other(self):
        self.assertTrue(self.leases.labrx_hold("rtla", "lrpt-0123456789abcdef")["ok"])
        refused = self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)
        self.assertEqual(refused["error"], "ENGINE_LEASE_LABRX_HOLDS")
        self.assertEqual(self.log, [])
        self.assertEqual(self.leases.labrx_hold("rtla", "other")["error"], "ENGINE_LEASE_LABRX_HOLDS")
        self.assertFalse(self.leases.labrx_release("rtla", "other"))
        self.assertTrue(self.leases.labrx_release("rtla", "lrpt-0123456789abcdef"))
        self.assertTrue(self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)["ok"])
        self.assertEqual(self.leases.labrx_hold("rtla", "lrpt-0123456789abcdef")["error"], "ENGINE_LEASE_BUSY")
        self.leases.stop("rtla", "OPERATOR_STOP")
        self.assertEqual(self.slot("rtla")["mode"], "labrx")
        self.assertTrue(self.leases.labrx_hold("rtla", "lrpt-0123456789abcdef")["ok"])

    def test_missing_or_foreign_node_never_starts_the_unit(self):
        for code in ("ENGINE_LEASE_NODE_MISSING", "ENGINE_LEASE_NODE_MISMATCH"):
            self.log.clear()
            self.node_codes["rtlb"] = code
            self.assertTrue(self.leases.request({"engine": "sdrangelsrv", "receiver": "rtlb"}, "uid:1000", 0)["ok"])
            self.assertNotIn("start", [entry[1] for entry in self.log])
            slot = self.slot("rtlb")
            self.assertEqual((slot["state"], slot["engine"], slot["last_error"]), ("IDLE", None, code))

    def test_failed_start_is_stopped_before_labrx_may_take_the_receiver(self):
        self.fake.codes[("start", "srrx-lease-readsb@hfplus.service")] = 1
        self.leases.request({"engine": "readsb", "receiver": "hfplus"}, "uid:1000", 0)
        self.assertEqual(self.log[-3:], [("systemctl", "stop", "srrx-lease-readsb@hfplus.service"),
                                         ("systemctl", "stop", "srrx-lease-aiscatcher@hfplus.service"),
                                         ("systemctl", "stop", "srrx-lease-sdrangelsrv@hfplus.service")])
        slot = self.slot("hfplus")
        self.assertEqual((slot["state"], slot["last_error"]), ("IDLE", "ENGINE_LEASE_START_FAILED"))

    def test_failed_stop_latches_fault_until_an_engine_stop_succeeds(self):
        self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)
        self.fake.codes[("stop", "srrx-lease-readsb@rtla.service")] = 1
        self.leases.stop_all("POLICY_TRIP")
        slot = self.slot("rtla")
        self.assertEqual((slot["state"], slot["last_error"], slot["last_stop"]),
                         ("FAULT", "ENGINE_LEASE_STOP_FAILED", "POLICY_TRIP"))
        self.assertEqual(self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 1)["error"],
                         "ENGINE_LEASE_FAULT")
        self.assertEqual(self.leases.labrx_hold("rtla", "x")["error"], "ENGINE_LEASE_BUSY")
        self.assertEqual(self.leases.stop_all("POLICY_TRIP"), [])  # a trip does not retry; engine_stop does
        del self.fake.codes[("stop", "srrx-lease-readsb@rtla.service")]
        self.assertEqual(self.leases.stop_request({"reason": "operator", "receiver": "rtla"})["stopping"], ["rtla"])
        self.assertEqual(self.slot("rtla")["state"], "IDLE")

    def test_stop_during_the_handover_wins(self):
        self.leases.start_thread = self.deferred.append
        self.leases.request({"engine": "aiscatcher", "receiver": "rtla"}, "uid:1000", 0)
        self.assertEqual(self.slot("rtla")["state"], "STARTING")
        self.assertEqual(self.leases.labrx_hold("rtla", "x")["error"], "ENGINE_LEASE_BUSY")
        self.leases.stop(None, "SCOPE_STOP")
        self.deferred.pop()()
        self.assertNotIn("start", [entry[1] for entry in self.log])
        slot = self.slot("rtla")
        self.assertEqual((slot["state"], slot["engine"], slot["last_stop"]), ("IDLE", None, "SCOPE_STOP"))

    def test_watch_notices_an_exited_unit(self):
        self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)
        self.leases.tick(engine_leases.WATCH_MS - 1, lambda owner: True)
        self.assertNotIn("is-active", [entry[2] for entry in self.log if len(entry) > 2])
        self.fake.codes[("--quiet", "is-active", "srrx-lease-readsb@rtla.service")] = 3
        self.leases.tick(engine_leases.WATCH_MS, lambda owner: True)
        slot = self.slot("rtla")
        self.assertEqual((slot["state"], slot["last_error"], slot["last_stop"]),
                         ("IDLE", "ENGINE_LEASE_UNIT_EXITED", "UNIT_EXITED"))

    def test_lost_operator_lease_stops_and_requests_are_validated(self):
        self.leases.request({"engine": "readsb", "receiver": "rtlb"}, "uid:1000", 0)
        self.leases.tick(100, lambda owner: owner == "uid:1001")
        self.assertEqual((self.slot("rtlb")["state"], self.slot("rtlb")["last_stop"]), ("IDLE", "OPERATOR_LEASE_LOST"))
        for value in (None, {}, {"engine": "readsb"}, {"engine": "readsb", "receiver": "hfp"},
                      {"engine": "dump1090", "receiver": "rtla"}, {"engine": "readsb", "receiver": "rtla", "args": "-X"}):
            self.assertEqual(self.leases.request(value, "uid:1000", 0)["error"], "ENGINE_LEASE_BAD_REQUEST")
        for value in (None, {}, {"reason": "other"}, {"reason": "scope", "receiver": "lime"}, {"reason": "scope", "x": 1}):
            self.assertEqual(self.leases.stop_request(value)["error"], "ENGINE_LEASE_BAD_REQUEST")

    def test_no_worker_thread_refuses_the_lease_and_queues_stops_without_waiting(self):
        def no_thread(target):
            raise RuntimeError("can't start new thread")
        self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)
        self.leases.start_thread = no_thread
        self.assertEqual(self.leases.request({"engine": "readsb", "receiver": "rtlb"}, "uid:1000", 0)["error"],
                         "ENGINE_LEASE_INTERNAL")
        self.assertEqual(self.slot("rtlb")["state"], "IDLE")
        self.log.clear()
        self.leases.stop_all("POLICY_TRIP")
        self.assertEqual(self.log, [("systemctl", "--no-block", "stop", engine_leases.unit_name(e, "rtla"))
                                    for e in engine_leases.ENGINES])
        self.assertEqual(self.slot("rtla")["state"], "FAULT")

    def test_close_refuses_new_leases_and_stops_running_units_without_waiting(self):
        self.leases.request({"engine": "sdrangelsrv", "receiver": "hfplus"}, "uid:1000", 0)
        self.log.clear()
        self.leases.close()
        self.assertEqual(self.log, [("systemctl", "--no-block", "stop", "srrx-lease-sdrangelsrv@hfplus.service")])
        self.assertEqual(self.leases.request({"engine": "readsb", "receiver": "rtla"}, "uid:1000", 0)["error"],
                         "ENGINE_LEASE_CLOSED")


@unittest.skipUnless(os.name == "posix", "the sysfs fixture names directories <major>:<minor>")
class ReenumerationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-lease-node-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        config = deploy.load(PROJECT / "deployment/devices.template.json")
        self.devices = self.root / "devices.json"
        self.devices.write_text(json.dumps(config), encoding="utf-8")
        self.sys = self.root / "sys"
        self.sysfs("189:5", "usb_device", "0bda", "2838", "LABRXA")

    def sysfs(self, node, devtype, vid, pid, serial):
        directory = self.sys / node
        directory.mkdir(parents=True)
        (directory / "uevent").write_text("MAJOR=189\nMINOR=5\nDEVNAME=bus/usb/001/005\nDEVTYPE=%s\n" % devtype)
        for name, value in (("idVendor", vid), ("idProduct", pid), ("serial", serial)):
            (directory / name).write_text(value + "\n")

    def check(self, node=lambda path: (189, 5), receiver="rtla"):
        return engine_leases.reenumeration_check(receiver, devices_path=self.devices, dev_root=self.root / "dev",
                                                 sys_char_root=self.sys, char_node=node)

    def test_the_alias_must_be_the_bound_usb_device_again(self):
        seen = []
        self.assertIsNone(self.check(lambda path: seen.append(path) or (189, 5)))
        self.assertEqual(seen, [self.root / "dev/rtla"])
        self.assertEqual(self.check(receiver="rtlb"), "ENGINE_LEASE_NODE_MISMATCH")  # serial LABRXB expected

        def missing(path):
            raise FileNotFoundError(path)
        self.assertEqual(self.check(missing), "ENGINE_LEASE_NODE_MISSING")
        self.assertEqual(self.check(lambda path: None), "ENGINE_LEASE_NODE_MISMATCH")  # not a character device
        self.assertEqual(self.check(lambda path: (189, 6)), "ENGINE_LEASE_NODE_MISMATCH")  # no sysfs node
        self.sysfs("189:7", "usb_interface", "0bda", "2838", "LABRXA")
        self.assertEqual(self.check(lambda path: (189, 7)), "ENGINE_LEASE_NODE_MISMATCH")
        self.sysfs("189:8", "usb_device", "0bda", "2832", "LABRXA")
        self.assertEqual(self.check(lambda path: (189, 8)), "ENGINE_LEASE_NODE_MISMATCH")
        # hfplus: the template serial is null, so the bindings are unusable until observed.
        self.assertEqual(self.check(receiver="hfplus"), "ENGINE_LEASE_DEVICES_UNAVAILABLE")
        self.devices.unlink()
        self.assertEqual(self.check(), "ENGINE_LEASE_DEVICES_UNAVAILABLE")


class EngineOperationTests(unittest.TestCase):
    """labd op engine_lease on the simulated Engine with injected leases (simulation leaves them off)."""

    def setUp(self):
        self.hardware = SimHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith("DCS_")})
        self.engine = Engine(self.hardware, SimLink(PROJECT), simulated=True)
        self.addCleanup(self.engine.close)
        self.log = []
        self.engine.leases = EngineLeases(systemctl=FakeSystemctl(self.log), check_node=lambda receiver: None,
                                          start_thread=lambda target: target())
        self.now = 0
        self.engine.tick(self.now)

    def advance(self, ms, renew=True):
        end = self.now + ms
        while self.now < end:
            self.now += 20
            if renew and self.engine.policy.armed and self.now % 1000 == 0:
                self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 5000})["ok"])
            self.engine.tick(self.now)

    def request(self, owner, **fields):
        return self.engine.request(dict(fields, _owner=owner), self.now)

    def lease(self, owner="uid:1000", engine="readsb", receiver="rtla"):
        return self.request(owner, op="engine_lease", value={"engine": engine, "receiver": receiver})

    def state(self, receiver="rtla"):
        return self.engine.status()["engine_leases"]["receivers"][receiver]

    def arm(self):
        self.assertTrue(self.request("uid:1000", op="arm")["ok"])
        self.advance(800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())

    def test_refused_without_the_callers_own_operator_lease(self):
        self.assertEqual(self.lease()["error"], "ENGINE_LEASE_NO_OPERATOR_LEASE")
        self.assertTrue(self.request("uid:1001", op="lease", value={"ttl_ms": 5000})["ok"])
        self.assertEqual(self.lease("uid:1000")["error"], "ENGINE_LEASE_NO_OPERATOR_LEASE")
        self.assertEqual(self.log, [])
        self.assertEqual(self.state()["state"], "IDLE")

    def test_refused_while_labrx_holds_the_receiver(self):
        self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 5000})["ok"])
        self.assertTrue(self.engine.leases.labrx_hold("rtla", "lrpt-0123456789abcdef")["ok"])
        self.assertEqual(self.lease()["error"], "ENGINE_LEASE_LABRX_HOLDS")
        self.assertEqual(self.log, [])
        self.assertTrue(self.lease(receiver="rtlb")["ok"])

    def test_stopped_on_disarm(self):
        self.arm()
        self.assertTrue(self.lease()["ok"])
        self.assertEqual((self.state()["state"], self.state()["mode"]), ("ACTIVE", "engine"))
        self.log.clear()
        self.assertTrue(self.request("uid:1000", op="disarm")["ok"])
        self.assertIn(("systemctl", "stop", "srrx-lease-readsb@rtla.service"), self.log)
        self.assertEqual((self.state()["state"], self.state()["mode"], self.state()["last_stop"]),
                         ("IDLE", "labrx", "POLICY_TRIP"))

    def test_a_trip_inside_the_policy_also_ends_the_lease(self):
        self.arm()
        self.assertTrue(self.lease(engine="aiscatcher")["ok"])
        self.engine.policy.trip("synthetic policy fault")  # not through Engine.trip
        self.advance(20)
        self.assertEqual((self.state()["state"], self.state()["last_stop"]), ("IDLE", "POLICY_TRIP"))

    def test_stopped_when_the_operator_lease_expires(self):
        self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 2000})["ok"])
        self.assertTrue(self.lease(engine="sdrangelsrv", receiver="rtlb")["ok"])
        self.advance(1000, renew=False)
        self.assertEqual(self.state("rtlb")["state"], "ACTIVE")
        self.advance(1100, renew=False)
        self.assertEqual((self.state("rtlb")["state"], self.state("rtlb")["last_stop"]), ("IDLE", "OPERATOR_LEASE_LOST"))

    def test_scope_stop_needs_no_lease(self):
        self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 5000})["ok"])
        self.assertTrue(self.lease()["ok"])
        reply = self.request("uid:1001", op="engine_stop", value={"reason": "scope"})
        self.assertEqual((reply["ok"], reply["stopping"]), (True, ["rtla"]))
        self.assertEqual((self.state()["state"], self.state()["last_stop"]), ("IDLE", "SCOPE_STOP"))

    def test_receiver_en_off_while_armed_ends_only_that_receivers_lease(self):
        # Powered again, the receiver re-enumerates with a new minor the unit's BPF allow-list lacks.
        self.assertEqual(engine_leases.POWER_OUTPUTS, {"rtla": "EN_RTLA", "rtlb": "EN_RTLB", "hfplus": "EN_HFP"})
        self.arm()
        for output in ("EN_RTLA", "EN_HFP"):
            self.assertTrue(self.request("uid:1000", op="control", name=output, value=True)["ok"])
        self.advance(40)
        self.assertTrue(self.lease()["ok"])
        self.assertTrue(self.lease(engine="sdrangelsrv", receiver="hfplus")["ok"])
        self.log.clear()
        self.assertTrue(self.request("uid:1000", op="control", name="EN_RTLA", value=False)["ok"])
        self.advance(20)
        self.assertTrue(self.engine.policy.armed)
        self.assertEqual((self.state()["state"], self.state()["last_stop"]), ("IDLE", "RECEIVER_OFF"))
        self.assertIn(("systemctl", "stop", "srrx-lease-readsb@rtla.service"), self.log)
        self.assertEqual(self.state("hfplus")["state"], "ACTIVE")
        self.assertFalse(any("@hfplus" in " ".join(entry) for entry in self.log))
        # A DISARM ends the rest as a policy trip, not as a receiver switched off.
        self.assertTrue(self.request("uid:1000", op="disarm")["ok"])
        self.advance(20)
        self.assertEqual((self.state("hfplus")["state"], self.state("hfplus")["last_stop"]), ("IDLE", "POLICY_TRIP"))

    def test_simulation_has_no_engine_leases_and_hardware_has_them(self):
        plain = Engine(SimHardware(), SimLink(PROJECT), simulated=True)
        self.addCleanup(plain.close)
        self.assertEqual(plain.request({"op": "engine_lease", "_owner": "uid:1000",
                                        "value": {"engine": "readsb", "receiver": "rtla"}}, 0)["error"],
                         "ENGINE_LEASE_DISABLED")
        self.assertEqual(plain.request({"op": "engine_stop", "value": {"reason": "scope"}}, 0)["error"],
                         "ENGINE_LEASE_DISABLED")
        self.assertEqual(plain.status()["engine_leases"], {"enabled": False})
        hardware = Engine(SimHardware(), SimLink(PROJECT), simulated=False)
        self.addCleanup(hardware.close)
        self.assertIsInstance(hardware.leases, EngineLeases)
        self.assertTrue(hardware.status()["engine_leases"]["enabled"])


if __name__ == "__main__":
    unittest.main()
