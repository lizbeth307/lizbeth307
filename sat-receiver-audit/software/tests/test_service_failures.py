"""Adversarial host/Pico integration checks; no devices or acceptance fabricated.

The fake clock drives the actual Engine, SimLink wire codecs and Pico Supervisor.
A separate smoke test uses the real Unix socket service in a child process.
"""
import contextlib
import copy
import json
import os
from pathlib import Path
import socket
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from srrx.daemon import MAX_REQUEST, Server, request_once
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SimLink
from srrx.wire import FrameDecoder, encode_frame

PROJECT = Path(__file__).resolve().parents[2]
# Linux sockaddr_un.sun_path holds 108 bytes including the terminating NUL.
UNIX_PATH_MAX = 108


@contextlib.contextmanager
def short_socket_directory(prefix):
    """Temporary directory whose ctl.sock path fits in sun_path, or None.

    A long TMPDIR (CI workspaces, nested sandboxes) pushes the socket path past
    the AF_UNIX limit and the daemon then refuses to start. Try TMPDIR first,
    then the short system temp directory /tmp.
    """
    for base in (None, '/tmp'):
        if base is not None and not os.path.isdir(base):
            continue
        try:
            directory = tempfile.TemporaryDirectory(prefix=prefix, dir=base)
        except OSError:
            continue
        with directory as name:
            if len(os.fsencode(os.path.join(name, 'ctl.sock'))) < UNIX_PATH_MAX:
                yield Path(name)
                return
    yield None


class FaultLink:
    """Fault injection around the real model transport, not a second controller."""
    def __init__(self):
        self.delegate = SimLink(PROJECT)
        self.freeze_status = False
        self.silence_status = False
        self.drop_hb = False
        self.fail_hb = False
        self.drop_trip = 0  # Number of host TRIP frames lost on the wire.
        self.last_frames = []
        self.injected = []
        self.sent = []

    def send(self, frame, now_ms=None):
        self.sent.append(copy.deepcopy(frame))
        if frame['t'] == 'HB':
            if self.fail_hb:
                raise OSError('injected UART write failure')
            if self.drop_hb:
                return
        if frame['t'] == 'TRIP' and self.drop_trip:
            self.drop_trip -= 1
            return
        self.delegate.send(frame, now_ms)

    def poll(self, now_ms):
        actual = self.delegate.poll(now_ms)
        if self.injected:
            result, self.injected = self.injected, []
            return result
        if self.silence_status:
            return []
        if self.freeze_status:
            return copy.deepcopy(self.last_frames)
        if actual:
            self.last_frames = copy.deepcopy(actual)
        return actual

    def inject_status(self, engine, **changes):
        status = dict(engine.pico, **changes)
        frame = {'v': 1, 't': 'STATUS', 's': engine.session,
                 'q': engine.rx_seq + 100, 'p': status}
        # Prove the payload is accepted by the actual UART codec before injecting.
        self.injected.extend(FrameDecoder().feed(encode_frame(frame)))
        assert self.injected

    @property
    def inputs(self):
        return self.delegate.inputs

    def close(self):
        self.delegate.close()


class SerialOrderLink(FaultLink):
    """SerialLink ordering: queued host frames reach the Pico at the next poll,
    after the frame the Pico produced for that poll was already in flight."""
    def __init__(self):
        super().__init__()
        self.queued = []

    def send(self, frame, now_ms=None):
        self.queued.append(copy.deepcopy(frame))

    def poll(self, now_ms):
        frames = super().poll(now_ms)
        queued, self.queued = self.queued, []
        for frame in queued:
            FaultLink.send(self, frame, now_ms)
        return frames


class EngineFailureTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith('DCS_')})
        self.link = FaultLink()
        self.engine = Engine(self.hardware, self.link, simulated=True)
        self.now = 0
        self.engine.tick(self.now)

    def tearDown(self):
        self.engine.close()

    def advance(self, target):
        while self.now < target:
            self.now = min(target, self.now + 20)
            self.engine.tick(self.now)

    def arm(self):
        self.assertTrue(self.engine.request({'op': 'arm', '_owner': 'operator-A'})['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())
        self.assertTrue(self.engine.request({'op': 'control', 'name': 'EN_LNA1',
                                              'value': True, '_owner': 'operator-A'})['ok'])
        self.assertTrue(self.hardware.outputs['EN_LNA1'])

    def assert_safe(self):
        self.assertFalse(self.engine.policy.armed)
        self.assertTrue(self.hardware.outputs['CHG_INHIBIT'])
        self.assertFalse(any(value for name, value in self.hardware.outputs.items() if name != 'CHG_INHIBIT'))

    def assert_stays_latched(self, milliseconds=1000):
        self.advance(self.now + milliseconds)
        self.assert_safe()
        self.assertFalse(self.engine.request({'op': 'control', 'name': 'EN_LNA1',
                                               'value': True, '_owner': 'operator-A'})['ok'])

    def test_default_simulation_is_never_hardware_qualification(self):
        self.arm()
        self.assertEqual(self.engine.status()['mode'], 'SIMULATION')
        self.assertFalse(self.engine.status()['hardware_qualified'])
        self.assertIsNone(self.engine.acceptance)

    def test_stale_pico_status_trips_before_independent_heartbeat_timeout(self):
        self.arm()
        self.link.silence_status = True
        self.advance(self.now + 520)
        self.assert_safe()
        self.assertIn('pico_status_timeout', self.engine.last_error)
        self.link.silence_status = False
        self.assert_stays_latched()

    def test_status_reports_pico_freshness_with_the_arm_refusal_bound(self):
        hardware, link = SimHardware(), FaultLink()
        engine = Engine(hardware, link, simulated=True)
        try:
            status = engine.status()
            self.assertEqual((status['pico_fresh'], status['pico_age_ms']), (False, None))
        finally:
            engine.close()
        self.advance(600)
        status = self.engine.status()
        self.assertIs(status['pico_fresh'], True)
        self.assertTrue(0 <= status['pico_age_ms'] <= 500)
        self.link.silence_status = True
        self.advance(self.now + 600)
        status = self.engine.status()
        self.assertIs(status['pico_fresh'], False)
        self.assertGreater(status['pico_age_ms'], 500)
        # The console's freshness claim and labd's ARM refusal agree.
        self.assertEqual(self.engine.request({'op': 'arm'})['error'], 'fresh Pico HELLO/status required')
        self.link.silence_status = False
        self.advance(self.now + 200)
        self.assertIs(self.engine.status()['pico_fresh'], True)

    def test_replayed_status_does_not_refresh_freshness(self):
        self.arm()
        last_fresh = self.engine.last_status_ms
        self.link.freeze_status = True
        self.advance(self.now + 520)
        self.assertEqual(self.engine.last_status_ms, last_fresh)
        self.assert_safe()
        self.link.freeze_status = False
        self.assert_stays_latched()

    def test_one_way_host_heartbeat_loss_asserts_pico_reset(self):
        self.arm()
        self.link.drop_hb = True
        self.advance(self.now + 800)
        self.assertTrue(self.link.delegate.model.outputs['mcp_reset'])
        # DISP12 is the operator console, not an ARM output; SAFE_BOOT is.
        self.assertTrue(self.link.delegate.model.outputs['safe_boot'])
        self.assertEqual(self.link.delegate.model.state, 'TRIPPED')
        # HMI-07: a non-thermal trip with Q6A on and a cool panel keeps the console
        # lit to show the fault (thermal trips such as CASE_HOT switch it off).
        self.assertEqual(self.link.delegate.model.fault, 'HEARTBEAT_TIMEOUT')
        self.assertTrue(self.link.delegate.model.outputs['disp_en'])
        self.assert_safe()
        self.link.drop_hb = False
        self.assert_stays_latched()

    def test_uart_write_failure_disables_and_never_auto_recovers(self):
        self.arm()
        self.link.fail_hb = True
        self.advance(self.now + 220)
        self.assert_safe()
        self.assertIn('UART write failure', self.engine.last_error)
        self.link.fail_hb = False
        self.assert_stays_latched()

    def test_gpio_read_failure_disables_then_restored_io_does_not_rearm(self):
        self.arm()
        with patch.object(self.hardware, 'read_inputs', side_effect=OSError('injected I2C read failure')):
            self.advance(self.now + 20)
        self.assert_safe()
        self.assertIn('I2C read failure', self.engine.last_error)
        self.assert_stays_latched()

    def test_physical_fault_clear_does_not_clear_host_latch(self):
        self.arm()
        self.hardware.set_inputs({'FAULT_LNA1': False})
        self.advance(self.now + 20)
        self.assert_safe()
        self.hardware.set_inputs({'FAULT_LNA1': True})
        self.assert_stays_latched()

    def test_explicit_recovery_arms_without_restoring_previous_enabled_loads(self):
        self.arm()
        self.hardware.set_inputs({'FAULT_LNA1': False})
        self.advance(self.now + 20)
        self.hardware.set_inputs({'FAULT_LNA1': True})
        self.advance(self.now + 200)
        self.assert_safe()
        self.assertTrue(self.engine.request({'op': 'recover', '_owner': 'operator-A'})['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())
        self.assertFalse(any(v for n, v in self.hardware.outputs.items() if n != 'CHG_INHIBIT'))

    def test_lease_expiry_and_late_renewal_never_rearm(self):
        self.arm()
        deadline = self.engine.policy.lease_deadline_ms
        self.advance(deadline)
        self.assert_safe()
        self.engine.request({'op': 'lease', 'value': {'ttl_ms': 5000}, '_owner': 'operator-A'})
        self.assert_stays_latched()

    def test_owner_cannot_be_spoofed_inside_lease_value_or_steal_active_control(self):
        self.arm()
        self.assertFalse(self.engine.request({'op': 'lease', 'value': {'ttl_ms': 5000, 'owner': 'operator-A'}, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.engine.request({'op': 'control', 'name': 'EN_LNA2', 'value': True, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.hardware.outputs['EN_LNA2'])
        # Another client may always request de-energizing an output.
        self.assertTrue(self.engine.request({'op': 'control', 'name': 'EN_LNA1', 'value': False, '_owner': 'operator-B'})['ok'])
        self.assertFalse(self.hardware.outputs['EN_LNA1'])

    def test_codec_valid_malformed_status_and_contradictory_active_fail_closed(self):
        for changes in ({'state': []}, {'state': {}}, {'mcp_reset': 'false'},
                        {'mcp_reset': True}, {'calibration_valid': False},
                        {'hardware_commissioned': False}, {'q6a_on': False}, {'hb_fresh': False}):
            with self.subTest(changes=changes):
                # Each subcase gets a new real model/engine because recovery is explicit.
                hardware = SimHardware()
                link = FaultLink()
                engine = Engine(hardware, link, simulated=True)
                try:
                    engine.tick(0)
                    self.assertTrue(engine.request({'op': 'arm'})['ok'])
                    for now in range(20, 821, 20):
                        engine.tick(now)
                    self.assertTrue(engine.policy.armed)
                    self.assertTrue(engine.request({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
                    link.inject_status(engine, **changes)
                    engine.tick(840)  # Must not raise TypeError for codec-valid payloads.
                    self.assertFalse(engine.policy.armed)
                    self.assertFalse(hardware.outputs['EN_LNA1'])
                    self.assertTrue(hardware.outputs['CHG_INHIBIT'])
                finally:
                    engine.close()

    def test_pico_new_session_revokes_old_permission(self):
        self.arm()
        previous = self.engine.session
        self.link.delegate.model._trip('injected Pico reset')
        self.advance(self.now + 120)
        self.assertNotEqual(self.engine.session, previous)
        self.assert_safe()
        self.assert_stays_latched()

    def test_close_is_idempotent_and_deenergizes(self):
        self.arm()
        self.engine.close()
        self.engine.close()
        self.assert_safe()
        self.assertTrue(self.hardware.closed)

    def test_rpc_parser_rejects_malformed_types_and_server_overrides_owner(self):
        server = object.__new__(Server)
        server.engine = self.engine
        for payload in (b'not json', b'[]', b'{"op":[]}',
                        b'{"op":"lease","value":{"ttl_ms":NaN}}',
                        b'{"op":"control","name":"EN_LNA1","value":1}',
                        b'{"op":"route","receiver":[],"value":"RF2"}',
                        b'[' * 1200 + b']' * 1200):
            with self.subTest(payload=payload[:60]):
                state = {'rx': bytearray(payload + b'\n'), 'uid': 1234}
                server._request(state)
                self.assertFalse(json.loads(state['tx'])['ok'])
                self.assert_safe()
        # The parser boundary uses its peer UID, not caller-controlled _owner.
        request = {'op': 'lease', 'value': {'ttl_ms': 1000}, '_owner': 'uid:0'}
        state = {'rx': bytearray(json.dumps(request).encode() + b'\n'), 'uid': 1234}
        server._request(state)
        self.assertTrue(json.loads(state['tx'])['ok'])
        self.assertEqual(self.engine.policy.owner, 'uid:1234')
        self.assert_safe()

    def test_live_hardware_identity_and_calibration_binding_before_arm(self):
        class PhysicalBoundaryFake(SimHardware):
            physical = True
        class IdentityLink(FaultLink):
            def __init__(self, serial, crc):
                super().__init__()
                self.serial, self.crc = serial, crc
            def poll(self, now_ms):
                frames = super().poll(now_ms)
                for frame in frames:
                    if frame['t'] == 'HELLO':
                        frame['p'].update(serial=self.serial, calibration_crc32=self.crc)
                return frames
        # This is an in-memory Engine unit fixture, never a commissioned file.
        acceptance = {'branch_limits': copy.deepcopy(self.engine.policy.limits),
                      'lab5_budget': {'always_on_a': .6, 'max_lab5_a': 3.2},
                      'pico_serial': 'e661000000001234',
                      'battery_adc': {'record': {'crc32': '7bd013af'}}}
        for serial, crc, allowed in ((None, None, False),
                                     ('e661000000005678', '7bd013af', False),
                                     ('e661000000001234', '00000000', False),
                                     ('e661000000001234', '7bd013af', True)):
            with self.subTest(serial=serial, crc=crc):
                hardware, link = PhysicalBoundaryFake(), IdentityLink(serial, crc)
                engine = Engine(hardware, link, simulated=False, acceptance=acceptance)
                try:
                    engine.tick(0)
                    result = engine.request({'op': 'arm'})
                    self.assertEqual(result['ok'], allowed, result)
                    self.assertEqual(any(f['t'] == 'ARM' for f in link.sent), allowed)
                    self.assertEqual(engine.status()['live_identity_verified'], allowed)
                    self.assertFalse(hardware.initialized)  # No MCP write before full handshake.
                finally:
                    engine.close()

    def test_close_still_releases_hardware_and_telemetry_when_link_close_raises(self):
        class Reader:
            closed = False
            def close(self):
                self.closed = True
        reader = Reader()
        self.engine.telemetry_reader = reader
        self.arm()
        with patch.object(self.link, 'close', side_effect=OSError('injected link-close error')):
            with self.assertRaises(OSError):
                self.engine.close()
        self.assertTrue(self.hardware.closed)
        self.assertTrue(reader.closed)
        self.assertTrue(self.engine.closed)
        self.assert_safe()

    def test_hardware_mode_never_substitutes_simulation_acceptance(self):
        # Physical-like fake verifies refusal without touching a Linux device.
        class PhysicalBoundaryFake(SimHardware):
            physical = True
        hardware = PhysicalBoundaryFake()
        link = FaultLink()
        engine = Engine(hardware, link, simulated=False, acceptance=None)
        try:
            engine.tick(0)
            self.assertFalse(engine.request({'op': 'arm'})['ok'])
            self.assertFalse(engine.request({'op': 'sim', 'name': 'drop_link', 'value': True})['ok'])
            self.assertFalse(hardware.initialized)
            self.assertFalse(engine.status()['hardware_qualified'])
            self.assertEqual(engine.policy.telemetry, {})
            self.assertFalse(any(hardware.outputs[n] for n in hardware.outputs if n.startswith('EN_')))
        finally:
            engine.close()

    def test_lost_host_trip_never_leaves_pico_active_with_reset_released(self):
        model = self.link.delegate.model
        for lost, fault in ((1, 'HOST_TRIP'), (1000, 'HEARTBEAT_TIMEOUT')):
            with self.subTest(lost=lost):
                self.arm()
                old, mark = self.engine.session, len(self.link.sent)
                self.link.drop_trip = lost
                disarmed = self.now
                self.assertTrue(self.engine.request({'op': 'disarm'})['ok'])
                self.advance(disarmed + 1000)
                self.assertEqual(model.state, 'TRIPPED')
                self.assertEqual(model.fault, fault)
                self.assertTrue(model.outputs['mcp_reset'])
                self.assert_safe()
                # No HB refreshed the old session; TRIP was repeated instead.
                after = self.link.sent[mark:]
                self.assertFalse(any(f['t'] == 'HB' and f['s'] == old for f in after))
                self.assertGreaterEqual(sum(f['t'] == 'TRIP' and f['s'] == old for f in after), 2)
                self.link.drop_trip = 0
                self.advance(self.now + 300)

    def test_recover_survives_tripped_report_already_in_flight(self):
        # Every 20 ms phase of the 100 ms model STATUS cadence, with SerialLink ordering.
        for phase in range(0, 120, 20):
            with self.subTest(phase=phase):
                hardware, link = SimHardware(), SerialOrderLink()
                hardware.set_inputs({n: False for n in hardware.inputs if n.startswith('DCS_')})
                engine = Engine(hardware, link, simulated=True)
                try:
                    now = 0
                    engine.tick(now)
                    def run(until):
                        nonlocal now
                        while now < until:
                            now += 20
                            engine.tick(now)
                    self.assertTrue(engine.request({'op': 'arm'})['ok'])
                    run(1000)
                    self.assertTrue(engine.policy.armed)
                    engine.request({'op': 'disarm'})
                    run(1500 + phase)
                    self.assertEqual(link.delegate.model.state, 'TRIPPED')
                    self.assertTrue(engine.request({'op': 'recover'})['ok'])
                    run(now + 1000)
                    self.assertTrue(engine.policy.armed, engine.status())
                    self.assertEqual(link.delegate.model.state, 'ACTIVE')
                finally:
                    engine.close()

    def test_refused_arm_releases_pending_state(self):
        self.link.delegate.inputs['panel_temp_c'] = 70.0
        self.advance(self.now + 100)
        self.assertTrue(self.engine.request({'op': 'arm', '_owner': 'operator-A'})['ok'])
        self.advance(self.now + 1100)
        self.assertFalse(self.engine.pending_arm)
        self.assertEqual(self.engine.last_error, 'pico_arm_not_acknowledged')
        self.assertEqual(self.link.delegate.model.state, 'SAFE')
        self.assert_safe()
        # Another operator is no longer blocked by the abandoned request.
        self.link.delegate.inputs['panel_temp_c'] = 25.0
        self.advance(self.now + 100)
        self.assertTrue(self.engine.request({'op': 'arm', '_owner': 'operator-B'})['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed)
        self.assertEqual(self.engine.policy.owner, 'operator-B')

    def test_relay_break_before_make_uses_request_time_not_stale_tick(self):
        server = object.__new__(Server)
        server.engine = self.engine
        def rpc(request, at_ms):
            state = {'rx': bytearray(json.dumps(request).encode() + b'\n'), 'uid': 1000}
            with patch('srrx.daemon.time.monotonic', return_value=(at_ms + .5) / 1000):
                server._request(state)
            return json.loads(state['tx'])
        self.assertTrue(rpc({'op': 'arm'}, self.now)['ok'])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed)
        self.assertTrue(rpc({'op': 'relay', 'value': 'HF'}, self.now + 1)['ok'])
        self.advance(self.now + 40)
        tick = self.now
        # Handled 15 ms after its loop's tick: K1 is released at tick+15, not tick.
        self.assertFalse(rpc({'op': 'relay', 'value': 'VHF'}, tick + 15)['ok'])
        self.assertFalse(self.hardware.outputs['K1_ON'] or self.hardware.outputs['K2_ON'])
        self.now = tick + 16
        self.engine.tick(self.now)
        self.assertFalse(rpc({'op': 'relay', 'value': 'VHF'}, tick + 17)['ok'])
        self.assertFalse(self.hardware.outputs['K2_ON'])
        self.now = tick + 25
        self.engine.tick(self.now)
        self.assertTrue(rpc({'op': 'relay', 'value': 'VHF'}, tick + 25)['ok'])
        self.assertTrue(self.hardware.outputs['K2_ON'])

    def test_integer_beyond_float_range_never_escapes_the_service_loop(self):
        server = object.__new__(Server)
        server.engine = self.engine
        self.arm()
        line = b'{"op":"lease","value":{"ttl_ms":1' + b'0' * 400 + b'}}\n'
        state = {'rx': bytearray(line), 'uid': 1001}
        with patch('srrx.daemon.time.monotonic', return_value=(self.now + .5) / 1000):
            server._request(state)
        self.assertFalse(json.loads(state['tx'])['ok'])
        self.assertTrue(self.engine.policy.armed)
        # Codec-valid Pico payload values beyond float range are unavailable, not raised.
        self.engine.imu_sample = (self.now, {'ok': True, 'fresh': True, 'age_ms': 0, 'status': 2,
                                             'report_id': 5, 'quaternion': [10 ** 400, 0, 0, 1]})
        self.engine.hmi_sample = (self.now, {'ok': True, 'fresh': True, 'age_ms': 0, 'keys': 0,
            'presses': [0] * 8, 'encoders': [0, 0], 'lux': 10 ** 400, 'lux_valid': True,
            'lux_age_ms': 0, 'sequence': 1, 'generation': 0, 'error': None})
        status = self.engine.status()
        self.assertFalse(status['imu']['fresh'])
        self.assertTrue(status['hmi']['fresh'])
        self.assertIsNone(status['hmi']['lux'])
        self.assertTrue(self.engine.request({'op': 'sim', 'name': 'battery_mv', 'value': 10 ** 400})['ok'])

    def test_repeated_tripped_reports_with_reset_held_stay_bounded(self):
        self.engine.close()
        link = self.link = FaultLink()
        class ResetHeldHardware(SimHardware):
            # Like LinuxHardware: OLAT writes NACK while the Pico holds MCP RESET.
            calls = 0
            def all_off(self):
                ResetHeldHardware.calls += 1
                super().all_off()
                if link.delegate.model.outputs['mcp_reset'] and not self.closed:
                    raise OSError('MCP held in RESET')
            def close(self):
                self.closed = True
                super().close()
        self.hardware = ResetHeldHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith('DCS_')})
        self.engine = Engine(self.hardware, link, simulated=True)
        self.engine.tick(self.now)
        self.arm()
        self.assertTrue(self.engine.request({'op': 'disarm'})['ok'])
        self.advance(self.now + 5000)
        calls, size = ResetHeldHardware.calls, len(json.dumps(self.engine.status()))
        self.advance(self.now + 60000)  # ~600 TRIPPED STATUS frames with RESET held.
        self.assertEqual(link.delegate.model.state, 'TRIPPED')
        self.assertTrue(self.engine.policy.fault.endswith('safe write unconfirmed: Pico MCP RESET required'))
        self.assertLess(len(self.engine.policy.fault), 200)
        self.assertEqual(ResetHeldHardware.calls, calls)
        self.assertLess(len(json.dumps(self.engine.status())), size + 256)

    def test_lease_owner_cannot_be_bypassed_through_arm_mode_or_pending_arm(self):
        self.arm()
        for op, value in (('mode', 'lab'), ('arm', None), ('recover', None)):
            request = {'op': op, '_owner': 'operator-B'}
            if value:
                request['value'] = value
            self.assertFalse(self.engine.request(request)['ok'], op)
        self.assertTrue(self.engine.policy.armed)
        self.assertEqual(self.engine.requested_mode, 'field')
        self.assertTrue(self.engine.request({'op': 'disarm', '_owner': 'operator-B'})['ok'])
        self.advance(self.now + 5200)  # A's lease expires.
        self.assertIsNone(self.engine.policy.owner)
        self.assertTrue(self.engine.request({'op': 'recover', '_owner': 'operator-A'})['ok'])
        for op in ('arm', 'recover', 'lease'):
            request = {'op': op, '_owner': 'operator-B'}
            if op == 'lease':
                request['value'] = {'ttl_ms': 5000}
            self.assertIn('pending', self.engine.request(request)['error'], op)
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed)
        self.assertEqual(self.engine.policy.owner, 'operator-A')

    def test_heartbeat_reports_host_soc_temperature_for_fan_hysteresis(self):
        for reading, expected, fan in ((lambda: 45.04, 45.0, False), (lambda: 150, None, True),
                                       (lambda: 1 / 0, None, True)):
            with self.subTest(expected=expected):
                hardware, link = SimHardware(), FaultLink()
                engine = Engine(hardware, link, simulated=True, soc_temp_reader=reading)
                try:
                    engine.tick(0)
                    self.assertTrue(engine.request({'op': 'arm'})['ok'])
                    for now in range(20, 1201, 20):
                        engine.tick(now)
                    self.assertTrue(engine.policy.armed)
                    payloads = [f['p'] for f in link.sent if f['t'] == 'HB']
                    self.assertTrue(payloads)
                    self.assertTrue(all(p == ({} if expected is None else {'soc_temp_c': expected}) for p in payloads))
                    self.assertEqual(link.delegate.model.outputs['fan_en'], fan)
                finally:
                    engine.close()

    def test_soc_temperature_reader_takes_hottest_zone_and_fails_unknown(self):
        from srrx.daemon import soc_temp_c
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(OSError):
                soc_temp_c(root)
            for zone, milli in (('thermal_zone0', '41000\n'), ('thermal_zone1', '52500\n')):
                (root / zone).mkdir()
                (root / zone / 'temp').write_text(milli)
            self.assertEqual(soc_temp_c(root), 52.5)
            (root / 'thermal_zone2').mkdir()
            (root / 'thermal_zone2' / 'temp').write_text('unavailable\n')
            with self.assertRaises(ValueError):
                soc_temp_c(root)

    def test_hung_thermal_zone_never_blocks_the_safety_tick(self):
        from srrx.daemon import SocTempSampler
        release = threading.Event()
        def hung_zone():
            release.wait(10)  # A PMIC/I2C-backed zone that does not answer.
            return 47.04
        sampler = SocTempSampler(hung_zone, period_s=.01)
        hardware, link = SimHardware(), FaultLink()
        engine = Engine(hardware, link, simulated=True, soc_temp_reader=sampler)
        try:
            started = time.monotonic()
            for now in range(0, 2001, 20):
                engine.tick(now)
            self.assertLess(time.monotonic() - started, 3)  # Not 10 s per synchronous read.
            payloads = [f['p'] for f in link.sent if f['t'] == 'HB']
            self.assertTrue(payloads)
            self.assertTrue(all(p == {} for p in payloads))  # Unknown: omitted, fan forced on.
            release.set()
            deadline = time.monotonic() + 5
            while (sampler.sample is None or sampler.sample[0] is None) and time.monotonic() < deadline:
                time.sleep(.01)
            mark = len(link.sent)
            for now in range(2020, 4001, 20):
                engine.tick(now)
            self.assertIn({'soc_temp_c': 47.0}, [f['p'] for f in link.sent[mark:] if f['t'] == 'HB'])
        finally:
            release.set()
            engine.close()
        self.assertTrue(sampler.stopping.is_set())  # Engine.close stops the sampler thread.
        sampler.thread.join(2)
        self.assertFalse(sampler.thread.is_alive())
        sampler.sample = (47.0, time.monotonic() - 3.5)
        with self.assertRaises(OSError):
            sampler()  # A stale sample is unknown, not the last value.
        sampler.sample = (None, time.monotonic())
        with self.assertRaises(OSError):
            sampler()

    def test_runtime_starts_tolerate_rtc_behind_acceptance_time(self):
        from srrx import commissioning, daemon, labrx
        seen = []
        def refuse(*args, **kwargs):
            seen.append(kwargs.get('clock_check', True))
            raise commissioning.ValidationError('fixture stops before any device is opened')
        with patch('srrx.commissioning.load_acceptance', side_effect=refuse), patch('builtins.print'):
            self.assertEqual(daemon.main(['--hardware', '--acceptance', 'a.json', '--i2c', '/nonexistent/i2c',
                                          '--i2c0', '/nonexistent/i2c0', '--pico', '/nonexistent/pico']), 1)
            self.assertEqual(labrx.main(['--hardware', '--acceptance', 'a.json', '--driver-record', 'd.json']), 2)
        self.assertEqual(seen, [False, False])  # Provisioning alone keeps the wall-clock bound.
        future = {'accepted_at': '2099-01-01T00:00:00Z', 'branch_limits': {}, 'lab5_budget': {}}
        with patch('srrx.commissioning.load_acceptance', return_value=future), patch('builtins.print') as output:
            self.assertEqual(daemon.main(['--hardware', '--acceptance', 'a.json', '--i2c', '/nonexistent/i2c',
                                          '--i2c0', '/nonexistent/i2c0', '--pico', '/nonexistent/pico']), 1)
        text = ' '.join(str(call.args[0]) for call in output.call_args_list if call.args)
        self.assertIn('system clock is behind acceptance accepted_at', text)
        self.assertIn('labd refused startup', text)

    def test_hold_never_disarms_a_session_it_does_not_own(self):
        from srrx import cli
        # (arm, leases granted, Pico state, seconds slept per loop, end, disarm expected)
        for arm, granted, state, stall, end, disarmed in (
                (False, 0, 'ACTIVE', 1, 2, False),  # Never leased: another operator's session.
                (True, 0, 'ACTIVE', 1, 2, False),   # Refused right after ARM: not ours, or already tripped.
                (False, 1, 'ACTIVE', 1, 2, False),  # Renewal refused after a lapse: another owner now.
                (False, 3, 'ACTIVE', 1, 0, True),   # Ctrl-C while holding: ours, disarm.
                (False, 9, 'SAFE', 1, 2, True),     # Leased but not ACTIVE: ours, disarm.
                (False, 1, 'ACTIVE', 6, 0, False)):  # Ctrl-C after a 6 s stall: lease lapsed.
            with self.subTest(arm=arm, granted=granted, state=state, stall=stall):
                sent, clock = [], [100.0]
                def fake(path, request, timeout=2.0):
                    sent.append(request['op'])
                    if request['op'] == 'lease':
                        if sent.count('lease') <= granted:
                            return {'ok': True}
                        return {'ok': False, 'error': 'another owner holds the lease'}
                    if request['op'] == 'status':
                        return {'ok': True, 'data': {'pico': {'state': state}}}
                    return {'ok': True}
                def sleep(seconds):
                    clock[0] += stall
                    if end == 0 and sent.count('lease') >= max(1, granted):
                        raise KeyboardInterrupt
                with patch('srrx.cli.request_once', side_effect=fake), \
                     patch('srrx.cli.time.sleep', side_effect=sleep), \
                     patch('srrx.cli.time.monotonic', side_effect=lambda: clock[0]), patch('builtins.print'):
                    code = cli.main(['--socket', '/nonexistent', 'hold'] + (['--arm'] if arm else []))
                self.assertEqual(code, end)
                self.assertEqual('disarm' in sent, disarmed)


class ServerDirectoryTests(unittest.TestCase):
    def test_control_socket_directory_writable_by_others_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='srrx-dir-') as directory:
            shared = Path(directory) / 'shared'
            shared.mkdir()
            os.chmod(shared, 0o777)
            with self.assertRaises(RuntimeError):
                Server(shared / 'ctl.sock', None)
            self.assertEqual(list(shared.iterdir()), [])


class StdioServiceIntegrationTests(unittest.TestCase):
    def test_real_child_service_arms_trips_on_link_loss_and_stays_latched(self):
        env = dict(os.environ, PYTHONPATH=str(PROJECT / 'software'))
        process = subprocess.Popen([sys.executable, '-m', 'srrx.daemon', '--simulate',
                                    '--stdio', '--project', str(PROJECT)], cwd=PROJECT,
                                   env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, bufsize=1)
        def rpc(request):
            process.stdin.write(json.dumps(request) + '\n')
            process.stdin.flush()
            ready, _, _ = select.select([process.stdout], [], [], 3)
            self.assertTrue(ready, 'child control response deadline exceeded')
            line = process.stdout.readline()
            self.assertTrue(line, 'child exited before a JSON response')
            return json.loads(line)
        def wait_status(predicate, timeout=3):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                status = rpc({'op': 'status'})['data']
                if predicate(status):
                    return status
                time.sleep(.03)
            self.fail('child state-transition deadline exceeded')
        try:
            status = rpc({'op': 'status'})['data']
            self.assertEqual(status['mode'], 'SIMULATION')
            self.assertFalse(status['hardware_qualified'])
            self.assertFalse(status['policy']['armed'])
            self.assertTrue(rpc({'op': 'arm'})['ok'])
            wait_status(lambda s: s['policy']['armed'])
            self.assertTrue(rpc({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
            self.assertTrue(rpc({'op': 'status'})['data']['policy']['outputs']['EN_LNA1'])
            self.assertFalse(rpc({'op': []})['ok'])
            self.assertTrue(rpc({'op': 'sim', 'name': 'drop_link', 'value': True})['ok'])
            status = wait_status(lambda s: not s['policy']['armed'])
            self.assertFalse(any(v for n, v in status['policy']['outputs'].items() if n != 'CHG_INHIBIT'))
            self.assertTrue(rpc({'op': 'sim', 'name': 'drop_link', 'value': False})['ok'])
            time.sleep(.25)
            status = rpc({'op': 'status'})['data']
            self.assertFalse(status['policy']['armed'])
            self.assertFalse(rpc({'op': 'control', 'name': 'EN_LNA1', 'value': True})['ok'])
            process.stdin.close()
            process.stdin = None
            stdout, stderr = process.communicate(timeout=4)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=2)


class UnixServiceFailureTests(unittest.TestCase):
    def test_invalid_rpc_is_bounded_and_service_remains_disarmed(self):
        try:
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except PermissionError as exc:
            self.skipTest('Execution environment forbids AF_UNIX socket creation: ' + str(exc))
        else:
            probe.close()
        with short_socket_directory('srrx-rpc-') as directory:
            if directory is None:
                self.skipTest('No temporary directory gives an AF_UNIX socket path under %d bytes '
                              '(TMPDIR=%r is too long and /tmp is unusable); set a shorter TMPDIR'
                              % (UNIX_PATH_MAX, os.environ.get('TMPDIR')))
            path = directory / 'ctl.sock'
            env = dict(os.environ, PYTHONPATH=str(PROJECT / 'software'))
            process = subprocess.Popen([sys.executable, '-m', 'srrx.daemon', '--simulate',
                                        '--project', str(PROJECT), '--socket', str(path)],
                                       cwd=PROJECT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            startup_complete = False
            try:
                # Cold ARM64 TCG startup is separate from all live RPC limits.
                deadline = time.monotonic() + 20
                while not path.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=4)
                    self.fail('daemon exited (code %s) before creating its socket %s (%d bytes): %s'
                              % (process.returncode, path, len(os.fsencode(str(path))),
                                 (stdout + stderr).strip()[-2000:] or 'no output'))
                self.assertTrue(path.exists(), 'daemon socket startup timed out')
                startup_complete = True
                malformed = [b'not json\n', b'[]\n', b'{"op":[]}\n',
                             b'{"op":"lease","value":{"ttl_ms":NaN}}\n',
                             b'{"op":"control","name":"EN_LNA1","value":1}\n',
                             b'{"op":"route","receiver":[],"value":"RF2"}\n',
                             (b'[' * 1200) + (b']' * 1200) + b'\n',
                             b'x' * (MAX_REQUEST + 1) + b'\n']
                for data in malformed:
                    with self.subTest(data=data[:60]):
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                            client.settimeout(2)
                            client.connect(str(path))
                            client.sendall(data)
                            try:
                                reply = client.recv(8192)
                            except ConnectionResetError:
                                reply = b''  # Oversize input may be closed without a reply.
                        if reply:
                            self.assertFalse(json.loads(reply.split(b'\n', 1)[0])['ok'])
                        status = request_once(path, {'op': 'status'})['data']
                        self.assertEqual(status['mode'], 'SIMULATION')
                        self.assertFalse(status['hardware_qualified'])
                        self.assertFalse(status['policy']['armed'])
                        self.assertFalse(any(v for n, v in status['policy']['outputs'].items() if n != 'CHG_INHIBIT'))
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate(timeout=2)
                # Preserve the primary startup failure if SIGTERM arrived before
                # the child had installed its clean-shutdown signal handler.
                if startup_complete:
                    self.assertEqual(process.returncode, 0, stdout + stderr)
                self.assertFalse(path.exists(), 'clean service shutdown left the socket behind')


if __name__ == '__main__':
    unittest.main()
