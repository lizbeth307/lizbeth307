#!/usr/bin/env python3
"""Exercise exact production location APIs with independent Linux emulators.

CLI: python3 location_scenarios.py --project REPOSITORY --output REPORT.json
Registry API: run(project) -> per-module EMULATION_PASS / FAIL / UNSUPPORTED.
NMEA bytes cross a real PTY into the production srrx.gnss_uart reader
(configure_raw_115200 read-back, NmeaUartReader) and LocationTracker; only the
udev/sysfs binding of open_lc76g needs the Q6A and is not exercised here.
The GPSD endpoint is a protocol emulator, not a real gpsd installation. The
synthetic reference used to test the UTC gate never qualifies GNSS/system UTC.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import tempfile
import termios
import time
from types import SimpleNamespace

try:
    from .location_modules import (GpsdAPIServer, LC76GPTY,
                                   PRIMARY_SOURCES, SYNTHETIC_DEVICE, SYNTHETIC_EPOCH,
                                   SYNTHETIC_LATITUDE, SYNTHETIC_LONGITUDE,
                                   UnsupportedEnvironment, epoch_sentences, gsa, rmc, tpv)
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from location_modules import (GpsdAPIServer, LC76GPTY,
                                  PRIMARY_SOURCES, SYNTHETIC_DEVICE, SYNTHETIC_EPOCH,
                                  SYNTHETIC_LATITUDE, SYNTHETIC_LONGITUDE,
                                  UnsupportedEnvironment, epoch_sentences, gsa, rmc, tpv)


def now_ms():
    return time.monotonic_ns() // 1_000_000


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def _load(project, relative, name):
    spec = importlib.util.spec_from_file_location(name, project / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _production(project):
    location = _load(project, "software/srrx/location.py", "srrx_module_lab_production_location")
    uart = _load(project, "software/srrx/gnss_uart.py", "srrx_module_lab_production_gnss_uart")
    return SimpleNamespace(LocationTracker=location.LocationTracker, GpsdClient=location.GpsdClient,
                           NmeaUartReader=uart.NmeaUartReader, configure_raw_115200=uart.configure_raw_115200,
                           raw_115200=uart.raw_115200)


def _reader(api, emulator, tracker):
    """Production reader on its own duplicate of the PTY slave, never the emulator's fd.

    Production configure_raw_115200 sets and reads back the line discipline; the
    reader owns, and on HUP closes, only the duplicate. Its first poll only
    flushes (bytes queued since open have no receipt time), so it runs here,
    before a scenario writes.
    """
    fd = os.dup(emulator.slave)
    try:
        api.configure_raw_115200(fd)
        reader = api.NmeaUartReader(fd, tracker)
    except BaseException:
        os.close(fd)
        raise
    try:
        check(reader.poll(now_ms()) == 0 and reader.flushes == 1 and reader.bytes_received == 0
              and reader.state == "STARTING" and not reader.disconnected,
              "Production reader's first poll was not a start flush")
    except BaseException:
        reader.close("MODULE_LAB_SETUP_FAILED")
        raise
    return reader


def _nmea_feed(emulator, reader, payload, *, fragment=7):
    accepted = 0
    for offset in range(0, len(payload), fragment):
        part = payload[offset:offset + fragment]
        before = reader.bytes_received
        emulator.write(part)
        deadline = time.monotonic() + .5
        while reader.bytes_received < before + len(part):
            if time.monotonic() > deadline or reader.disconnected:
                raise TimeoutError("NMEA PTY receive deadline")
            select.select([reader.fileno()], [], [], .01)
            accepted += reader.poll(now_ms())
    return accepted


def nmea_valid_and_fragmented(api):
    tracker = api.LocationTracker()
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        check(api.raw_115200(termios.tcgetattr(reader.fileno())),
              "Production raw115200 read-back did not hold on the PTY")
        check(_nmea_feed(emulator, reader, gsa(), fragment=3) == 0, "GSA invented a position")
        message = rmc()
        check(_nmea_feed(emulator, reader, message[:-1], fragment=1) == 0, "Fragmented sentence released a fix before LF")
        check(_nmea_feed(emulator, reader, message[-1:], fragment=1) == 1, "Complete RMC did not reach production parser")
        state = tracker.status(now_ms())
        check(state["source"] == "nmea" and state["fresh"] and state["mode"] == 3,
              "Valid PTY GNSS output did not produce a live3D NMEA fix")
        check((state["lat"], state["lon"]) == (SYNTHETIC_LATITUDE, SYNTHETIC_LONGITUDE),
              "Synthetic NMEA coordinate decoding mismatch")
        check(state["utc_verified"] is False, "GNSS UTC became verified without an independent reference")
        check(_nmea_feed(emulator, reader, epoch_sentences(1)) == 1,
              "Same-epoch RMC/GGA incorrectly counted as several distinct positions")
        enriched = tracker.status(now_ms())
        check(enriched["uncertainty_m"] == 5.0 and enriched["alt_msl_m"] == 12.3,
              "GGA/GST fields were not associated with the same synthetic epoch")
        return {"transport": "real_linux_pty_raw115200",
                "production_api": "gnss_uart.configure_raw_115200+NmeaUartReader -> LocationTracker.ingest_nmea",
                "termios_read_back": True,
                "synthetic_input": True, "fragment_size_bytes": 1,
                "three_dimensional_fix": True, "gst_axis_rss_m": enriched["uncertainty_m"],
                "gnss_utc_qualified": False}


def nmea_checksum_invalid_fix_and_resync(api):
    tracker = api.LocationTracker()
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        _nmea_feed(emulator, reader, epoch_sentences())
        corrupt = bytearray(rmc(1))
        corrupt[-3] = ord("0") if corrupt[-3] != ord("0") else ord("1")
        check(_nmea_feed(emulator, reader, bytes(corrupt)) == 0, "Corrupt NMEA checksum was accepted")
        state = tracker.status(now_ms())
        check(not state["fresh"] and state["source"] == "last_good" and state["reason"] == "NMEA_CHECKSUM",
              "Checksum fault did not invalidate live fix while preserving fallback")
        check(_nmea_feed(emulator, reader, rmc(1, valid=False)) == 0, "Invalid RMC navigation status was accepted")
        check(tracker.status(now_ms())["reason"] == "NMEA_NO_FIX", "Invalid navigation state was not reported")
        check(_nmea_feed(emulator, reader, epoch_sentences(1)) == 1, "Valid NMEA did not recover after checksum/no-fix faults")
        _nmea_feed(emulator, reader, b"$" + b"A" * 400 + b"\r\n")
        check(not tracker.status(now_ms())["fresh"], "Oversize NMEA line retained a live fix")
        check(_nmea_feed(emulator, reader, epoch_sentences(2)) == 1 and tracker.status(now_ms())["fresh"],
              "Production stream parser did not resynchronize after an oversized sentence")
        return {"checksum_rejected": True, "invalid_fix_rejected": True,
                "oversize_rejected": True, "next_valid_epoch_recovers": True}


def nmea_replayed_epoch_and_stale(api):
    tracker = api.LocationTracker(fresh_ms=180)
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        _nmea_feed(emulator, reader, epoch_sentences())
        initial_now = now_ms()
        initial_received = initial_now - tracker.status(initial_now)["age_ms"]
        time.sleep(.05)
        check(_nmea_feed(emulator, reader, epoch_sentences()) == 0, "Replayed NMEA epoch was counted as a new fix")
        stamp = now_ms()
        check(stamp - tracker.status(stamp)["age_ms"] == initial_received,
              "Replayed epoch refreshed position receipt time")
        time.sleep(.19)
        stale = tracker.status(now_ms())
        check(not stale["fresh"] and stale["source"] == "last_good" and stale["uncertainty_m"] is None,
              "Silent/replayed receiver was not downgraded to unbounded stale fallback")
        check(stale["utc_verified"] is False, "Stale NMEA retained verified UTC")
        return {"replay_does_not_refresh_receipt_time": True, "freshness_ms": 180,
                "observed_stale_age_ms": stale["age_ms"], "fallback_current_accuracy": "unknown"}


def nmea_drop_and_explicit_reopen(api):
    tracker = api.LocationTracker()
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        _nmea_feed(emulator, reader, epoch_sentences())
        _nmea_feed(emulator, reader, rmc(1)[:17])
        emulator.disconnect()
        reader.poll(now_ms())
        state = tracker.status(now_ms())
        check(reader.disconnected and reader.state == "DISCONNECTED" and reader.fileno() == -1
              and not state["fresh"] and state["reason"] == "NMEA_UART_LOST",
              "Production reader did not turn PTY HUP into NMEA_UART_LOST")
        check(reader.poll(now_ms()) == 0 and reader.disconnected, "Disconnected production reader reopened or read again")
    with LC76GPTY() as replacement, _reader(api, replacement, tracker) as reader:
        check(_nmea_feed(replacement, reader, epoch_sentences(1)) == 1 and tracker.status(now_ms())["fresh"],
              "Explicit fresh PTY transport could not recover after a partial sentence and HUP")
    return {"real_pty_hup": True, "explicit_new_endpoint": True, "partial_stream_resynchronized": True,
            "automatic_reopen": False,
            "disconnect_detection_owner": "production_gnss_uart_NmeaUartReader_pollhup"}


def nmea_synthetic_utc_three_distinct_3d_gates(api):
    reference = [SYNTHETIC_EPOCH]
    tracker = api.LocationTracker(utc_reference=lambda: reference[0])
    states = []
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        for second in range(2):
            reference[0] = SYNTHETIC_EPOCH + second
            check(_nmea_feed(emulator, reader, epoch_sentences(second)) == 1, "Synthetic3D position was rejected")
            states.append(tracker.status(now_ms())["utc_verified"])
        _nmea_feed(emulator, reader, epoch_sentences(1))
        check(tracker.status(now_ms())["utc_verified"] is False, "Duplicate epoch satisfied the third-fix UTC gate")
        reference[0] = SYNTHETIC_EPOCH + 2
        _nmea_feed(emulator, reader, epoch_sentences(2))
        states.append(tracker.status(now_ms())["utc_verified"])
        check(states == [False, False, True], "Three-distinct-3D UTC policy gate behaved incorrectly")
        reference[0] = SYNTHETIC_EPOCH + 1000
        _nmea_feed(emulator, reader, epoch_sentences(3))
        mismatch = tracker.status(now_ms())
        check(not mismatch["fresh"] and not mismatch["utc_verified"] and mismatch["last_error"] == "UTC_REFERENCE_MISMATCH",
              "Untrusted UTC mismatch passed the independent-reference policy")
    # Three distinct2D positions must not pass the same gate.
    reference[0] = SYNTHETIC_EPOCH
    tracker = api.LocationTracker(utc_reference=lambda: reference[0])
    with LC76GPTY() as emulator, _reader(api, emulator, tracker) as reader:
        for second in range(3):
            reference[0] = SYNTHETIC_EPOCH + second
            _nmea_feed(emulator, reader, epoch_sentences(second, mode=2))
        check(tracker.status(now_ms())["utc_verified"] is False, "Three2D fixes passed the3D UTC policy")
    return {"synthetic_reference_gate_sequence": states, "duplicate_not_distinct": True,
            "two_dimensional_fixes_rejected_for_utc_gate": True, "reference_mismatch_rejected": True,
            "real_gnss_utc_qualified": False, "system_clock_modified": False}


def _client(api, server, *, fresh_ms=3000, reference=None):
    tracker = api.LocationTracker(fresh_ms=fresh_ms, device=SYNTHETIC_DEVICE, utc_reference=reference)
    client = api.GpsdClient(tracker, "127.0.0.1", server.port)
    check(client.start(now_ms()), "Production GpsdClient could not start against its explicit loopback emulator")
    return tracker, client


def _gpsd_wait(server, client, tracker, predicate, timeout=1.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        client.poll(now_ms())
        check(server.error is None, "Independent GPSD API server failed: " + str(server.error))
        state = tracker.status(now_ms())
        if predicate(state):
            return state
        time.sleep(.002)
    raise TimeoutError("GPSD API emulation scenario deadline")


def gpsd_watch_fragmented_tpv_and_no_autoreconnect(api):
    with GpsdAPIServer() as server:
        tracker, client = _client(api, server)
        try:
            _gpsd_wait(server, client, tracker, lambda state: client.watching)
            check(server.watch_requests == 1, "Expected one genuine production WATCH request")
            server.enqueue(tpv(), fragment=1)
            state = _gpsd_wait(server, client, tracker, lambda state: state["fresh"])
            check(state["source"] == "gpsd" and state["mode"] == 3 and not state["utc_verified"],
                  "Fragmented synthetic GPSD TPV bypassed source/dimension/UTC policy")
            server.disconnect()
            _gpsd_wait(server, client, tracker, lambda state: client.sock is None)
            accepts = server.accepts
            for unused in range(20):
                client.poll(now_ms())
                time.sleep(.003)
            check(server.accepts == accepts and client.sock is None, "GpsdClient reconnected automatically")
            check(not tracker.status(now_ms())["fresh"], "Disconnected GPSD source retained a live fix")
            check(client.start(now_ms()), "Explicit GPSD reconnect refused")
            _gpsd_wait(server, client, tracker, lambda state: client.watching)
            server.enqueue(tpv(1), fragment=5)
            _gpsd_wait(server, client, tracker, lambda state: state["fresh"])
            check(server.accepts == 2 and server.watch_requests == 2, "Explicit reconnect skipped VERSION/WATCH handshake")
            return {"real_loopback_tcp": True, "server_implementation": "independent_gpsd_api_emulator",
                    "real_gpsd_binary": False, "fragmented_tpv_bytes": True,
                    "observed_watch_requests": server.watch_requests, "connections": server.accepts,
                    "reconnect_requires_explicit_start": True}
        finally:
            client.close("MODULE_LAB_COMPLETE")


def gpsd_invalid_json_replay_and_stale(api):
    with GpsdAPIServer() as server:
        tracker, client = _client(api, server, fresh_ms=180)
        try:
            _gpsd_wait(server, client, tracker, lambda state: client.watching)
            server.enqueue(tpv(), fragment=9)
            _gpsd_wait(server, client, tracker, lambda state: state["fresh"])
            stamp = now_ms()
            original = stamp - tracker.status(stamp)["age_ms"]
            server.enqueue(tpv(), fragment=13)
            _gpsd_wait(server, client, tracker, lambda state: state["ignored_count"] >= 1)
            stamp = now_ms()
            check(stamp - tracker.status(stamp)["age_ms"] == original, "Replayed GPSD epoch refreshed position receipt")
            stale = _gpsd_wait(server, client, tracker, lambda state: not state["fresh"], timeout=.6)
            check(stale["source"] == "last_good" and stale["uncertainty_m"] is None,
                  "GPSD stale fallback retained a bounded current accuracy")
            server.enqueue(b'{"class":"TPV","mode":3,"mode":2}\r\n', fragment=3)
            invalid = _gpsd_wait(server, client, tracker, lambda state: state["last_error"] == "GPSD_JSON")
            check(not invalid["fresh"] and client.watching, "Bad JSON passed as a fix or destroyed the healthy protocol connection")
            return {"repeated_epoch_does_not_refresh": True, "freshness_ms": 180,
                    "stale_fallback_labelled": True, "duplicate_json_keys_rejected": True}
        finally:
            client.close("MODULE_LAB_COMPLETE")


def gpsd_synthetic_utc_gate_and_wrong_protocol(api):
    reference = [SYNTHETIC_EPOCH]
    with GpsdAPIServer() as server:
        tracker, client = _client(api, server, reference=lambda: reference[0])
        try:
            _gpsd_wait(server, client, tracker, lambda state: client.watching)
            states = []
            for second in range(2):
                reference[0] = SYNTHETIC_EPOCH + second
                server.enqueue(tpv(second), fragment=11)
                expected = tpv(second)["time"]
                state = _gpsd_wait(server, client, tracker, lambda state: state["utc"] == expected)
                states.append(state["utc_verified"])
            ignored_before = tracker.ignored_count
            server.enqueue(tpv(1), fragment=11)
            _gpsd_wait(server, client, tracker, lambda state: state["ignored_count"] > ignored_before)
            check(not tracker.status(now_ms())["utc_verified"], "GPSD replay counted as a third independent3D fix")
            reference[0] = SYNTHETIC_EPOCH + 2
            server.enqueue(tpv(2), fragment=11)
            state = _gpsd_wait(server, client, tracker, lambda state: state["utc"] == tpv(2)["time"])
            states.append(state["utc_verified"])
            check(states == [False, False, True], "GPSD three-distinct-3D reference policy failed")
            reference[0] = SYNTHETIC_EPOCH + 3
            server.enqueue(tpv(3, mode=2), fragment=11)
            state = _gpsd_wait(server, client, tracker, lambda state: state["utc"] == tpv(3)["time"])
            check(not state["utc_verified"], "GPSD2D fix retained verified UTC")
            reference[0] = SYNTHETIC_EPOCH + 1000
            server.enqueue(tpv(4), fragment=11)
            state = _gpsd_wait(server, client, tracker, lambda state: state["last_error"] == "UTC_REFERENCE_MISMATCH")
            check(not state["fresh"] and not state["utc_verified"], "GPSD UTC-reference mismatch passed")
        finally:
            client.close("MODULE_LAB_COMPLETE")
    with GpsdAPIServer(protocol_major=99) as server:
        tracker, client = _client(api, server)
        try:
            _gpsd_wait(server, client, tracker, lambda state: client.error == "GPSD_PROTOCOL_UNSUPPORTED")
            check(client.sock is None and not tracker.status(now_ms())["fresh"],
                  "Unsupported GPSD protocol was accepted")
        finally:
            client.close("MODULE_LAB_COMPLETE")
    return {"synthetic_reference_gate_sequence": states, "duplicate_epoch_not_distinct": True,
            "two_dimensional_fix_not_utc_verified": True, "reference_mismatch_rejected": True,
            "unsupported_protocol_refused": True, "real_gnss_utc_qualified": False,
            "system_clock_modified": False}


NMEA_CASES = (nmea_valid_and_fragmented, nmea_checksum_invalid_fix_and_resync,
              nmea_replayed_epoch_and_stale, nmea_drop_and_explicit_reopen,
              nmea_synthetic_utc_three_distinct_3d_gates)
GPSD_CASES = (gpsd_watch_fragmented_tpv_and_no_autoreconnect,
              gpsd_invalid_json_replay_and_stale, gpsd_synthetic_utc_gate_and_wrong_protocol)


def _run_cases(cases, api):
    results = []
    for case in cases:
        started = time.monotonic()
        try:
            observed = case(api)
            result = {"scenario": case.__name__, "status": "EMULATION_PASS", "observed": observed}
        except UnsupportedEnvironment as error:
            result = {"scenario": case.__name__, "status": "UNSUPPORTED", "reason": str(error)[:300]}
        except Exception as error:
            result = {"scenario": case.__name__, "status": "FAIL", "error_type": type(error).__name__,
                      "reason": str(error)[:500]}
        result["elapsed_s"] = round(time.monotonic() - started, 3)
        results.append(result)
    statuses = {result["status"] for result in results}
    status = "FAIL" if "FAIL" in statuses else "UNSUPPORTED" if "UNSUPPORTED" in statuses else "EMULATION_PASS"
    return status, results


def run(project):
    """Unified-registry entry: no files written, only fresh PTYs/loopback sockets."""
    project = Path(project).resolve(strict=True)
    started = time.monotonic()
    graph = json.loads((project / "design/E3.json").read_text(encoding="utf-8"))
    component = next(item for item in graph["components"] if item["ref"] == "U304")
    pins = {item["number"]: item.get("net") for item in component["pins"]}
    check("LC76G" in component["value"] and pins.get("P1.3") == "UART6_RX" and pins.get("P1.4") == "UART6_TX",
          "LC76G U304 identity/UART6 schematic binding changed")
    api = _production(project)
    modules = []
    for module_id, cases, description, unsupported in (
        ("lc76g_u304", NMEA_CASES, "Waveshare LC76G GNSS24370 NMEA output over Linux PTY into the production read-only UART reader",
         ["GNSS RF acquisition, constellation tracking, sensitivity and physical accuracy",
          "PPS edges/phase/jitter, oscillator and GNSS UTC qualification",
          "Physical Q6A UART6 pinmux/baud/electrical levels and reset circuit",
          "Live udev /dev/lab/gnss and sysfs 998000.serial binding of open_lc76g (Q6A only)",
          "Proprietary PAIR/PQTM configuration, flash/NVM and firmware updates"]),
        ("gpsd_client_protocol", GPSD_CASES, "Production GpsdClient against independent loopback GPSD API emulator",
         ["Actual gpsd executable/device discovery/driver operation",
          "Real GNSS UTC, kernel PPS, chrony and host clock discipline"]),
    ):
        status, scenarios = _run_cases(cases, api)
        modules.append({"module_id": module_id, "refs": ["U304"], "status": status,
                        "description": description, "scenarios": scenarios, "unsupported": unsupported})
    status = "FAIL" if any(item["status"] == "FAIL" for item in modules) else (
        "UNSUPPORTED" if any(item["status"] == "UNSUPPORTED" for item in modules) else "EMULATION_PASS")
    paths = {"software/srrx/location.py": project / "software/srrx/location.py",
             "software/srrx/gnss_uart.py": project / "software/srrx/gnss_uart.py",
             "design/E3.json": project / "design/E3.json",
             "deployment/module_lab/location_modules.py": Path(__file__).with_name("location_modules.py"),
             "deployment/module_lab/location_scenarios.py": Path(__file__)}
    scenarios = [scenario for module in modules for scenario in module["scenarios"]]
    return {"v": 1, "suite": "location_module_emulation", "status": status, "modules": modules,
            "scenario_counts": {"total": len(scenarios),
                                "passed": sum(item["status"] == "EMULATION_PASS" for item in scenarios),
                                "failed": sum(item["status"] == "FAIL" for item in scenarios),
                                "unsupported": sum(item["status"] == "UNSUPPORTED" for item in scenarios)},
            "elapsed_s": round(time.monotonic() - started, 3), "primary_sources": PRIMARY_SOURCES,
            "scope": {"synthetic_lab_coordinates_only": True,
                      "real_linux_pty": any(item["status"] == "EMULATION_PASS" for item in modules[0]["scenarios"]),
                      "real_loopback_tcp": any(item["status"] == "EMULATION_PASS" for item in modules[1]["scenarios"]),
                      "gpsd_api_emulation_not_real_gpsd": True, "loopback_address": "127.0.0.1",
                      "physical_gnss": False, "gnss_utc_qualified": False, "system_clock_modified": False,
                      "acceptance_records_created": False, "hardware_release": "BLOCKED"},
            "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}}


run_all = run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run(args.project)
    except Exception as error:
        report = {"v": 1, "suite": "location_module_emulation", "status": "FAIL", "modules": [],
                  "error_type": type(error).__name__, "reason": str(error)[:500],
                  "scope": {"physical_gnss": False, "gnss_utc_qualified": False, "hardware_release": "BLOCKED"}}
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=output.parent,
                                         prefix=".location-emulation-", suffix=".json", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"suite": report["suite"], "status": report["status"],
                      "modules": [{"module_id": item["module_id"], "status": item["status"]}
                                  for item in report["modules"]]}))
    return 1 if report["status"] == "FAIL" else 2 if report["status"] == "UNSUPPORTED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
