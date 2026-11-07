"""labd's GNSS time orchestration around gnss_reset with fake effects, the simulated Engine
and real AF_UNIX sockets for the nonblocking request helper.

Simulation only: no LC76G, gpsd, chrony or PPS signal. Selecting PPS on a real Q6A
(chrony selects PPS within 10 min of a 3D fix, build/07:502) stays a Q6A gate.
"""
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest

from srrx import gnss_orchestrator as orchestrator
from srrx.engine import Engine
from srrx.gnss_orchestrator import (ConfigRun, Done, GnssOrchestrator, JamLatchFile, LinuxGnssEffects,
                                    JAMMING_FRESH_MS, POLL_MS, QUALIFY_MS, RETRY_MS, WATCH_LOST_MS, UnixLineRequest)
from srrx.hardware import SimHardware
from srrx.link import SimLink
from srrx.policy import GNSS_RESET_GATE

PROJECT = Path(__file__).resolve().parents[2]


class Later:
    def __init__(self, result, ready_ms):
        self.result, self.ready_ms, self.cancelled = result, ready_ms, False

    def poll(self, now_ms):
        return self.result if now_ms >= self.ready_ms else None

    def cancel(self):
        self.cancelled = True


def snapshot(qualified=True, jamming=False, status=None, reports=5, age_ms=200):
    # One unnamed synthetic point: the orchestrator must never copy it into its status.
    return {"ok": True, "data": {"schema_version": 1, "qualified_fix": qualified,
                                 "jamming": {"active": jamming,
                                             "status": (2 if jamming else 1) if status is None else status,
                                             "source": "PAIRSPF", "error": None, "reports": reports,
                                             "age_ms": age_ms},
                                 "location": {"lat": 0.125, "lon": 0.375, "mode": 3, "satellites": 8}}}


class FakeEffects:
    def __init__(self, log):
        self.log = log
        self.invalidate_ok = True
        self.noselect_ok = self.select_ok = True
        self.config_result = {"ok": True, "readback_match": True, "wrote": False, "version": "TESTVER1", "error": None}
        self.config_delay_ms = 0
        self.reply = snapshot()
        self.now = 0
        self.jobs = []

    def invalidate(self, reason, now_ms):
        self.log.append(("invalidate", reason, now_ms))
        return Done({"ok": self.invalidate_ok})

    def pps(self, select, now_ms):
        self.log.append(("pps", select, now_ms))
        ok = self.select_ok if select else self.noselect_ok
        return Done({"ok": True, "command": "PPS_SELECT" if select else "PPS_NOSELECT"} if ok
                    else {"ok": False, "error": "TIMEGATE_UNREACHABLE"})

    def snapshot(self, now_ms):
        self.log.append(("snapshot", None, now_ms))
        return Done(self.reply)

    def config(self, now_ms):
        self.log.append(("config", None, now_ms))
        job = Later(self.config_result, now_ms + self.config_delay_ms)
        self.jobs.append(job)
        return job


class Harness:
    def __init__(self, mode="gpsd", latch=None):
        self.log = []
        self.effects = FakeEffects(self.log)
        self.orch = GnssOrchestrator(self.effects, mode=mode, latch=latch)
        self.now = 0
        self.reset = {"state": "IDLE", "release_ms": None}
        self.release_at = None
        self.pulse_result = {"ok": True, "state": "ASSERTED"}

    def pulse(self, owner, value):
        self.log.append(("pulse", (owner, value), self.now))
        if self.pulse_result.get("ok"):
            self.reset, self.release_at = {"state": "ASSERTED", "release_ms": None}, self.now + 200
        return self.pulse_result

    def advance(self, ms, step=20):
        end = self.now + ms
        while self.now < end:
            self.now += step
            if self.reset["state"] == "ASSERTED" and self.now >= self.release_at:
                self.reset = {"state": "IDLE", "release_ms": self.now}
            self.orch.tick(self.now, dict(self.reset), self.pulse)

    def kinds(self, skip=("snapshot",)):
        return [(kind, arg) if kind in ("pps", "invalidate") else kind for kind, arg, unused in self.log if kind not in skip]

    def selected(self):
        self.advance(QUALIFY_MS + 3 * POLL_MS)
        return self.orch.state == "SELECTED"

    def reset_released(self):
        """Accept a gnss_reset and advance past its proven release."""
        reply = self.orch.request_reset("uid:1000", None, self.now)
        self.advance(260)
        return reply


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()

    def test_boot_reads_back_then_selects_pps_only_after_a_held_qualified_fix(self):
        self.h.advance(20)
        self.assertEqual(self.h.kinds(), [("pps", False), "config"])
        self.assertEqual(self.h.orch.state, "AWAIT_FIX")
        self.assertFalse(self.h.orch.status()["pps_gate_open"])
        self.h.advance(QUALIFY_MS - 2 * POLL_MS)
        self.assertNotIn(("pps", True), self.h.kinds())  # not yet held for QUALIFY_MS
        self.h.advance(3 * POLL_MS)
        self.assertEqual(self.h.kinds(), [("pps", False), "config", ("pps", True)])
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["pps_selected"], status["rtc_stale"], status["pps_gate_open"]),
                         ("SELECTED", True, False, True))
        self.assertEqual((status["jamming_active"], status["jamming_visible"], status["reset_required"]),
                         (False, True, False))
        self.assertEqual(status["config"]["version"], "TESTVER1")
        self.assertFalse(status["automatic_reset"])
        self.assertNotIn("time_trusted", status)  # labd's gate, not chrony's selection (chronyc sources)

    def test_one_unqualified_or_missing_sample_restarts_the_qualification_window(self):
        self.h.advance(20 + QUALIFY_MS - 2 * POLL_MS)
        self.h.effects.reply = snapshot(qualified=False)
        self.h.advance(POLL_MS)
        self.h.effects.reply = {"ok": False, "error": "LOCATIOND_UNREACHABLE"}
        self.h.advance(POLL_MS)
        self.h.effects.reply = snapshot()
        self.h.advance(QUALIFY_MS - POLL_MS)
        self.assertNotIn(("pps", True), self.h.kinds())
        self.h.advance(2 * POLL_MS)
        self.assertIn(("pps", True), self.h.kinds())

    def test_pps_needs_a_fresh_good_jamming_report_not_just_a_qualified_fix(self):
        # gpsd "raw":1 passthrough or $PAIRSPF output may not work (QEMU/Q6A items): no report, no PPS.
        for case, reply in (("no report yet", snapshot(reports=0, age_ms=None)),
                            ("stale report", snapshot(age_ms=JAMMING_FRESH_MS + 1)),
                            ("status 0 unknown", snapshot(status=0)), ("status True", snapshot(status=True)),
                            ("no jamming field", {"ok": True, "data": {"schema_version": 1, "qualified_fix": True}})):
            with self.subTest(case):
                h = Harness()
                h.effects.reply = reply
                h.advance(QUALIFY_MS * 3)
                self.assertEqual(h.orch.state, "AWAIT_FIX")
                self.assertNotIn(("pps", True), h.kinds())
                self.assertFalse(h.orch.status()["jamming_visible"])
                h.effects.reply = snapshot()
                self.assertTrue(h.selected())

    def test_reset_deselects_pps_before_the_pulse_and_reselects_after_config_and_fix(self):
        self.assertTrue(self.h.selected())
        del self.h.log[:]
        reply = self.h.orch.request_reset("uid:1000", {"width_ms": 200}, self.h.now)
        self.assertEqual(reply["state"], "ACCEPTED")
        self.h.advance(20)
        self.assertEqual(self.h.kinds(), [("invalidate", "GNSS_RESET"), ("pps", False), "pulse"])
        self.assertEqual(self.h.log[2][1], ("uid:1000", {"width_ms": 200}))  # the same owner's checked pulse
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["pps_selected"], status["rtc_stale"]), ("RESET_RELEASE", False, True))
        self.h.advance(200)
        self.assertEqual(self.h.kinds()[-1], "config")  # only after the proven release
        self.h.advance(QUALIFY_MS + 3 * POLL_MS)
        self.assertEqual(self.h.kinds(), [("invalidate", "GNSS_RESET"), ("pps", False), "pulse", "config", ("pps", True)])
        self.assertEqual(self.h.orch.state, "SELECTED")
        self.assertEqual(sum(kind == "pulse" for kind in self.h.kinds()), 1)

    def test_no_pulse_without_a_confirmed_noselect(self):
        self.assertTrue(self.h.selected())
        self.h.effects.noselect_ok = False
        self.assertTrue(self.h.orch.request_reset("uid:1000", None, self.h.now)["ok"])
        self.h.advance(RETRY_MS * 4 + 100)
        self.assertNotIn("pulse", self.h.kinds())
        status = self.h.orch.status()
        # The plan ended without a pulse; PPS may still be selected, so only the noselect is retried.
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"], status["pps_gate_open"]),
                         ("PPS_NOSELECT_FAULT", "PPS_NOSELECT_FAILED", None, False))
        self.assertEqual(self.h.kinds().count(("pps", False)), 2 + 4)  # boot, the plan's own, 4 retries
        self.h.effects.noselect_ok = True
        self.h.advance(RETRY_MS)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"]),
                         ("FAILED", "PPS_NOSELECT_FAILED", False))
        self.h.advance(RETRY_MS * 3)
        self.assertEqual(self.h.kinds().count(("pps", False)), 2 + 5)  # confirmed: no further retry
        self.assertNotIn("pulse", self.h.kinds())

    def test_refused_pulse_still_reads_back_and_reselects_without_a_release_step(self):
        self.assertTrue(self.h.selected())
        self.h.pulse_result = {"ok": False, "error": "GNSS_RESET_SPACING: 30 s after the previous release required"}
        self.h.orch.request_reset("uid:1000", None, self.h.now)
        self.h.advance(40)
        status = self.h.orch.status()
        self.assertIn("GNSS_RESET_REFUSED", status["warnings"])
        self.assertTrue(status["last_error"].startswith("GNSS_RESET_REFUSED: GNSS_RESET_SPACING"))
        self.assertEqual(self.h.kinds()[-1], "config")
        self.assertTrue(self.h.selected())

    def test_unproven_release_and_failed_config_keep_pps_deselected(self):
        self.assertTrue(self.h.selected())
        self.h.orch.request_reset("uid:1000", None, self.h.now)
        self.h.advance(20)
        self.h.reset = {"state": "RELEASE_UNCONFIRMED", "release_ms": None}
        self.h.release_at = 10 ** 12
        self.h.advance(40)
        self.assertEqual((self.h.orch.state, self.h.orch.last_error), ("FAILED", "GNSS_RESET_RELEASE_UNCONFIRMED"))
        self.assertNotIn("config", self.h.kinds()[2:])
        h = Harness()
        h.effects.config_result = {"ok": False, "readback_match": False, "error": "GNSS_CONFIG_NO_SENTENCE"}
        h.advance(QUALIFY_MS * 3)
        self.assertEqual((h.orch.state, h.orch.last_error), ("FAILED", "GNSS_CONFIG_FAILED: GNSS_CONFIG_NO_SENTENCE"))
        self.assertNotIn(("pps", True), h.kinds())
        self.assertEqual(h.orch.status()["pps_selected"], False)

    def test_config_timeout_and_fix_timeout_end_without_any_retry(self):
        h = Harness()
        h.effects.config_delay_ms = 10 ** 9
        h.advance(orchestrator.CONFIG_TIMEOUT_MS + 1000, step=500)
        self.assertEqual((h.orch.state, h.orch.last_error), ("FAILED", "GNSS_CONFIG_TIMEOUT"))
        self.assertTrue(h.effects.jobs[0].cancelled)
        h = Harness()
        h.effects.reply = snapshot(qualified=False)
        h.advance(orchestrator.FIX_TIMEOUT_MS + 2000, step=500)
        self.assertEqual((h.orch.state, h.orch.last_error), ("FIX_TIMEOUT", "GNSS_FIX_TIMEOUT"))
        self.assertEqual(h.kinds(), [("pps", False), "config"])  # no automatic re-RESET or config retry
        h.advance(60000, step=500)
        self.assertEqual(h.kinds(), [("pps", False), "config"])

    def test_jamming_latch_needs_a_proven_reset_and_never_a_mere_config(self):
        self.assertTrue(self.h.selected())
        self.h.effects.reply = snapshot(jamming=True)
        self.h.advance(POLL_MS + 20)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"], status["jamming_seen"],
                          status["reset_required"], status["jamming_active"]),
                         ("JAMMED", "GNSS_JAMMING", False, True, True, True))
        self.assertEqual(self.h.kinds()[-1], ("pps", False))
        self.h.advance(POLL_MS * 5)
        self.assertEqual(self.h.kinds().count(("pps", False)), 2)  # a held flag is not deselected again
        self.h.effects.reply = snapshot()
        self.h.advance(QUALIFY_MS * 2)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["jamming_active"]), ("JAMMED", False))  # no reselect by itself
        self.assertNotIn("pulse", self.h.kinds())
        # build/07:484: after the flag, a cold restart and the settings again before PPS is trusted.
        reply = self.h.orch.request_config("uid:1000", self.h.now)
        self.assertFalse(reply["ok"])
        self.assertTrue(reply["error"].startswith("GNSS_JAMMED_RESET_REQUIRED"))
        self.assertEqual(self.h.orch.state, "JAMMED")
        self.h.reset_released()
        self.assertFalse(self.h.orch.status()["reset_required"])  # cleared by the proven release
        self.assertTrue(self.h.selected())
        self.assertEqual(self.h.kinds()[-5:], [("invalidate", "GNSS_RESET"), ("pps", False), "pulse", "config",
                                               ("pps", True)])
        self.assertEqual(sum(kind == "pulse" for kind in self.h.kinds()), 1)
        self.assertEqual([e["event"] for e in self.h.orch.events].count("GNSS_JAM_LATCH_CLEARED"), 1)

    def test_a_refused_or_unproven_reset_keeps_the_latch(self):
        self.h.effects.reply = snapshot(jamming=True)
        self.h.advance(40)
        self.assertEqual(self.h.orch.state, "JAMMED")
        self.h.effects.reply = snapshot()
        self.h.pulse_result = {"ok": False, "error": "GNSS_RESET_RATE_LIMIT: at most 3 pulses per 15 min"}
        before = len(self.h.kinds())
        self.assertTrue(self.h.orch.request_reset("uid:1000", None, self.h.now)["ok"])
        self.h.advance(40)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["reset_required"]), ("JAMMED", True))
        self.assertTrue(status["last_error"].startswith("GNSS_RESET_REFUSED: GNSS_RESET_RATE_LIMIT"))
        self.assertEqual(self.h.kinds()[before:], [("invalidate", "GNSS_RESET"), ("pps", False), "pulse"])  # no config
        self.h.pulse_result = {"ok": True, "state": "ASSERTED"}
        self.h.orch.request_reset("uid:1000", None, self.h.now)
        self.h.advance(20)
        self.h.reset = {"state": "RELEASE_UNCONFIRMED", "release_ms": None}
        self.h.release_at = 10 ** 12
        self.h.advance(40)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["reset_required"]), ("FAILED", True))
        self.assertFalse(self.h.orch.request_config("uid:1000", self.h.now)["ok"])

    def test_a_reset_while_the_flag_still_holds_latches_again(self):
        self.assertTrue(self.h.selected())
        self.h.effects.reply = snapshot(jamming=True)  # locationd holds the flag 60 s after the last report
        self.h.advance(POLL_MS + 20)
        self.h.reset_released()
        self.h.advance(POLL_MS * 2)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["reset_required"]), ("JAMMED", True))
        self.assertNotIn(("pps", True), self.h.kinds()[3:])  # after the boot select

    def test_the_latch_survives_a_labd_restart_and_boot_never_selects_pps(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-jam-latch-")
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "jamming-latch.json"
        first = Harness(latch=JamLatchFile(path))
        self.assertTrue(first.selected())
        self.assertFalse(path.exists())
        first.effects.reply = snapshot(jamming=True)
        first.advance(POLL_MS + 20)
        self.assertEqual(json.loads(path.read_text()), {"reset_required": True, "schema_version": 1})
        # labd crashes or is restarted (systemctl restart srrx): the boot plan honours the file.
        again = Harness(latch=JamLatchFile(path))
        self.assertTrue(again.orch.status()["reset_required"])
        again.advance(QUALIFY_MS * 3)
        status = again.orch.status()
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"], status["latch_error"]),
                         ("JAMMED", "GNSS_JAMMED_RESET_REQUIRED", False, None))
        self.assertEqual(again.kinds(), [("pps", False)])  # deselected; no config, no select
        self.assertFalse(again.orch.request_config("uid:1000", again.now)["ok"])
        again.reset_released()
        self.assertFalse(path.exists())
        self.assertTrue(again.selected())
        self.assertFalse(Harness(latch=JamLatchFile(path)).orch.status()["reset_required"])

    def test_the_latch_file_fails_closed(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-jam-latch-")
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.assertEqual(JamLatchFile(root / "absent.json").load(), (False, None))
        self.assertEqual(JamLatchFile(root / "missing-dir/latch.json").load(), (True, "GNSS_JAM_LATCH_DIRECTORY_MISSING"))
        for content in (b"", b"{bad", b'{"schema_version":1,"reset_required":false}', b"[1]",
                        b'{"schema_version":2,"reset_required":true}', b'{"x":NaN}', b"x" * 5000):
            with self.subTest(content=content[:40]):
                (root / "odd.json").write_bytes(content)
                self.assertEqual(JamLatchFile(root / "odd.json").load(), (True, "GNSS_JAM_LATCH_UNREADABLE"))
        (root / "dir.json").mkdir()
        self.assertEqual(JamLatchFile(root / "dir.json").load(), (True, "GNSS_JAM_LATCH_UNREADABLE"))
        latch = JamLatchFile(root / "missing-dir/latch.json")
        self.assertFalse(latch.store(True))
        self.assertFalse(latch.store(False))
        h = Harness(latch=latch)
        h.advance(QUALIFY_MS * 2)
        self.assertEqual((h.orch.state, h.orch.status()["latch_error"]), ("JAMMED", "GNSS_JAM_LATCH_DIRECTORY_MISSING"))
        h.reset_released()
        self.assertEqual(h.orch.status()["latch_error"], "GNSS_JAM_LATCH_STORE_FAILED")
        self.assertTrue(h.selected())  # this run saw the proven reset; the next start is latched again

    def test_jamming_while_waiting_for_a_fix_never_selects_and_failed_noselect_retries(self):
        h = Harness()
        h.effects.reply = snapshot(jamming=True)
        h.advance(40)
        self.assertEqual(h.orch.state, "JAMMED")
        self.assertNotIn(("pps", True), h.kinds())
        h = Harness()
        self.assertTrue(h.selected())
        h.effects.noselect_ok = False
        h.effects.reply = snapshot(jamming=True)
        h.advance(POLL_MS + 20)
        self.assertEqual((h.orch.state, h.orch.last_error, h.orch.pps_selected),
                         ("PPS_NOSELECT_JAMMING", "PPS_NOSELECT_FAILED", None))
        before = h.kinds().count(("pps", False))
        h.advance(RETRY_MS + 40)
        self.assertEqual(h.kinds().count(("pps", False)), before + 1)  # keeps trying to stop disciplining
        h.effects.noselect_ok = True
        h.advance(RETRY_MS + 40)
        self.assertEqual(h.orch.state, "JAMMED")

    def test_boot_noselect_failure_is_retried_and_busy_plans_refuse_new_requests(self):
        h = Harness()
        h.effects.noselect_ok = False
        h.advance(RETRY_MS * 2 + 100)
        self.assertEqual(h.kinds().count(("pps", False)), 3)
        self.assertEqual((h.orch.state, h.orch.last_error), ("PPS_NOSELECT", "PPS_NOSELECT_FAILED"))
        h.effects.noselect_ok = True
        h.effects.config_delay_ms = 60000
        h.advance(RETRY_MS)
        self.assertEqual(h.orch.state, "GNSS_CONFIG")
        for request in (lambda: h.orch.request_reset("uid:1000", None, h.now), lambda: h.orch.request_config("uid:1000", h.now)):
            reply = request()
            self.assertFalse(reply["ok"])
            self.assertEqual(reply["error"], "GNSS_ORCHESTRATION_BUSY: GNSS_CONFIG")

    def test_an_operator_plan_replaces_the_endless_boot_noselect_retry(self):
        # timegate, chronyd or the PPS refclock missing: boot keeps retrying, labctl is never locked out.
        h = Harness()
        h.effects.noselect_ok = False
        h.advance(RETRY_MS * 3)
        self.assertEqual(h.orch.step, "noselect")
        reply = h.orch.request_config("uid:1000", h.now)
        self.assertEqual((reply["ok"], reply["orchestration"]), (True, "config"))
        h.advance(40)
        status = h.orch.status()
        # The operator plan fails cleanly (no config without a confirmed noselect) and keeps deselecting.
        self.assertEqual((status["state"], status["last_error"], status["orchestration"]),
                         ("PPS_NOSELECT_FAULT", "PPS_NOSELECT_FAILED", "config"))
        self.assertNotIn("config", h.kinds())
        self.assertTrue(h.orch.request_reset("uid:1000", None, h.now)["ok"])  # the retry is replaceable too
        h.advance(40)
        self.assertNotIn("pulse", h.kinds())
        h.effects.noselect_ok = True
        h.advance(RETRY_MS + 40)
        self.assertEqual((h.orch.state, h.orch.pps_selected), ("FAILED", False))

    def test_status_never_carries_coordinates(self):
        self.assertTrue(self.h.selected())
        text = json.dumps(self.h.orch.status())
        for word in ('"lat"', '"lon"', "0.125", "0.375", "location", "satellites"):  # "latch" is no coordinate
            self.assertNotIn(word, text)

    def test_select_failure_returns_to_the_fix_gate(self):
        h = Harness()
        h.effects.select_ok = False
        h.advance(QUALIFY_MS + 3 * POLL_MS)
        self.assertEqual((h.orch.state, h.orch.last_error), ("AWAIT_FIX", "PPS_SELECT_FAILED"))
        self.assertIsNone(h.orch.pps_selected)  # the failed request may still have reached chronyd
        h.effects.select_ok = True
        h.advance(RETRY_MS + QUALIFY_MS + 3 * POLL_MS)
        self.assertEqual((h.orch.state, h.orch.last_error), ("SELECTED", None))

    def test_a_fix_timeout_after_a_failed_select_deselects_first(self):
        h = Harness()
        h.effects.select_ok = False
        h.advance(QUALIFY_MS + 3 * POLL_MS)
        h.effects.reply = snapshot(qualified=False)
        h.advance(orchestrator.FIX_TIMEOUT_MS + 2000, step=500)
        status = h.orch.status()
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"]),
                         ("FIX_TIMEOUT", "GNSS_FIX_TIMEOUT", False))
        self.assertEqual(h.kinds()[-1], ("pps", False))

    def test_raw_mode_never_selects_pps_because_chrony_gets_no_nmea(self):
        # gpsd stopped: 'refclock SHM 0 refid NMEA' gets no samples and 'lock NMEA' drops every pulse.
        h = Harness(mode="raw")
        h.advance(QUALIFY_MS * 3)
        status = h.orch.status()
        self.assertEqual((status["state"], status["pps_selected"], status["pps_gate_open"], status["rtc_stale"]),
                         ("POSITION_ONLY", False, False, True))
        self.assertIn("RAW_MODE_NO_NMEA_SHM", status["warnings"])
        self.assertEqual(h.kinds(), [("pps", False), "config"])
        reply = h.orch.request_reset("uid:1000", None, h.now)
        self.assertEqual(reply["steps"], ["invalidate", "noselect", "stale", "pulse", "release", "config", "position_only"])
        h.advance(QUALIFY_MS * 3)
        self.assertEqual(h.orch.state, "POSITION_ONLY")
        self.assertNotIn(("pps", True), h.kinds())
        h.effects.reply = snapshot(jamming=True)  # the latch still applies to the receiver itself
        h.advance(POLL_MS + 20)
        self.assertEqual((h.orch.state, h.orch.reset_required), ("JAMMED", True))
        self.assertFalse(h.orch.request_config("uid:1000", h.now)["ok"])

    def test_fault_while_selected_deselects_pps_before_failing(self):
        self.assertTrue(self.h.selected())
        self.h.effects.noselect_ok = False
        self.h.orch.fault("GNSS_ORCHESTRATOR_ERROR: RuntimeError", self.h.now)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["pps_gate_open"]), ("PPS_NOSELECT_FAULT", False))
        self.h.advance(RETRY_MS * 2 + 100)
        self.assertEqual((self.h.orch.state, self.h.orch.pps_selected), ("PPS_NOSELECT_FAULT", None))
        self.h.effects.noselect_ok = True
        self.h.advance(RETRY_MS)
        status = self.h.orch.status()
        self.assertEqual((status["state"], status["last_error"], status["pps_selected"], status["pps_gate_open"]),
                         ("FAILED", "GNSS_ORCHESTRATOR_ERROR: RuntimeError", False, False))
        self.h.effects.reply = snapshot(jamming=True)  # still watched for jamming while FAILED
        self.h.advance(POLL_MS + 20)
        self.assertEqual((self.h.orch.state, self.h.orch.reset_required), ("JAMMED", True))

    def test_lost_snapshots_or_reports_while_selected_deselect_and_requalify(self):
        for case, reply in (("locationd down", {"ok": False, "error": "LOCATIOND_UNREACHABLE"}),
                            ("no fresh jamming report", snapshot(age_ms=JAMMING_FRESH_MS + 500))):
            with self.subTest(case):
                h = Harness()
                self.assertTrue(h.selected())
                h.effects.reply = reply
                h.advance(WATCH_LOST_MS - POLL_MS)
                self.assertEqual(h.orch.state, "SELECTED")  # a short gap is tolerated
                h.advance(2 * POLL_MS + 40)
                status = h.orch.status()
                self.assertEqual((status["state"], status["orchestration"], status["pps_selected"],
                                  status["pps_gate_open"], status["reset_required"]),
                                 ("AWAIT_FIX", "watch", False, False, False))
                self.assertIn("JAMMING_WATCH_LOST", status["warnings"])
                self.assertEqual(h.kinds()[-1], ("pps", False))
                h.effects.reply = snapshot()
                self.assertTrue(h.selected())  # no reset needed: nothing was flagged


class EngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith("DCS_")})
        self.log = []
        self.effects = FakeEffects(self.log)
        self.orch = GnssOrchestrator(self.effects)
        self.engine = Engine(self.hardware, SimLink(PROJECT), simulated=True, gnss=self.orch)
        self.addCleanup(self.engine.close)
        self.now = 0
        self.engine.tick(self.now)

    def advance(self, ms):
        end = self.now + ms
        while self.now < end:
            self.now += 20
            if self.engine.policy.armed and self.now % 1000 == 0:  # as `labctl hold` renews its lease
                self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 5000})["ok"])
            self.engine.tick(self.now)

    def request(self, owner, **fields):
        return self.engine.request(dict(fields, _owner=owner), self.now)

    def arm(self):
        self.assertTrue(self.request("uid:1000", op="arm")["ok"])
        self.advance(800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())

    def test_orchestrated_reset_pulses_after_noselect_and_reselects(self):
        self.arm()
        self.assertEqual(self.engine.status()["gnss"]["state"], "AWAIT_FIX")
        count = len(self.log)
        for value in ({"width_ms": 99}, {"width_ms": 200, "x": 1}):
            reply = self.request("uid:1000", op="gnss_reset", value=value)
            self.assertFalse(reply["ok"])
        self.assertIn("own valid lease", self.request("uid:1001", op="gnss_reset")["error"])
        self.assertEqual(len(self.log), count)  # refused before anything was deselected
        reply = self.request("uid:1000", op="gnss_reset", value={"width_ms": 200})
        self.assertEqual(reply["state"], "ACCEPTED")
        self.assertFalse(self.hardware.outputs[GNSS_RESET_GATE])  # nothing pulses inside the request
        self.advance(20)
        self.assertTrue(self.hardware.outputs[GNSS_RESET_GATE])
        kinds = [kind for kind, unused, unused2 in self.log[count:] if kind != "snapshot"]
        self.assertEqual(kinds, ["invalidate", "pps"])
        self.advance(220)
        self.assertFalse(self.hardware.outputs[GNSS_RESET_GATE])
        self.assertEqual(self.engine.status()["policy"]["gnss_reset"]["last_width_ms"], 200)
        self.advance(QUALIFY_MS + 3 * POLL_MS)
        status = self.engine.status()["gnss"]
        self.assertEqual((status["state"], status["pps_selected"], status["pps_gate_open"]), ("SELECTED", True, True))
        self.assertTrue(self.engine.policy.armed)  # orchestration never touched the power session

    def test_gnss_config_needs_the_lease_and_off_mode_refuses(self):
        self.arm()
        self.assertIn("own valid lease", self.request("uid:1001", op="gnss_config")["error"])
        self.assertTrue(self.request("uid:1000", op="gnss_config")["ok"])
        self.effects.reply = snapshot(jamming=True)
        self.advance(POLL_MS + 40)
        self.assertEqual(self.engine.status()["gnss"]["state"], "JAMMED")
        self.assertIn("GNSS_JAMMED_RESET_REQUIRED", self.request("uid:1000", op="gnss_config")["error"])
        plain = Engine(SimHardware(), SimLink(PROJECT), simulated=True)
        self.addCleanup(plain.close)
        self.assertIn("GNSS_ORCHESTRATION_OFF", plain.request({"op": "gnss_config", "_owner": "uid:1000"}, 0)["error"])
        self.assertIsNone(plain.status()["gnss"])

    def test_orchestrator_errors_never_trip_the_power_policy(self):
        self.arm()
        def broken(now_ms):
            raise RuntimeError("synthetic")
        self.effects.snapshot = broken
        self.advance(POLL_MS * 2)
        status = self.engine.status()
        self.assertEqual(status["gnss"]["state"], "FAILED")
        self.assertEqual(status["gnss"]["last_error"], "GNSS_ORCHESTRATOR_ERROR: RuntimeError")
        self.assertTrue(self.engine.policy.armed)
        self.assertIsNone(status["policy"]["fault"])


class UnixRequestTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-orch-test-")
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "s.sock")
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(self.listener.close)
        self.listener.bind(self.path)
        self.listener.listen(4)

    def serve(self, reply, chunks=1):
        client, unused = self.listener.accept()
        with client:
            request = client.recv(4096)
            data = reply
            step = max(1, len(data) // chunks)
            for start in range(0, len(data), step):
                client.sendall(data[start:start + step])
        return request

    def test_reply_is_read_without_blocking_and_parsed(self):
        job = UnixLineRequest(self.path, b'{"op":"snapshot"}\n', 0, 2000, "LOCATIOND")
        self.assertIsNone(job.poll(10))  # sent, no reply yet: never blocks
        self.assertEqual(self.serve(b'{"ok":true,"data":{}}\n', chunks=3), b'{"op":"snapshot"}\n')
        result = None
        for now in range(20, 2000, 10):
            result = job.poll(now)
            if result is not None:
                break
        self.assertEqual(result, {"ok": True, "data": {}})

    def test_unreachable_timeout_invalid_and_closed_replies_are_codes(self):
        self.assertEqual(UnixLineRequest(self.path + ".missing", b"x\n", 0, 100, "TIMEGATE").poll(0),
                         {"ok": False, "error": "TIMEGATE_UNREACHABLE"})
        job = UnixLineRequest(self.path, b"PPS_SELECT\n", 0, 100, "TIMEGATE")  # in the backlog, never answered
        self.assertIsNone(job.poll(99))
        self.assertEqual(job.poll(100), {"ok": False, "error": "TIMEGATE_TIMEOUT"})
        stale, unused = self.listener.accept()  # drop that abandoned connection from the backlog
        stale.close()
        for reply, code in ((b"[1]\n", "TIMEGATE_REPLY_INVALID"), (b"{bad\n", "TIMEGATE_REPLY_INVALID"),
                            (b"", "TIMEGATE_CLOSED"), (b'{"x":NaN}\n', "TIMEGATE_REPLY_INVALID")):
            with self.subTest(reply=reply):
                job = UnixLineRequest(self.path, b"PPS_SELECT\n", 0, 2000, "TIMEGATE")
                job.poll(0)
                self.serve(reply)
                result = None
                for now in range(1, 2000):
                    result = job.poll(now)
                    if result is not None:
                        break
                self.assertEqual(result, {"ok": False, "error": code})
        job = UnixLineRequest(self.path, b"PPS_SELECT\n", 0, 2000, "TIMEGATE")
        job.cancel()
        self.assertEqual(job.poll(1), {"ok": False, "error": "TIMEGATE_CANCELLED"})

    def test_linux_effects_send_the_exact_requests(self):
        effects = LinuxGnssEffects(self.path, self.path)
        for start, expected in ((lambda: effects.snapshot(0), b'{"op":"snapshot"}\n'),
                                (lambda: effects.invalidate("GNSS_RESET", 0), b'{"op":"invalidate","reason":"GNSS_RESET"}\n'),
                                (lambda: effects.pps(True, 0), b"PPS_SELECT\n"),
                                (lambda: effects.pps(False, 0), b"PPS_NOSELECT\n")):
            job = start()
            job.poll(0)
            self.assertEqual(self.serve(b'{"ok":true}\n'), expected)
            job.cancel()


class FakeProcess:
    def __init__(self, codes):
        self.codes, self.killed = list(codes), False

    def poll(self):
        return self.codes.pop(0) if len(self.codes) > 1 else self.codes[0]

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return -9


class ConfigRunTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-config-run-")
        self.addCleanup(folder.cleanup)
        self.result = Path(folder.name) / "result.json"
        self.argv = []

    def popen(self, codes):
        def start(argv, **kwargs):
            self.argv.append(argv)
            return FakeProcess(codes)
        return start

    def write(self, started, finished=2000, **fields):
        self.result.write_text(json.dumps(dict({"schema_version": 1, "ok": True, "readback_match": True,
                                                "started_boottime_ms": started, "finished_boottime_ms": finished}, **fields)))

    def test_only_this_runs_result_is_accepted(self):
        run = ConfigRun("srrx-gnss-config.service", self.result, 0, popen=self.popen([None, 0]), boottime=lambda: 1000)
        self.assertEqual(self.argv, [["/usr/bin/systemctl", "--no-ask-password", "--no-block", "start",
                                      "srrx-gnss-config.service"]])
        self.assertIsNone(run.poll(0))
        self.write(900)  # the previous run's verdict
        self.assertIsNone(run.poll(300))
        self.write(1500, finished=None)  # still running
        self.assertIsNone(run.poll(600))
        self.write(1500)
        self.assertIsNone(run.poll(700))  # read at most every 250 ms
        self.assertEqual(run.poll(900)["started_boottime_ms"], 1500)

    def test_refused_start_missing_systemctl_and_start_timeout(self):
        self.assertEqual(ConfigRun("u", self.result, 0, popen=self.popen([4]), boottime=lambda: 0).poll(0),
                         {"ok": False, "error": "GNSS_CONFIG_START_REFUSED"})
        def missing(argv, **kwargs):
            raise FileNotFoundError(argv[0])
        self.assertEqual(ConfigRun("u", self.result, 0, popen=missing, boottime=lambda: 0).poll(0),
                         {"ok": False, "error": "GNSS_CONFIG_START_EXEC"})
        processes = []
        def hanging(argv, **kwargs):
            processes.append(FakeProcess([None]))
            return processes[-1]
        run = ConfigRun("u", self.result, 0, popen=hanging, boottime=lambda: 0)
        self.assertIsNone(run.poll(9999))
        self.assertEqual(run.poll(10000), {"ok": False, "error": "GNSS_CONFIG_START_TIMEOUT"})
        self.assertTrue(processes[0].killed)


if __name__ == "__main__":
    unittest.main()
