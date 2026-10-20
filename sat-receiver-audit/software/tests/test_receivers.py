import copy
import ctypes as C
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from srrx.receivers import RTLReceiver, ControlGuard, load_driver_record, validate_tuning


def ready():
    return {"ok": True, "data": {"mode": "HARDWARE", "hardware_qualified": True,
        "live_identity_verified": True, "configured": True, "last_error": None,
        "session": "session-17", "pico": {"state": "ACTIVE", "mcp_reset": False},
        "policy": {"armed": True, "commissioned": True, "pico_active": True,
                   "fault": None, "outputs": {"EN_RTLA": True}}}}


class Function:
    def __init__(self, fn):
        self.fn = fn
    def __call__(self, *args):
        return self.fn(*args)


class FakeRTL:
    def __init__(self, serials=("307A",)):
        self.serials, self.calls = serials, []
        self.center, self.rate = 0, 0
        for name in ("rtlsdr_get_device_count", "rtlsdr_get_device_usb_strings", "rtlsdr_open",
                     "rtlsdr_close", "rtlsdr_get_usb_strings", "rtlsdr_set_bias_tee",
                     "rtlsdr_set_direct_sampling", "rtlsdr_set_center_freq", "rtlsdr_get_center_freq",
                     "rtlsdr_set_sample_rate", "rtlsdr_get_sample_rate", "rtlsdr_set_tuner_gain_mode",
                     "rtlsdr_set_agc_mode", "rtlsdr_reset_buffer", "rtlsdr_read_sync"):
            setattr(self, name, Function(lambda *a, n=name: self.invoke(n, a)))
    def invoke(self, name, args):
        self.calls.append((name, args))
        if name == "rtlsdr_get_device_count": return len(self.serials)
        if name == "rtlsdr_get_device_usb_strings": args[3].value = self.serials[args[0]].encode()
        if name == "rtlsdr_open": C.cast(args[0], C.POINTER(C.c_void_p))[0] = 307
        if name == "rtlsdr_get_usb_strings": args[3].value = b"307A"
        if name == "rtlsdr_set_center_freq": self.center = args[1]
        if name == "rtlsdr_set_sample_rate": self.rate = args[1]
        if name == "rtlsdr_get_center_freq": return self.center
        if name == "rtlsdr_get_sample_rate": return self.rate
        if name == "rtlsdr_read_sync":
            a = np.tile(np.array([255, 0], dtype=np.uint8), 8192)
            C.memmove(args[1], a.ctypes.data, len(a))
            C.cast(args[3], C.POINTER(C.c_int))[0] = len(a)
        return 0


class ReceiverTests(unittest.TestCase):
    def test_rtl_binding_selects_unique_serial_and_only_disables_bias(self):
        lib = FakeRTL()
        rx = RTLReceiver({"serial": "307A", "library_path": "/fixture/lib.so"}, 100000000, 1024000,
                         loader=lambda _: lib)
        a = rx.read()
        self.assertEqual(a.shape, (8192,))
        self.assertTrue(np.allclose(a, 1-1j))
        rx.close(); rx.close()
        self.assertEqual([a[1] for n, a in lib.calls if n == "rtlsdr_set_bias_tee"], [0, 0])
        self.assertEqual(sum(n == "rtlsdr_close" for n, _ in lib.calls), 1)
        self.assertFalse(any("eeprom" in n or "tx" in n for n, _ in lib.calls))

    def test_ambiguous_or_absent_serial_does_not_open(self):
        for serials in [("307A", "307A"), ("other",)]:
            lib = FakeRTL(serials)
            with self.assertRaises(OSError):
                RTLReceiver({"serial": "307A", "library_path": "/fixture/lib.so"}, 100000000, 1024000,
                            loader=lambda _: lib)
            self.assertFalse(any(n == "rtlsdr_open" for n, _ in lib.calls))

    def test_guard_never_arms_or_renews_and_latches_session(self):
        reply, calls = ready(), []
        def transport(command):
            calls.append(command)
            return reply
        guard = ControlGuard(transport, "RTLA")
        guard.check()
        reply["data"]["session"] = "new-session"
        with self.assertRaises(RuntimeError): guard.check()
        self.assertEqual(calls, [{"op": "status"}, {"op": "status"}])

    def test_guard_rejects_every_missing_readiness_boundary(self):
        mutations = [("mode", "SIMULATION"), ("hardware_qualified", False),
                     ("live_identity_verified", False), ("configured", False), ("last_error", "fault")]
        for k, v in mutations:
            reply = ready(); reply["data"][k] = v
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()
        for k, v in [("armed", False), ("commissioned", False), ("pico_active", False), ("fault", "fault")]:
            reply = ready(); reply["data"]["policy"][k] = v
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()
        for path in [("pico", "mcp_reset", True), ("pico", "state", "TRIPPED")]:
            reply = ready();reply["data"][path[0]][path[1]] = path[2]
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()

    def test_explicit_tuning_ranges_and_no_lime_fallback(self):
        validate_tuning("rtl", 100000000, 1024000)
        validate_tuning("airspyhf", 10000000, 768000)
        for args in [("rtl", 100000000, 3200000), ("airspyhf", 40000000, 768000),
                     ("lime", 100000000, 56000000), ("rtl", True, 1024000)]:
            with self.assertRaises(ValueError):validate_tuning(*args)

    def test_driver_must_be_accepted_artifact_and_bind_library_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); library = root / "lib.so"; library.write_bytes(b"not an ELF; validation fixture only")
            record = {"v": 1, "backend": "rtl", "branch": "RTLA", "serial": "307A",
                      "library_path": str(library), "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
                      "rx_only_reviewed": True, "bias_disabled_verified": True, "dependencies_reviewed": True}
            p = root / "driver.json";p.write_text(json.dumps(record))
            accepted = {"gates": {"E5-fixture": {"evidence": {"artifacts": []}}}}
            with self.assertRaises(ValueError):load_driver_record(p, root, accepted)
            accepted["gates"]["E5-fixture"]["evidence"]["artifacts"] = [{"path": "driver.json", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}]
            self.assertEqual(load_driver_record(p, root, accepted)["serial"], "307A")
            library.write_bytes(b"changed")
            with self.assertRaises(ValueError):load_driver_record(p, root, accepted)


class CaptureTests(unittest.TestCase):
    def test_failed_hardware_guard_never_constructs_worker(self):
        from srrx.labrx import run_capture
        with patch("srrx.labrx.WorkerSource") as worker:
            with self.assertRaises(RuntimeError):
                run_capture(record={"backend": "rtl", "branch": "RTLA"}, transport=lambda _: {"ok": False},
                            source_factory=worker)
            worker.assert_not_called()

    def test_simulation_writes_masked_spectrum_only(self):
        from srrx.labrx import run_capture
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=run_capture(center_hz=300000000, frames=2, output=root/"latest.json", survey=root/"survey.jsonl")
            self.assertFalse(result["raw_iq_persisted"])
            self.assertEqual(result["frames"],2)
            frame=json.loads((root/"latest.json").read_text())
            self.assertTrue(all(v is None for v in frame["power_dbfs"]))
            self.assertEqual(set(p.name for p in root.iterdir()), {"latest.json", "survey.jsonl"})

    def test_worker_closed_and_power_off_requested_after_failure(self):
        from srrx.labrx import run_capture
        calls=[]
        class Source:
            closed=False
            def read(self,guard):raise OSError("fixture USB loss")
            def close(self):self.closed=True
        source=Source()
        def transport(request):calls.append(request);return ready()
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"}, transport=transport,
                        source_factory=lambda *a:source)
        self.assertTrue(source.closed)
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})

    def test_constructor_failure_still_requests_branch_off(self):
        from srrx.labrx import run_capture
        calls=[]
        def transport(request):calls.append(request);return ready()
        def failing(*args):raise OSError("fixture Process.start failed")
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"},transport=transport,source_factory=failing)
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})

    def test_close_failure_cannot_skip_branch_off(self):
        from srrx.labrx import run_capture
        calls=[]
        class Source:
            def read(self,guard):raise OSError("fixture read error")
            def close(self):raise OSError("fixture close error")
        def transport(request):calls.append(request);return ready()
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"},transport=transport,source_factory=lambda *a:Source())
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})
