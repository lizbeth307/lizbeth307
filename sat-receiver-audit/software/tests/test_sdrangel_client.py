"""SDRangel +lab (SW-SDRANGEL): the LOppmTenths REST client and the recipe's own checks.

srrx.sdrangel_client runs against a fake SDRangel REST server: in process, and behind a real
http.server on an AF_UNIX socket (the host regression denies AF_INET sockets, so the TCP path to
127.0.0.1:8091 itself is not exercised here). The recipe tests check that the package hook, the
runtime check, the receive-only policy, the lease template and the RX-only patch agree, on
synthetic install trees. No SDRangel is built or started here: that is the sr-rx-packages heavy
job (CI model), and the HF+ read-back on a Q6A stays the device row HF-5.
"""
import copy
import hashlib
import http.client
import http.server
import importlib.util
import json
import os
from pathlib import Path
import socket
import socketserver
import sys
import tempfile
import threading
import unittest
from urllib.parse import parse_qsl, urlsplit

from srrx import sdrangel_client
from srrx.sdrangel_client import SdrangelClient, SdrangelError, lo_ppm_tenths

PROJECT = Path(__file__).resolve().parents[2]
RECIPE_DIR = PROJECT / "deployment/recipes/sdrangel"
sys.path.insert(0, str(PROJECT / "deployment"))
sys.path.insert(0, str(PROJECT / "deployment/recipes"))
import build_recipe  # noqa: E402
import deploy  # noqa: E402
import selftest  # noqa: E402


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_recipe = _module("srrx_sdrangel_check_recipe", RECIPE_DIR / "check_recipe.py")
runtime_check = _module("srrx_sdrangel_runtime_check", RECIPE_DIR / "runtime_check.py")

PRESETS = {("HF", 7_100_000, "R", "40 m"): 0, ("HF", 10_000_000, "R", "WWV 10"): 0, ("HF", 518_000, "R", "NAVTEX 518"): 0}


class FakeSdrangel:
    """The REST paths srrx.sdrangel_client uses (swagger.yaml at 97e9e21), with one device set.
    As in SDRangel, preset loads and device PATCHes go through queues: load_polls and patch_polls
    settings reads pass before they land. Faults: save_drops_lo (PUT /sdrangel/preset keeps the
    old LOppmTenths), reply_offset (the PATCH reply is off), read_offset (every GET is off),
    hwtype (the device of set 0)."""

    def __init__(self, hwtype="AirspyHF", load_polls=0, patch_polls=0, save_drops_lo=False, reply_offset=0, read_offset=0):
        self.hwtype, self.load_polls, self.patch_polls, self.save_drops_lo = hwtype, load_polls, patch_polls, save_drops_lo
        self.reply_offset, self.read_offset = reply_offset, read_offset
        self.presets = {k: {"centerFrequency": k[1], "LOppmTenths": v} for k, v in PRESETS.items()}
        self.device = {"centerFrequency": 7_100_000, "LOppmTenths": 0, "log2Decim": 0}
        self.queue, self.calls = [], []

    def _land(self):
        for item in list(self.queue):
            if item[0] == 0:
                self.device.update(item[1])
                self.queue.remove(item)
            else:
                item[0] -= 1

    def _settings(self, offset):
        if self.hwtype != "AirspyHF":
            return {"deviceHwType": self.hwtype, "direction": 0, "rtlSdrSettings": {"centerFrequency": self.device["centerFrequency"]}}
        return {"deviceHwType": "AirspyHF", "direction": 0, "airspyHFSettings": dict(self.device, LOppmTenths=self.device["LOppmTenths"] + offset)}

    def _key(self, body):
        preset = (body or {}).get("preset") or {}
        return (preset.get("groupName"), preset.get("centerFrequency"), preset.get("type"), preset.get("name"))

    def handle(self, method, path, query, body):
        self.calls.append((method, path, dict(query), copy.deepcopy(body)))
        if (method, path) == ("GET", "/sdrangel"):
            return 200, {"appname": "SDRangelSrv", "version": "7.27.2", "devicesetlist": {"devicesetcount": 1, "deviceSets": [
                {"samplingDevice": {"index": 0, "hwType": self.hwtype, "sequence": 0, "serial": "fixture"}, "channelcount": 0}]}}
        if (method, path) == ("GET", "/sdrangel/presets"):
            groups = {}
            for group, frequency, kind, name in sorted(self.presets):
                groups.setdefault(group, []).append({"centerFrequency": frequency, "type": kind, "name": name})
            groups.setdefault("TX", []).append({"centerFrequency": 1, "type": "T", "name": "never listed as Rx"})
            return 200, {"nbGroups": len(groups), "groups": [{"groupName": g, "nbPresets": len(p), "presets": p} for g, p in groups.items()]}
        if path == "/sdrangel/preset" and method in ("PATCH", "PUT"):
            key = self._key(body)
            if body.get("deviceSetIndex") != 0 or key not in self.presets:
                return 404, {"message": "There is no preset"}
            if method == "PATCH":
                self.queue.append([self.load_polls, dict(self.presets[key])])
            else:
                saved = dict(self.device)
                if self.save_drops_lo:
                    saved["LOppmTenths"] = self.presets[key]["LOppmTenths"]
                self.presets[key] = saved
            return 202, {"groupName": key[0], "centerFrequency": key[1], "type": key[2], "name": key[3]}
        if path == "/sdrangel/deviceset/0/device/settings":
            if method == "GET":
                self._land()
                return 200, self._settings(self.read_offset)
            if method == "PATCH":
                if body.get("deviceHwType") != self.hwtype:
                    return 400, {"message": "device type mismatch"}
                values = dict(body.get("airspyHFSettings") or {})
                self.queue.append([self.patch_polls, values])
                reply = self._settings(self.reply_offset)
                reply["airspyHFSettings"].update({k: v + (self.reply_offset if k == "LOppmTenths" else 0) for k, v in values.items()})
                return 200, reply
        return 404, {"message": "no such path"}


class InProcess:
    """RestTransport stand-in: the same JSON round trip, no socket."""

    def __init__(self, fake):
        self.fake = fake

    def request(self, method, path, body=None, query=None):
        status, data = self.fake.handle(method, path, dict(query or {}), json.loads(json.dumps(body)) if body is not None else None)
        return status, json.loads(json.dumps(data))


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def client(fake, **kwargs):
    clock = Clock()
    return SdrangelClient(InProcess(fake), clock=clock, sleep=clock.sleep, **kwargs)


class LoPpmTenthsTests(unittest.TestCase):
    def test_round_half_away_from_zero_within_the_gui_range(self):
        cases = {0: 0, 49: 0, 50: 1, 149: 1, 150: 2, 250: 3, -49: 0, -50: -1, -250: -3, -152: -2, 10049: 100, -10049: -100}
        for ppb, tenths in cases.items():
            self.assertEqual(lo_ppm_tenths(ppb), tenths, ppb)

    def test_refusals(self):
        for ppb, code in ((10050, "SDRANGEL_PPB_OUT_OF_RANGE"), (-10050, "SDRANGEL_PPB_OUT_OF_RANGE"), (1.5, "SDRANGEL_BAD_PPB"),
                          ("150", "SDRANGEL_BAD_PPB"), (True, "SDRANGEL_BAD_PPB"), (None, "SDRANGEL_BAD_PPB")):
            with self.assertRaises(SdrangelError) as caught:
                lo_ppm_tenths(ppb)
            self.assertEqual(caught.exception.code, code, ppb)
        with self.assertRaises(ValueError):
            SdrangelError("NOT_A_CODE")


class EndpointTests(unittest.TestCase):
    def test_only_loopback_ip_literals_over_http(self):
        self.assertEqual(sdrangel_client.loopback_endpoint("http://127.0.0.1:8091"), ("127.0.0.1", 8091))
        self.assertEqual(sdrangel_client.loopback_endpoint("http://[::1]:8091/"), ("::1", 8091))
        for url in ("http://localhost:8091", "http://192.168.1.5:8091", "https://127.0.0.1:8091", "http://127.0.0.1",
                    "http://127.0.0.1:80", "http://127.0.0.1:8091/sdrangel", "http://user@127.0.0.1:8091", "http://0.0.0.0:8091",
                    "http://[::]:8091", "ftp://127.0.0.1:8091", "127.0.0.1:8091", "http://127.0.0.1:8091?x=1"):
            with self.assertRaises(SdrangelError, msg=url) as caught:
                sdrangel_client.RestTransport(url)
            self.assertEqual(caught.exception.code, "SDRANGEL_NOT_LOOPBACK", url)


class ClientTests(unittest.TestCase):
    def test_push_writes_reads_back_saves_and_reads_back_after_reload_for_every_rx_preset(self):
        fake = FakeSdrangel(load_polls=2, patch_polls=1)
        result = client(fake).push_lo_ppm(-152, 0)
        self.assertEqual((result["status"], result["lo_ppm_tenths"]), ("LO_PPM_WRITTEN", -2))
        self.assertEqual(sorted(p["name"] for p in result["presets"]), sorted(k[3] for k in PRESETS))
        self.assertEqual({v["LOppmTenths"] for v in fake.presets.values()}, {-2})
        patches = [c[3] for c in fake.calls if c[:2] == ("PATCH", "/sdrangel/deviceset/0/device/settings")]
        self.assertEqual([p for p in patches if "LOppmTenths" in p["airspyHFSettings"]],
                         [{"deviceHwType": "AirspyHF", "direction": 0, "airspyHFSettings": {"LOppmTenths": -2}}] * 3)
        markers = sorted(p["airspyHFSettings"]["centerFrequency"] for p in patches if "centerFrequency" in p["airspyHFSettings"])
        self.assertEqual(markers, sorted(2 * [k[1] + 1 for k in PRESETS]))  # 1 Hz off before each of the two loads
        self.assertEqual(sum(c[:2] == ("PUT", "/sdrangel/preset") for c in fake.calls), 3)
        self.assertEqual(sum(c[:2] == ("PATCH", "/sdrangel/preset") for c in fake.calls), 6)  # load, then reload after the save
        self.assertFalse(result["hardware_ready"])
        self.assertEqual(client(fake).verify_lo_ppm(-152, 0)["status"], "LO_PPM_VERIFIED")

    def test_a_slow_reload_of_a_preset_that_lost_the_value_is_still_caught(self):
        # The device already sits on the preset's frequency when it is reloaded after the save: only
        # the 1 Hz marker tells the landed reload from the settings before it.
        with self.assertRaises(SdrangelError) as caught:
            client(FakeSdrangel(load_polls=3, patch_polls=2, save_drops_lo=True)).push_lo_ppm(300, 0)
        self.assertEqual(caught.exception.code, "LO_PPM_MISMATCH")
        self.assertIn("after reloading the saved preset", caught.exception.detail)
        with self.assertRaises(SdrangelError) as caught:
            client(FakeSdrangel(patch_polls=10_000)).verify_lo_ppm(0, 0)
        self.assertEqual(caught.exception.code, "SDRANGEL_PRESET_NOT_LOADED")
        self.assertIn("marker", caught.exception.detail)

    def test_explicit_presets_and_the_tx_preset_is_never_a_target(self):
        fake = FakeSdrangel()
        only = {"groupName": "HF", "centerFrequency": 518_000, "type": "R", "name": "NAVTEX 518"}
        self.assertEqual(client(fake).push_lo_ppm(250, 0, [only])["presets"], [only])
        self.assertEqual(fake.presets[("HF", 518_000, "R", "NAVTEX 518")]["LOppmTenths"], 3)
        self.assertEqual(fake.presets[("HF", 7_100_000, "R", "40 m")]["LOppmTenths"], 0)
        self.assertNotIn("never listed as Rx", [p["name"] for p in client(fake).rx_presets()])
        for bad in (dict(only, type="T"), dict(only, centerFrequency="518000"), {"name": "x"}, "preset"):
            with self.assertRaises(SdrangelError) as caught:
                client(FakeSdrangel()).push_lo_ppm(250, 0, [bad])
            self.assertEqual(caught.exception.code, "SDRANGEL_NO_PRESET")

    def test_every_mismatch_is_refused(self):
        for fake, stage in ((FakeSdrangel(save_drops_lo=True), "after reloading the saved preset"),
                            (FakeSdrangel(read_offset=1), "after the write"),
                            (FakeSdrangel(reply_offset=1), "PATCH reply")):
            with self.assertRaises(SdrangelError) as caught:
                client(fake).push_lo_ppm(300, 0)
            self.assertEqual(caught.exception.code, "LO_PPM_MISMATCH")
            self.assertIn(stage, caught.exception.detail)
        fake = FakeSdrangel()
        client(fake).push_lo_ppm(300, 0)
        with self.assertRaises(SdrangelError) as caught:
            client(fake).verify_lo_ppm(400, 0)  # the flash calibration changed; the presets did not
        self.assertEqual(caught.exception.code, "LO_PPM_MISMATCH")

    def test_wrong_device_missing_preset_lost_load_and_http_errors(self):
        for kwargs, call, code in ((dict(hwtype="RTLSDR"), lambda c: c.push_lo_ppm(100, 0), "SDRANGEL_NOT_AIRSPYHF"),
                                   ({}, lambda c: c.push_lo_ppm(100, 1), "SDRANGEL_NOT_AIRSPYHF"),
                                   (dict(load_polls=10_000), lambda c: c.verify_lo_ppm(100, 0), "SDRANGEL_PRESET_NOT_LOADED")):
            with self.assertRaises(SdrangelError) as caught:
                call(client(FakeSdrangel(**kwargs)))
            self.assertEqual(caught.exception.code, code)
        missing = {"groupName": "HF", "centerFrequency": 1, "type": "R", "name": "gone"}
        with self.assertRaises(SdrangelError) as caught:
            client(FakeSdrangel()).push_lo_ppm(100, 0, [missing])
        self.assertEqual(caught.exception.code, "SDRANGEL_HTTP")
        empty = FakeSdrangel()
        empty.presets = {}
        with self.assertRaises(SdrangelError) as caught:
            client(empty).verify_lo_ppm(100, 0)
        self.assertEqual(caught.exception.code, "SDRANGEL_NO_PRESET")


class _Handler(http.server.BaseHTTPRequestHandler):
    def _serve(self):
        parts = urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length else None
        status, data = self.server.fake.handle(self.command, parts.path, dict(parse_qsl(parts.query)), body)
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_PATCH = do_PUT = _serve

    def log_message(self, *args):  # no host log; client_address of an AF_UNIX peer is not a tuple
        pass


class _UnixConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost", timeout=5)
        self.unix_path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect(self.unix_path)


@unittest.skipUnless(hasattr(socket, "AF_UNIX") and hasattr(socketserver, "UnixStreamServer"), "AF_UNIX sockets are unavailable")
class HttpFakeServerTests(unittest.TestCase):
    """The same fake behind a real HTTP server: request lines, headers and JSON bodies of RestTransport."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="srrx-sdr-")
        self.path = os.path.join(self.directory.name, "rest.sock")
        self.server = socketserver.UnixStreamServer(self.path, _Handler)
        self.server.fake = FakeSdrangel(load_polls=1)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def transport(self):
        return sdrangel_client.RestTransport(connection_factory=lambda: _UnixConnection(self.path))

    def test_push_and_verify_over_http(self):
        clock = Clock()
        remote = SdrangelClient(self.transport(), clock=clock, sleep=clock.sleep)
        self.assertEqual(remote.push_lo_ppm(1049, 0)["lo_ppm_tenths"], 10)
        self.assertEqual(remote.verify_lo_ppm(1049, 0)["status"], "LO_PPM_VERIFIED")
        self.assertEqual({v["LOppmTenths"] for v in self.server.fake.presets.values()}, {10})

    def test_http_status_and_non_json_replies_are_refused(self):
        status, data = self.transport().request("GET", "/nowhere")
        self.assertEqual((status, data), (404, {"message": "no such path"}))
        with self.assertRaises(SdrangelError) as caught:
            SdrangelClient(self.transport())._call("GET", "/nowhere", 200)
        self.assertEqual(caught.exception.code, "SDRANGEL_HTTP")
        broken = sdrangel_client.RestTransport(connection_factory=lambda: _UnixConnection(self.path + ".missing"))
        with self.assertRaises(SdrangelError) as caught:
            broken.request("GET", "/sdrangel")
        self.assertEqual(caught.exception.code, "SDRANGEL_HTTP")


def _symlinks_work():
    with tempfile.TemporaryDirectory(prefix="srrx-link-") as temporary:
        try:
            os.symlink("target", os.path.join(temporary, "link"))
        except (OSError, NotImplementedError):
            return False
    return True


def install_tree(root, extra=(), missing=()):
    """A synthetic `cmake --install` tree in the reviewed layout (ELF magic in binaries and libraries)."""
    prefix = Path(root) / "opt/sdrangel"
    files = (["bin/" + b for b in check_recipe.BINARIES] + ["lib/" + n for n in check_recipe.CORE_LIBRARIES]
             + ["lib/sdrangel/plugins/" + n for n in check_recipe.GUI_PLUGINS] + ["lib/sdrangel/pluginssrv/" + n for n in check_recipe.SERVER_PLUGINS])
    for relative in sorted(set(files) - set(missing)) + list(extra):
        path = prefix / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x7fELF" + relative.encode())
    for relative, text in (("share/sdrangel/Readme.md", "readme"), ("share/sdrangel/LICENSE", "GPL-3.0"),
                           ("share/applications/sdrangel.desktop", "[Desktop Entry]"), ("share/metainfo/org.sdrangel.SDRangel.metainfo.xml", "<x/>")):
        (prefix / relative).parent.mkdir(parents=True, exist_ok=True)
        (prefix / relative).write_text(text, encoding="utf-8")
    return prefix


class RecipeTests(unittest.TestCase):
    """The recipe, its hook, its runtime check, the policy component and the lease template agree."""

    recipe = deploy.load(RECIPE_DIR / "recipe.json")

    def test_recipe_validates_as_a_heavy_recipe_built_against_the_lab_librtlsdr(self):
        component = build_recipe.validate_recipe(self.recipe)
        self.assertEqual((component["id"], component["version"], component["commit"]),
                         ("sdrangel", "7.27.2+lab1", "97e9e21fe9754b363ae70caac822802d908e8acd"))
        plan = build_recipe.ci_plan()
        self.assertIn("sdrangel", plan["heavy"])
        self.assertEqual(plan["recipes"]["sdrangel"]["chain"], ["rtlsdr", "sdrangel"])
        self.assertTrue(plan["recipes"]["sdrangel"]["runtime_check"])
        self.assertEqual(self.recipe["ci"], {"heavy": True, "runtime_depends": [], "tag_samples": []})
        self.assertNotIn("libhamlib-dev", self.recipe["build_depends"])
        self.assertEqual(self.recipe["cmake"]["variables"]["ENABLE_EXTERNAL_LIBRARIES"], "OFF")
        self.assertEqual(self.recipe["cmake"]["variables"]["ARCH_OPT"], "armv8-a")

    def test_options_turn_on_exactly_the_built_allowlist(self):
        options = self.recipe["cmake"]["options"]
        on = {k for k, v in options.items() if v == "ON"}
        channels = {k[len("ENABLE_CHANNELRX_"):].lower() for k in on if k.startswith("ENABLE_CHANNELRX_")}
        features = {k[len("ENABLE_FEATURE_"):].lower() for k in on if k.startswith("ENABLE_FEATURE_")}
        self.assertEqual(channels, {"chanalyzer", "channelpower", "demodam", "demodbfm", "demodwfm", "demodnfm", "demodssb", "demodnavtex",
                                    "demodrtty", "demodft8", "demodpacket", "radioclock", "radioastronomy", "freqtracker", "demodvor",
                                    "demodils", "noisefigure"})
        self.assertEqual(features, {"freqdisplay", "antennatools", "demodanalyzer"})
        self.assertEqual({k for k in on if not k.startswith(("ENABLE_CHANNELRX_", "ENABLE_FEATURE_"))},
                         {"BUILD_GUI", "BUILD_SERVER", "BUILD_SHARED_LIBS", "HIDE_CONSOLE", "RX_SAMPLE_24BIT", "ENABLE_AIRSPYHF",
                          "ENABLE_RTLSDR", "ENABLE_SOAPYSDR", "ENABLE_CHANNELRX", "ENABLE_FEATURE"})
        self.assertTrue(all(v == "OFF" for k, v in options.items() if k.startswith(("ENABLE_CHANNELTX", "ENABLE_CHANNELMIMO"))))
        for name in ("ENABLE_CHANNELTX", "ENABLE_CHANNELMIMO", "BUILD_BENCH", "ENABLE_LIMESUITE", "ENABLE_USRP", "ENABLE_LIBUNWIND",
                     "ENABLE_FEATURE_SATELLITETRACKER", "ENABLE_FEATURE_STARTRACKER", "ENABLE_FEATURE_SKYMAP", "ENABLE_FEATURE_MORSEDECODER",
                     "ENABLE_FEATURE_DENOISER", "ENABLE_CHANNELRX_DEMODINMARSAT", "ENABLE_QT6"):
            self.assertEqual(options[name], "OFF", name)

    def test_hook_and_runtime_check_carry_the_same_sets_and_the_lease_command(self):
        for name in ("GUI_PLUGINS", "SERVER_PLUGINS", "CORE_LIBRARIES"):
            self.assertEqual(getattr(check_recipe, name), getattr(runtime_check, name), name)
        template = (PROJECT / "software/systemd/srrx-lease-sdrangelsrv@.service").read_text(encoding="utf-8")
        starts = [line.split("=", 1)[1].split() for line in template.splitlines() if line.startswith("ExecStart=")]
        self.assertEqual(starts, [list(runtime_check.LEASE_ARGV)])
        self.assertEqual(runtime_check.LEASE_ARGV[2:4], ("-a", "127.0.0.1"))
        self.assertNotIn("--soapy", runtime_check.LEASE_ARGV)  # Soapy (the Lime path) stays unloaded while Lime is disabled
        self.assertTrue({"libdemodnavtex.so", "libdemodrtty.so", "libdemodpacket.so"}.isdisjoint(check_recipe.GUI_PLUGINS))
        self.assertTrue({"libdemodnavtexsrv.so", "libdemodrttysrv.so", "libdemodpacketsrv.so"} <= check_recipe.SERVER_PLUGINS)

    def test_policy_allowlist_equals_the_built_plugin_set_and_the_deny_layer_is_clean(self):
        policy = selftest.load_policy(PROJECT / "deployment/receive-only-policy.json")["components"]["sdrangel"]
        allow, deny, present = set(policy["allow_plugins"]), policy["deny_tokens"], set()
        for base in check_recipe.GUI_PLUGINS | check_recipe.SERVER_PLUGINS:
            name = selftest._plugin_name(base)  # the RX-02 matching of selftest.check_02
            matched = {name, name[5:] if name.startswith("input") else name, name[7:] if name.startswith("feature") else name} & allow
            self.assertTrue(matched, base)
            self.assertFalse([t for t in deny if t in name], base)
            present |= matched
        self.assertEqual(present, allow)
        self.assertEqual(policy["install_prefix"], "opt/sdrangel")
        self.assertEqual(policy["plugin_dirs"][0], "opt/sdrangel/lib/sdrangel")
        for name in ("sigmffileinput", "satellitetracker", "startracker", "skymap", "denoiser", "morsedecoder", "soapysdrinput"):
            self.assertNotIn(name, allow)

    def test_patch_removes_exactly_the_reviewed_subdirectories(self):
        text = (PROJECT / "deployment/patches/sdrangel-rx-only.patch").read_text(encoding="utf-8")
        targets = set(json.loads((PROJECT / "deployment/patches/target-hashes.json").read_text(encoding="utf-8"))["sdrangel"])
        self.assertEqual(set(build_recipe.patch_paths(text, 1)), targets)
        removed = [l[1:].strip() for l in text.splitlines() if l.startswith("-") and not l.startswith("---")]
        added = [l[1:].strip() for l in text.splitlines() if l.startswith("+") and not l.startswith("+++")]
        self.assertEqual(sorted(l for l in removed if l.startswith("add_subdirectory(")),
                         sorted("add_subdirectory(%s)" % n for n in ("samplemimo", "samplesink", "localinput", "audioinput", "kiwisdr",
                                                                    "remotetcpinput", "modemm17", "modemmeshtastic", "modemmeshcore", "wdsp")))
        self.assertFalse([l for l in added if "add_subdirectory(" in l])
        self.assertEqual(sorted(l for l in added if l.startswith("if (")),
                         ["if (ENABLE_CHANNELRX_%s AND SERVER_MODE)" % n for n in ("DEMODNAVTEX", "DEMODPACKET", "DEMODRTTY")])

    @unittest.skipUnless(_symlinks_work(), "symlinks need privileges on this host")
    def test_package_hook_links_the_binaries_and_writes_the_unsigned_rx02_manifest(self):
        with tempfile.TemporaryDirectory(prefix="srrx-sdr-hook-") as temporary:
            root = Path(temporary) / "destdir"
            prefix = install_tree(root)
            out = Path(temporary) / "hook.json"
            result = check_recipe.package(root, out)
            self.assertTrue(result["ok"], result)
            self.assertEqual(os.readlink(root / "usr/bin/sdrangelsrv"), "../../opt/sdrangel/bin/sdrangelsrv")
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual((data["status"], data["signature"], data["manifest"]["status"]), ("OPEN_UNSIGNED", None, "OPEN"))
            files, modules = deploy.build_inventory(prefix)
            self.assertEqual((data["manifest"]["files"], data["manifest"]["allowed_modules"]), (files, sorted(modules)))
            self.assertEqual(runtime_check.prefix_manifest(prefix), data["manifest"])  # the runtime check walks alike
            self.assertEqual(data["record_digests"]["rx02_manifest_sha256"], hashlib.sha256(runtime_check.canonical(data["manifest"])).hexdigest())
            self.assertEqual(data["record_digests"]["rx02_manifest_files"], len(files))
            links = {str(root / "usr/bin/sdrangelsrv"): prefix / "bin/sdrangelsrv", str(root / "usr/bin/sdrangel"): prefix / "bin/sdrangel"}
            self.assertEqual(runtime_check.installed_findings(prefix, links), [])
            again = check_recipe.package(root, out)
            self.assertFalse(again["ok"])  # a second run finds usr/ and refuses

    def test_package_hook_refuses_any_other_layout(self):
        cases = {"extra Tx plugin": dict(extra=["lib/sdrangel/plugins/libmodam.so"]),
                 "missing text decoder": dict(missing=["lib/sdrangel/pluginssrv/libdemodnavtexsrv.so"]),
                 "core library in lib/sdrangel": dict(extra=["lib/sdrangel/libsdrbase.so"]),
                 "unlisted library": dict(extra=["lib/libmodemm17.so"]),
                 "stray ELF": dict(extra=["share/sdrangel/helper"])}
        for label, kwargs in cases.items():
            with tempfile.TemporaryDirectory(prefix="srrx-sdr-bad-") as temporary:
                install_tree(Path(temporary), **kwargs)
                findings = check_recipe.check_tree(Path(temporary))
                self.assertTrue(findings, label)
        with tempfile.TemporaryDirectory(prefix="srrx-sdr-top-") as temporary:
            install_tree(Path(temporary))
            (Path(temporary) / "etc").mkdir()
            self.assertIn("install tree top level is not only opt/: etc,opt", check_recipe.check_tree(Path(temporary)))
            self.assertEqual(runtime_check.installed_findings(Path(temporary) / "opt/sdrangel", {}), [])


class RuntimeCheckTests(unittest.TestCase):
    """The comparisons runtime_check.py applies to the REST answers, the sockets and the log."""

    good = {"summary": {"appname": "SDRangelSrv", "version": "7.27.2"},
            "channels_rx": {"channelcount": 16, "channels": [{"id": i} for i in sorted(runtime_check.RX_CHANNELS)]},
            "channels_tx": {"channelcount": 0}, "channels_mimo": {"channelcount": 0},
            "features": {"featurecount": 3, "features": [{"id": i} for i in sorted(runtime_check.FEATURES)]},
            "devices_rx": {"devicecount": 2, "devices": [{"hwType": "FileInput"}, {"hwType": "TestSource"}]},
            "devices_tx": {"devicecount": 0}, "devices_mimo": {"devicecount": 0}}

    def test_rest_answers(self):
        self.assertEqual(runtime_check.rest_findings(self.good), [])
        bad = copy.deepcopy(self.good)
        bad["channels_tx"] = {"channelcount": 1, "channels": [{"id": "NFMMod"}]}
        bad["channels_rx"]["channels"].append({"id": "DSDDemod"})
        bad["devices_rx"]["devices"].append({"hwType": "KiwiSDR"})
        findings = runtime_check.rest_findings(bad)
        self.assertEqual(len(findings), 3, findings)
        self.assertTrue(runtime_check.rest_findings(dict(self.good, summary={"appname": "SDRangel", "version": "7.27.2"})))

    def test_sockets_must_be_loopback(self):
        loopback_v4 = ["0:", "0100007F:1F9B", "00000000:0000", "0A"]
        any_v4 = ["1:", "00000000:1F9B", "00000000:0000", "0A"]
        loopback_v6 = ["0:", "00000000000000000000000001000000:1F9B", "0" * 32 + ":0000", "0A"]
        with tempfile.TemporaryDirectory(prefix="srrx-proc-") as temporary:
            for name, rows in (("tcp", [loopback_v4]), ("tcp6", [loopback_v6]), ("udp", []), ("udp6", [])):
                (Path(temporary) / name).write_text("header\n" + "".join(" ".join(r) + "\n" for r in rows), encoding="ascii")
            sockets = runtime_check.bound_sockets(temporary)
            self.assertEqual(sockets, [("tcp", "127.0.0.1", 8091), ("tcp6", "0000:0000:0000:0000:0000:0000:0000:0001", 8091)])
            self.assertEqual(runtime_check.socket_findings(sockets), [])
            (Path(temporary) / "tcp").write_text("header\n" + " ".join(any_v4) + "\n", encoding="ascii")
            self.assertTrue(runtime_check.socket_findings(runtime_check.bound_sockets(temporary)))
        self.assertTrue(runtime_check.is_loopback("0000:0000:0000:0000:0000:ffff:7f00:0001"))
        self.assertFalse(runtime_check.is_loopback("0000:0000:0000:0000:0000:0000:0000:0000"))
        self.assertEqual(runtime_check.socket_findings([]), ["no listening TCP socket on port 8091"])
        self.assertEqual(runtime_check.socket_findings([], require_listen=False), [])  # loopback down: nothing to reach
        self.assertTrue(runtime_check.socket_findings([("udp", "0.0.0.0", 5353)], require_listen=False))

    def test_loopback_state_from_sysfs_flags(self):
        with tempfile.TemporaryDirectory(prefix="srrx-lo-") as temporary:
            flags = Path(temporary) / "flags"
            for text, up in (("0x8\n", False), ("0x9\n", True), ("0x10049", True), ("junk", False)):
                flags.write_text(text, encoding="ascii")
                self.assertEqual(runtime_check.loopback(flags)["up"], up, text)
            self.assertEqual(runtime_check.loopback(Path(temporary) / "missing"), {"flags": None, "up": False})

    def test_log_names_the_loaded_plugins(self):
        lines = ["2026-11-07 12:00:00.000 (I) PluginManager::loadPluginsDir: loaded plugin %s" % n
                 for n in sorted(runtime_check.SERVER_PLUGINS - {runtime_check.SOAPY_PLUGIN})]
        lease = "\n".join(lines + ["(I) PluginManager::loadPluginsDir: Soapy SDR disabled skipping libinputsoapysdrsrv.so"])
        self.assertEqual(runtime_check.log_findings(lease, soapy=False)[0], [])
        self.assertTrue(runtime_check.log_findings(lease, soapy=True)[0])  # --soapy must load it
        soapy = "\n".join(lines + ["(I) PluginManager::loadPluginsDir: loaded plugin libinputsoapysdrsrv.so"])
        self.assertEqual(runtime_check.log_findings(soapy, soapy=True)[0], [])
        self.assertTrue(runtime_check.log_findings(soapy + "\n(I) PluginManager::loadPluginsDir: loaded plugin libmodamsrv.so", soapy=True)[0])


if __name__ == "__main__":
    unittest.main()
