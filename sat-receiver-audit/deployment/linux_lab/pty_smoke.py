#!/usr/bin/env python3
"""Real Linux PTY smoke checks for SerialLink and a SIMULATION supervisor peer.

No physical UART, GPIO, I2C, SDR, acceptance record or network endpoint is used.
The peer is the real portable Supervisor state machine with synthetic local
inputs; the host Engine is explicitly SIMULATION. PTY behavior is not electrical
UART qualification, MCU timing evidence or a hardware-release result.
"""
from __future__ import annotations

import argparse
import array
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import sys
import tempfile
import termios
import time

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "software"))

from srrx.engine import Engine
from srrx.hardware import SimHardware, load_mapping
from srrx.link import SerialLink
from srrx.wire import FrameDecoder, encode_frame


def _firmware(name, attribute):
    spec = importlib.util.spec_from_file_location("srrx_pty_" + name + "_fixture", PROJECT / "firmware/pico" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, attribute)


Supervisor = _firmware("supervisor", "Supervisor")
# The shipped main.py frame cadence (STATUS on change or every 200 ms), not a
# faster fixture rate that would hide real 500 ms freshness margins.
TelemetrySchedule = _firmware("main", "TelemetrySchedule")


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def now_ms():
    return time.monotonic_ns() // 1_000_000


def queued_input_bytes(fd):
    queued = array.array("i", [0])
    fcntl.ioctl(fd, termios.FIONREAD, queued, True)
    return queued[0]


def wait_queued_input(fd, expected, timeout=.5):
    """Observe the complete known write in the real slave line discipline."""
    deadline = time.monotonic() + timeout
    while True:
        queued = queued_input_bytes(fd)
        check(queued <= expected, "PTY queued more bytes than the fixture wrote")
        if queued == expected:
            return queued
        remaining = deadline - time.monotonic()
        check(remaining > 0, "PTY complete input queue deadline exceeded: expected=" +
              str(expected) + " observed=" + str(queued))
        time.sleep(min(.002, remaining))


def write_all(fd, payload, timeout=.5):
    deadline, position = time.monotonic() + timeout, 0
    while position < len(payload):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
            raise TimeoutError("PTY fixture write deadline exceeded")
        try:
            position += os.write(fd, payload[position:])
        except BlockingIOError:
            pass


def drain(fd, limit=65536):
    data = bytearray()
    while True:
        try:
            block = os.read(fd, min(4096, limit - len(data) + 1))
        except BlockingIOError:
            break
        if not block:
            break
        data.extend(block)
        if len(data) > limit:
            raise RuntimeError("PTY fixture receive bound exceeded")
    return bytes(data)


class PTY:
    """Own only fresh /dev/pts endpoints allocated for this fixture."""
    def __init__(self):
        self.master = self.link = self.engine = None
        self.max_loop_gap_ms = 0  # Host stalls >100 ms flush real-cadence frames.
        slave = None
        try:
            self.master, slave = pty.openpty()
            name = os.ttyname(slave)
            check(name.startswith("/dev/pts/"), "Expected an ephemeral Linux /dev/pts slave")
            os.set_blocking(self.master, False)
            self.link = SerialLink(name)
        except BaseException:
            self.close()
            raise
        finally:
            if slave is not None:
                os.close(slave)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close_master(self):
        if self.master is not None:
            os.close(self.master)
            self.master = None

    def close(self):
        try:
            if self.engine is not None:
                self.engine.close()
            elif self.link is not None:
                self.link.close()
        finally:
            self.close_master()


def poll_until(link, count=1, timeout=.5):
    found, deadline = [], time.monotonic() + timeout
    while len(found) < count and time.monotonic() < deadline:
        found.extend(link.poll(now_ms()))
        if len(found) < count:
            time.sleep(.002)
    check(len(found) == count, "SerialLink frame receive deadline/count mismatch")
    return found


def frame(sequence=0, session=307):
    return {"v": 1, "t": "HELLO", "s": session, "q": sequence,
            "p": {"state": "SAFE", "mcp_reset": True}}


class Peer:
    """Portable Supervisor, real codecs and PTY bytes; synthetic sensors only."""
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.decoder = FrameDecoder()
        self.session_seed = 300
        self.received_types = []
        self.last_frame = None
        self.last_session = None
        self.last_hello, self.hello_seq = -1000, None
        self.tx_sequence = 0
        self.inputs = {"q6a_on": True, "battery_mv": 14800,
                       "panel_temp_c": 25.0, "case_temp_c": 25.0,
                       "fan_stalled": False, "button_pressed": False}
        self.replace_model()

    def next_session(self):
        self.session_seed += 1
        return self.session_seed

    def replace_model(self):
        # These model flags match SimLink. They never create/pass an acceptance
        # file, and the host Engine remains explicitly simulated throughout.
        self.model = Supervisor(calibration_valid=True, hardware_commissioned=True,
                                session_factory=self.next_session)
        self.schedule = TelemetrySchedule()
        self.last_session = None
        self.decoder.reset()

    def tick(self, stamp, *, emit=True):
        for item in self.decoder.feed(drain(self.endpoint.master)):
            self.received_types.append(item["t"])
            self.received_types = self.received_types[-128:]
            self.model.receive(item, stamp)
        self.model.step(stamp, self.inputs)
        if not emit:
            return
        # Same rule as firmware/pico/main.py: a HELLO discarded by the host's
        # delayed-tick flush must not make this session undiscoverable.
        needs_hello = (self.model.session != self.last_session or
                       stamp - self.schedule.hello_at >= 1000 and self.model.state in ("SAFE", "TRIPPED", "OFF"))
        kind = self.schedule.choose(stamp, self.model.state, needs_hello, False, False)
        if kind not in ("HELLO", "STATUS"):
            return
        if self.model.session != self.last_session:
            self.tx_sequence, self.last_session = 0, self.model.session
        outgoing = {"v": 1, "t": kind, "s": self.model.session,
                    "q": self.tx_sequence, "p": self.model.status()}
        write_all(self.endpoint.master, encode_frame(outgoing))
        self.last_frame = outgoing
        self.tx_sequence += 1
        self.schedule.sent(kind, stamp, self.model.state)
        if kind == "HELLO":
            self.last_hello, self.hello_seq = stamp, outgoing["q"]


def pump(endpoint, peer, predicate=lambda: False, *, timeout=1, emit=True, replay=None):
    deadline, previous = time.monotonic() + timeout, None
    while time.monotonic() < deadline:
        stamp = now_ms()
        if previous is not None:
            endpoint.max_loop_gap_ms = max(endpoint.max_loop_gap_ms, stamp - previous)
        previous = stamp
        peer.tick(stamp, emit=emit)
        if replay is not None:
            write_all(endpoint.master, encode_frame(replay))
        endpoint.engine.tick(stamp)
        if predicate():
            return True
        time.sleep(.01)
    return bool(predicate())


class HandshakeFailure(AssertionError):
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def handshake_diagnostics(endpoint, peer):
    engine = endpoint.engine
    stamp = now_ms()
    def queued(fd):
        if fd is None:
            return None
        try:
            return queued_input_bytes(fd)
        except OSError as error:
            return type(error).__name__ + ": " + str(error)
    return {"observed_at_ms": stamp,
            "engine": {"session": engine.session, "rx_seq": engine.rx_seq, "tx_seq": engine.tx_seq,
                       "pending_arm": engine.pending_arm, "configured": engine.configured,
                       "last_error": engine.last_error, "last_status_ms": engine.last_status_ms,
                       "last_status_age_ms": None if engine.last_status_ms is None else stamp-engine.last_status_ms,
                       "last_tick_ms": engine.last_tick_ms, "last_hb_ms": engine.last_hb_ms,
                       "policy": engine.policy.status()},
            "pico_received": dict(engine.pico),
            "peer": {"session": peer.model.session, "state": peer.model.state,
                     "status": peer.model.status(), "last_host_seq": peer.model.last_host_seq,
                     "last_tx_session": peer.last_session, "next_tx_sequence": peer.tx_sequence,
                     "last_hello_ms": peer.last_hello,
                     "last_frame": peer.last_frame, "received_types": peer.received_types[-16:]},
            "transport": {"pending_host_bytes": len(endpoint.link.pending),
                          "host_decoder_bytes": endpoint.link.decoder.buffered_bytes,
                          "peer_decoder_bytes": peer.decoder.buffered_bytes,
                          "slave_queued_bytes": queued(endpoint.link.fd),
                          "master_queued_bytes": queued(endpoint.master),
                          "max_pump_loop_gap_ms": endpoint.max_loop_gap_ms}}


def handshake_check(condition, message, endpoint, peer):
    if not condition:
        raise HandshakeFailure(message, handshake_diagnostics(endpoint, peer))


def handshake_pump(endpoint, peer, predicate, message, **options):
    try:
        success = pump(endpoint, peer, predicate, **options)
    except Exception as error:
        raise HandshakeFailure(message + ": " + type(error).__name__ + ": " + str(error),
                               handshake_diagnostics(endpoint, peer)) from error
    handshake_check(success, message, endpoint, peer)


def active_engine(endpoint):
    hardware = SimHardware(load_mapping(PROJECT / "design/E3.json"))
    hardware.set_inputs({name: False for name in hardware.inputs if name.startswith("DCS_")})
    endpoint.engine = Engine(hardware, endpoint.link, simulated=True)
    peer = Peer(endpoint)
    handshake_pump(endpoint, peer, lambda: endpoint.engine.session is not None,
                   "Supervisor HELLO did not arrive over PTY", timeout=.5)
    reply = endpoint.engine.request({"op": "arm", "_owner": "pty-smoke-fixture"})
    handshake_check(reply.get("ok") is True, "Explicit simulation ARM request refused", endpoint, peer)
    handshake_pump(endpoint, peer, lambda: endpoint.engine.policy.armed,
                   "Real Supervisor/Engine handshake did not reach simulated ACTIVE", timeout=2)
    handshake_check(peer.model.state == "ACTIVE", "Supervisor did not reach ACTIVE", endpoint, peer)
    check(endpoint.engine.status()["mode"] == "SIMULATION", "Fixture lost SIMULATION label")
    check(endpoint.engine.status()["hardware_qualified"] is False,
          "PTY fixture must never qualify physical hardware")
    reply = endpoint.engine.request({"op": "control", "name": "EN_T7", "value": True,
                                     "_owner": "pty-smoke-fixture"})
    handshake_check(reply.get("ok") is True and hardware.outputs["EN_T7"],
                    "Fixture test load did not become active", endpoint, peer)
    return peer


def hup_trip_path(cause):
    """Engine.trip stores 'OSError: ...' (or a subclass name) for transport
    failures; an empty-read HUP surfaces only via the 500 ms status deadline."""
    names, pending = set(), [OSError]
    while pending:
        kind = pending.pop()
        names.add(kind.__name__)
        pending.extend(kind.__subclasses__())
    if type(cause) is str and ": " in cause and cause.split(": ", 1)[0] in names:
        return "transport_error"
    return "status_deadline" if cause == "pico_status_timeout" else None


def outputs_off(endpoint):
    return not endpoint.engine.policy.armed and not any(
        value for name, value in endpoint.engine.hardware.outputs.items() if name != "CHG_INHIBIT")


def termios_and_fragmented_bidirectional_frames():
    with PTY() as endpoint:
        attrs = termios.tcgetattr(endpoint.link.fd)
        check(attrs[4] == attrs[5] == termios.B115200, "Kernel PTY speed is not 115200")
        check(attrs[0] == attrs[1] == attrs[3] == 0, "PTY input/output/local flags are not raw")
        check(attrs[2] & termios.CSIZE == termios.CS8, "PTY is not configured for eight bits")
        expected, received = frame(), []
        encoded = encode_frame(expected)
        for value in encoded[:-1]:
            write_all(endpoint.master, bytes((value,)))
            received.extend(endpoint.link.poll(now_ms()))
        check(not received, "Partial frame was released before the LF terminator")
        write_all(endpoint.master, encoded[-1:])
        check(poll_until(endpoint.link) == [expected], "Fragmented peer frame changed in transit")
        outgoing = {"v": 1, "t": "HB", "s": 307, "q": 1, "p": {}}
        endpoint.link.send(outgoing, now_ms())
        endpoint.link.poll(now_ms())
        decoder, received = FrameDecoder(), []
        deadline = time.monotonic() + .5
        while not received and time.monotonic() < deadline:
            for value in drain(endpoint.master):
                received.extend(decoder.feed(bytes((value,))))
            time.sleep(.002)
        check(received == [outgoing], "Host frame did not cross the kernel PTY intact")
    return {"baud_setting": 115200, "fragmented_byte_delivery": True, "directions_checked": 2}


def crc_oversize_and_resynchronization():
    with PTY() as endpoint:
        corrupted = bytearray(encode_frame(frame()))
        corrupted[-3] = ord("0") if corrupted[-3] != ord("0") else ord("1")
        expected = frame(2)
        write_all(endpoint.master, bytes(corrupted) + b"@" + b"x" * 600 + b"\n" + encode_frame(expected))
        check(poll_until(endpoint.link) == [expected], "Bad CRC/oversize data crossed the decoder boundary")
        check(endpoint.link.poll(now_ms()) == [], "Rejected bytes leaked a second frame")
    return {"corrupt_crc_rejected": True, "oversize_rejected": True, "next_valid_frame_received": True}


def kernel_input_flush_and_decoder_reset():
    with PTY() as endpoint:
        encoded = encode_frame(frame())
        write_all(endpoint.master, encoded[:12])
        wait_queued_input(endpoint.link.fd, 12)
        check(endpoint.link.poll(now_ms()) == [], "Partial input unexpectedly decoded")
        check(endpoint.link.decoder.buffered_bytes == 12, "Partial decoder input was not actually consumed")
        payload = encoded[12:] + encode_frame(frame(1))
        write_all(endpoint.master, payload)
        # Readability proves only one byte arrived. FIONREAD observes the whole
        # known write before TCIFLUSH, including deferred PTY flip-buffer work.
        wait_queued_input(endpoint.link.fd, len(payload))
        endpoint.link.discard_input()
        check(queued_input_bytes(endpoint.link.fd) == 0, "TCIFLUSH left queued input bytes")
        check(endpoint.link.decoder.buffered_bytes == 0, "Input reset left a partial decoder frame")
        check(endpoint.link.poll(now_ms()) == [], "TCIFLUSH did not discard queued UART bytes")
        fresh = frame(2)
        write_all(endpoint.master, encode_frame(fresh))
        check(poll_until(endpoint.link) == [fresh], "Decoder failed to resynchronize after input reset")
    return {"kernel_tciflush": True, "partial_decoder_state_cleared": True,
            "prefix_decoder_bytes_verified": 12, "complete_kernel_queue_barrier": True}


def bounded_transmit_queue():
    with PTY() as endpoint:
        rejected = False
        for sequence in range(128):
            try:
                endpoint.link.send({"v": 1, "t": "HB", "s": 307, "q": sequence, "p": {}})
            except OSError:
                rejected = True
                break
        check(rejected and len(endpoint.link.pending) <= 2048, "Transmit queue was not bounded at 2048 bytes")
    return {"maximum_pending_bytes": 2048, "overflow_refused": True}


def supervisor_handshake_and_clean_close():
    with PTY() as endpoint:
        peer = active_engine(endpoint)
        # Flush the CONFIGURED frame and let the peer observe ordinary HBs.
        pump(endpoint, peer, timeout=.15)
        check({"ARM", "HB", "CONFIGURED"}.issubset(peer.received_types),
              "Handshake messages did not traverse both real codecs and the PTY")
        endpoint.engine.close()
        check(outputs_off(endpoint), "Clean Engine close retained an active simulated output")
        check(endpoint.link.fd is None, "Clean close retained the serial file descriptor")
        endpoint.engine.close()
    return {"real_supervisor_state_machine": True, "simulated_host_engine": True,
            "explicit_arm_handshake": True, "close_deenergizes_model": True}


def replay_timeout_and_explicit_recovery():
    with PTY() as endpoint:
        peer = active_engine(endpoint)
        pump(endpoint, peer, timeout=.10)
        stale = peer.last_frame
        # A completed master write can still be in the kernel PTY pipeline.
        # Freeze emission and accept that exact final frame before taking the
        # freshness baseline; only already accepted frames are replay traffic.
        handshake_pump(endpoint, peer,
                       lambda: endpoint.engine.session == stale["s"] and endpoint.engine.rx_seq == stale["q"],
                       "Replay baseline frame did not reach Engine", timeout=.5, emit=False)
        handshake_check(endpoint.engine.policy.armed and peer.model.state == "ACTIVE" and
                        peer.model.session == stale["s"], "Replay baseline was not an active current session", endpoint, peer)
        original_received = endpoint.engine.last_status_ms
        check(pump(endpoint, peer, lambda: outputs_off(endpoint), timeout=1, emit=False, replay=stale),
              "Repeated old UART status kept the host armed beyond its freshness deadline")
        check(endpoint.engine.last_status_ms == original_received,
              "Replayed status advanced host freshness")
        # Revocation queues a host TRIP and the peer rotates its session on
        # receipt. Wait for that causal round trip instead of assuming .2s is
        # enough for the kernel queues and both state machines under TCG.
        def restored_tripped_session():
            latest = peer.last_frame
            return (peer.model.state == "TRIPPED" and latest is not None
                    and latest["s"] == peer.model.session == endpoint.engine.session
                    and latest["p"].get("state") == "TRIPPED"
                    and endpoint.engine.pico.get("state") == "TRIPPED"
                    and endpoint.engine.rx_seq == latest["q"]
                    and endpoint.engine.last_status_ms is not None
                    and 0 <= now_ms()-endpoint.engine.last_status_ms <= 500)
        handshake_pump(endpoint, peer, restored_tripped_session,
                       "Restored current TRIPPED session did not reach Engine", timeout=2)
        handshake_check(outputs_off(endpoint), "Restored UART rearmed automatically", endpoint, peer)
        reply = endpoint.engine.request({"op": "recover", "_owner": "pty-smoke-fixture"})
        handshake_check(reply.get("ok") is True, "Explicit simulated recovery was refused", endpoint, peer)
        handshake_pump(endpoint, peer, lambda: endpoint.engine.policy.armed,
                       "Explicit recovery handshake did not complete", timeout=2)
        handshake_check(not any(value for name, value in endpoint.engine.hardware.outputs.items() if name != "CHG_INHIBIT"),
                        "Explicit recovery restored a previous output", endpoint, peer)
    return {"replay_does_not_refresh_status": True, "uart_return_does_not_auto_arm": True,
            "explicit_recovery_keeps_previous_loads_off": True,
            "accepted_replay_baseline": True, "current_tripped_session_barrier": True}


def new_session_invalidates_old_frames():
    with PTY() as endpoint:
        peer = active_engine(endpoint)
        old_session, old_frame = endpoint.engine.session, peer.last_frame
        peer.replace_model()
        check(pump(endpoint, peer, lambda: endpoint.engine.session != old_session, timeout=.5),
              "New Supervisor session was not observed")
        new_session = endpoint.engine.session
        check(outputs_off(endpoint), "New HELLO session did not revoke active outputs")
        pump(endpoint, peer, timeout=.2, replay=old_frame)
        check(endpoint.engine.session == new_session and outputs_off(endpoint),
              "Old-session frame restored old permission")
    return {"new_session_revokes_permission": True, "old_session_replay_rejected": True}


def lost_hello_repeats_and_resynchronizes_without_arm():
    with PTY() as endpoint:
        hardware = SimHardware(load_mapping(PROJECT / "design/E3.json"))
        endpoint.engine = Engine(hardware, endpoint.link, simulated=True)
        peer = Peer(endpoint)
        peer.tick(now_ms())
        first = peer.last_frame
        first_hello_at = peer.last_hello
        handshake_check(first["t"] == "HELLO", "Initial peer frame was not HELLO", endpoint, peer)
        wait_queued_input(endpoint.link.fd, len(encode_frame(first)))
        endpoint.link.discard_input()
        check(queued_input_bytes(endpoint.link.fd) == 0, "First HELLO was not actually flushed")

        # Receive exactly one complete, fresh STATUS through the real kernel
        # before the 1000ms HELLO repeat. Engine must ignore this unknown session.
        deadline = time.monotonic() + .5
        while peer.last_frame["t"] != "STATUS" and time.monotonic() < deadline:
            peer.tick(now_ms())
            time.sleep(.002)
        handshake_check(peer.last_frame["t"] == "STATUS", "Peer did not emit pre-repeat STATUS", endpoint, peer)
        status = peer.last_frame
        wait_queued_input(endpoint.link.fd, len(encode_frame(status)))
        endpoint.engine.tick(now_ms())
        check(queued_input_bytes(endpoint.link.fd) == 0 and endpoint.link.decoder.buffered_bytes == 0,
              "Unknown-session STATUS was not completely consumed")
        check(endpoint.engine.session is None and endpoint.engine.rx_seq == -1,
              "Unknown-session STATUS established identity without HELLO")

        # Only a HELLO can establish the session; like firmware, a due STATUS
        # may follow it in the very next loop, so do not require it to be last.
        # A delayed-tick flush may also drop a repeat: allow three 1000 ms repeats.
        handshake_pump(endpoint, peer,
                       lambda: peer.last_hello > first_hello_at
                       and endpoint.engine.session == peer.model.session
                       and endpoint.engine.rx_seq >= peer.hello_seq,
                       "Repeated HELLO did not resynchronize after real TCIFLUSH", timeout=3.5)
        check(peer.last_hello-first_hello_at >= 1000, "HELLO repeat bypassed the real firmware interval")
        check(outputs_off(endpoint) and not endpoint.engine.pending_arm and "ARM" not in peer.received_types,
              "Session resynchronization automatically armed or restored a load")
        check(endpoint.engine.status()["mode"] == "SIMULATION"
              and endpoint.engine.status()["hardware_qualified"] is False,
              "Lost-HELLO fixture unexpectedly qualified physical hardware")
        return {"first_hello_deliberately_tciflush": True, "unknown_session_status_ignored": True,
                "real_hello_repeat_interval_ms": peer.last_hello-first_hello_at,
                "restored_session": endpoint.engine.session, "repeated_hello_seq": peer.hello_seq,
                "automatic_arm": False, "previous_loads_restored": False}


def master_hup_trips_and_closes():
    with PTY() as endpoint:
        active_engine(endpoint)
        endpoint.close_master()
        started = time.monotonic()
        # A PTY may signal HUP as an empty read rather than immediate EIO. The
        # host status deadline must still revoke permission; do not invent an
        # electrical/disconnect timing guarantee stricter than that contract.
        while time.monotonic() - started < .8 and not outputs_off(endpoint):
            endpoint.engine.tick(now_ms())
            time.sleep(.01)
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        check(outputs_off(endpoint), "Kernel PTY HUP retained permission beyond the host freshness deadline")
        # Read before close(), which records daemon_exit. Every trip sets
        # last_error, so record which accepted HUP path actually disarmed.
        cause = endpoint.engine.last_error
        path = hup_trip_path(cause)
        check(path is not None, "PTY HUP disarm had an unrelated trip cause: " + str(cause))
        endpoint.engine.close()
        check(endpoint.link.fd is None, "HUP cleanup left the serial file descriptor open")
    return {"real_kernel_hup": True, "trip_cause": cause, "trip_path": path,
            "transport_fault_disarms_model": path == "transport_error",
            "status_deadline_disarmed_model": path == "status_deadline",
            "hup_to_model_disarm_ms": elapsed_ms, "descriptor_closed": True}


CASES = (
    termios_and_fragmented_bidirectional_frames,
    crc_oversize_and_resynchronization,
    kernel_input_flush_and_decoder_reset,
    bounded_transmit_queue,
    supervisor_handshake_and_clean_close,
    replay_timeout_and_explicit_recovery,
    new_session_invalidates_old_frames,
    lost_hello_repeats_and_resynchronizes_without_arm,
    master_hup_trips_and_closes,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if sys.platform != "linux":
        parser.error("This smoke suite requires the real Linux PTY/termios implementation")
    results, started = [], time.monotonic()
    for case in CASES:
        before = time.monotonic()
        try:
            observed = case()
            result = {"case": case.__name__, "status": "PASS", "observed": observed}
        except Exception as error:
            result = {"case": case.__name__, "status": "FAIL", "error_type": type(error).__name__,
                      "error": str(error)[:500]}
            if isinstance(error, HandshakeFailure):
                result["diagnostics"] = error.diagnostics
        result["elapsed_s"] = round(time.monotonic() - before, 3)
        results.append(result)
    passed = sum(item["status"] == "PASS" for item in results)
    paths = ("deployment/linux_lab/pty_smoke.py", "software/srrx/link.py", "software/srrx/wire.py",
             "software/srrx/engine.py", "software/srrx/hardware.py", "software/srrx/policy.py",
             "firmware/pico/supervisor.py", "firmware/pico/main.py", "design/E3.json")
    report = {"v": 1, "suite": "real_linux_pty_smoke", "status": "PASS" if passed == len(results) else "FAIL",
              "passed": passed, "failed": len(results) - passed, "cases": results,
              "elapsed_s": round(time.monotonic() - started, 3),
              "python": sys.version.split()[0], "platform": sys.platform,
              "scope": {"kernel_pty_termios": True, "peer_is_portable_supervisor_model": True,
                        "host_engine_mode": "SIMULATION", "physical_uart_tested": False,
                        "gpio_i2c_sdr_opened": False, "acceptance_records_created": False,
                        "physical_tests_performed": False, "hardware_release": "BLOCKED"},
              "source_sha256": {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in paths}}
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=".pty-smoke-", suffix=".json", delete=False) as stream:
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
    print(json.dumps({"suite": report["suite"], "status": report["status"], "passed": passed,
                      "failed": report["failed"], "elapsed_s": report["elapsed_s"]}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
