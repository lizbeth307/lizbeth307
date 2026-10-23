"""Protocol fixtures and injected hardware tests; no physical-board PASS claim."""
import math
import struct
import unittest

from firmware.imu.shtp import (
    ImuError, SHTPDecoder, header_length, make_packet, parse_product_id,
    parse_product_ids, product_id_request, set_feature, get_feature, validate_feature_response,
    parse_sensor_cargo,
)
from firmware.imu.session import ImuSession
from firmware.imu.device import SPITransport, UARTPublisher, TX_BUDGET_MS
from srrx.wire import FrameDecoder


PRODUCT = bytes.fromhex("f8 01 03 02 34 12 00 00 78 56 00 00 09 00 00 00")
FEATURE = bytes.fromhex("fc 05 00 00 00 40 0d 03 00 00 00 00 00 00 00 00 00")


def timestamp(ticks=100, report=0xFB):
    return bytes((report,)) + struct.pack("<i", ticks)


def rotation(sequence=7, status=3, quat=(0, 0, 0, 16384), accuracy=2048,
             delay=0, report_id=5):
    head = bytes((report_id, sequence, status | ((delay >> 8) << 2), delay & 255))
    result = head + struct.pack("<hhhh", *quat)
    return result + struct.pack("<h", accuracy) if report_id == 5 else result


def cargo(sequence=7, **kwargs):
    return timestamp() + rotation(sequence, **kwargs)


def configured():
    session = ImuSession(0)
    session.receive(2, PRODUCT, 10)
    session.receive(2, FEATURE, 20)
    return session


class SHTPTests(unittest.TestCase):
    def test_fragmentation_and_independent_channels(self):
        packets = make_packet(0, 0, b"ads") + make_packet(2, 0, PRODUCT) + make_packet(0, 1, b"a")
        expected = [(0, b"ads"), (2, PRODUCT), (0, b"a")]
        for split in range(len(packets) + 1):
            decoder = SHTPDecoder()
            self.assertEqual(decoder.feed(packets[:split]) + decoder.feed(packets[split:]), expected)
            self.assertEqual(decoder.buffered_bytes, 0)

    def test_bytewise_max_packet_is_bounded(self):
        packet = make_packet(0, 0, bytes(508))
        decoder = SHTPDecoder()
        for byte in packet[:-1]:
            self.assertEqual(decoder.feed(bytes((byte,))), [])
            self.assertLessEqual(decoder.buffered_bytes, 511)
        self.assertEqual(decoder.feed(packet[-1:]), [(0, bytes(508))])
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_zero_header_no_data_and_empty_cargo(self):
        self.assertEqual(SHTPDecoder().feed(bytes(4) + b"\x04\x00\x00\x00"), [(0, b"")])

    def test_invalid_headers_latch_until_hardware_reset(self):
        for header in (b"\x03\x00\x00\x00", b"\x01\x02\x00\x00",
                       b"\xff\xff\x00\x00", b"\x04\x80\x00\x00",
                       b"\x04\x00\x06\x00"):
            decoder = SHTPDecoder()
            with self.assertRaises(ImuError):
                decoder.feed(header + bytes(1000))
            self.assertEqual(decoder.buffered_bytes, 0)
            with self.assertRaises(ImuError):
                decoder.feed(make_packet(0, 0, b"ok"))
            decoder.reset()
            self.assertEqual(decoder.feed(make_packet(0, 0, b"ok")), [(0, b"ok")])

    def test_header_and_encoder_validation(self):
        for value in (b"", b"123", b"12345"):
            with self.assertRaises(ImuError):
                header_length(value)
        for args in ((True, 0, b""), (-1, 0, b""), (6, 0, b""),
                     (0, True, b""), (0, 256, b""), (0, 0, bytes(509)), (0, 0, "a")):
            with self.assertRaises(ImuError):
                make_packet(*args)
        with self.assertRaises(ImuError):
            SHTPDecoder().feed(None)

    def test_shtp_sequences_reject_gaps_and_duplicates_but_wrap(self):
        for second in (0, 2):
            decoder = SHTPDecoder()
            decoder.feed(make_packet(3, 0, b"x"))
            with self.assertRaisesRegex(ImuError, "shtp_sequence"):
                decoder.feed(make_packet(3, second, b"x"))
        decoder = SHTPDecoder()
        for seq in range(257):
            self.assertEqual(decoder.feed(make_packet(2, seq & 255, b"x")), [(2, b"x")])

    def test_primary_document_command_fixtures(self):
        self.assertEqual(product_id_request(), b"\xf9\x00")
        self.assertEqual(set_feature(), bytes.fromhex("fd 05 00 00 00 40 0d 03 00 00 00 00 00 00 00 00 00"))
        self.assertEqual(get_feature(), b"\xfe\x05")
        self.assertTrue(validate_feature_response(FEATURE))
        product = parse_product_id(PRODUCT)
        self.assertEqual(product, {"reset_cause": 1, "major": 3, "minor": 2,
                                   "part": 0x1234, "build": 0x5678, "patch": 9})

    def test_bad_product_and_feature_echo(self):
        for value in (PRODUCT[:-1], b"\xf9" + PRODUCT[1:], PRODUCT[:4] + bytes(4) + PRODUCT[8:]):
            with self.assertRaises(ImuError):
                parse_product_id(value)
        for at in (0, 1, 2, 3, 5, 9, 13):
            bad = bytearray(FEATURE)
            bad[at] ^= 1
            with self.assertRaises(ImuError):
                validate_feature_response(bad)
        for value in (True, 0, 1000, 200001):
            with self.assertRaises(ImuError):
                set_feature(interval_us=value)
        with self.assertRaises(ImuError):
            get_feature(9)
        self.assertEqual(parse_product_ids(PRODUCT * 4), [parse_product_id(PRODUCT)] * 4)
        for value in (b"", PRODUCT + PRODUCT[:8], PRODUCT + FEATURE[:16]):
            with self.assertRaisesRegex(ImuError, "product_id_length"):
                parse_product_ids(value)

    def test_signed_q14_and_q12_units_and_status(self):
        report = parse_sensor_cargo(cargo(quat=(-8192, 8192, -8192, 8192), status=2))[0]
        self.assertEqual(report["quaternion"], [-0.5, 0.5, -0.5, 0.5])
        self.assertEqual(report["heading_accuracy_rad"], 0.5)
        self.assertEqual(report["status"], 2)
        self.assertEqual(report["sensor_age_us"], 10000)
        self.assertTrue(all(math.isfinite(value) for value in report["quaternion"]))

    def test_report_delay_rebase_and_multiple_reports(self):
        reports = timestamp(500) + rotation(255, delay=300) + timestamp(100, 0xFA) + rotation(0, delay=50)
        values = parse_sensor_cargo(reports)
        self.assertEqual([x["sensor_age_us"] for x in values], [20000, 35000])
        self.assertEqual([x["sample_seq"] for x in values], [255, 0])

    def test_game_report_has_no_invented_accuracy(self):
        value = parse_sensor_cargo(cargo(report_id=8))[0]
        self.assertEqual(value["report_id"], 8)
        self.assertNotIn("heading_accuracy_rad", value)

    def test_bad_reports_fail_whole_batch(self):
        malformed = (b"", rotation(), b"\xfb\x00", timestamp(),
                     timestamp() + b"\x01", cargo()[:-1], cargo(quat=(0, 0, 0, 0)),
                     cargo(quat=(32767, 32767, 0, 0)), cargo(accuracy=-1),
                     timestamp(-1) + rotation(), timestamp(5000) + rotation(),
                     timestamp(0x7fffffff) + rotation(), cargo() + b"\x05")
        for value in malformed:
            with self.subTest(value=value.hex()):
                with self.assertRaises(ImuError):
                    parse_sensor_cargo(value)


class SessionTests(unittest.TestCase):
    def assert_health(self, events, reason):
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0]["ok"])
        self.assertFalse(events[0]["fresh"])
        self.assertIsNone(events[0]["quaternion"])
        self.assertEqual(events[0]["error"], reason)

    def test_configure_then_fresh_event_has_no_calibration_or_heading_claim(self):
        session = ImuSession()
        self.assertEqual(session.first_command(), (2, b"\xf9\x00"))
        commands, events = session.receive(2, PRODUCT, 10)
        self.assertEqual(commands, [(2, set_feature()), (2, get_feature())])
        self.assertEqual(events, [])
        self.assertEqual(session.receive(2, FEATURE, 20), ([], []))
        commands, events = session.receive(3, cargo(), 30, 7)
        self.assertEqual(commands, [])
        self.assertTrue(events[0]["ok"])
        self.assertEqual(events[0]["age_ms"], 17)
        self.assertEqual(set(events[0]), {"ok", "fresh", "quaternion", "report_id", "status",
                                          "heading_accuracy_rad", "age_ms", "at_ms", "sample_seq"})

    def test_set_feature_may_stream_before_echo_but_is_withheld(self):
        session = ImuSession()
        session.receive(2, PRODUCT, 10)
        self.assertEqual(session.receive(3, cargo(), 15), ([], []))
        self.assertEqual(session.state, "WAIT_FEATURE")
        session.receive(2, FEATURE, 20)
        self.assertTrue(session.receive(3, cargo(sequence=8), 30)[1][0]["ok"])

    def test_report_before_product_fails_closed(self):
        session = ImuSession()
        self.assert_health(session.receive(3, cargo(), 1)[1], "report_before_configuration")
        self.assertEqual(session.receive(2, PRODUCT, 2), ([], []))

    def test_echo_mismatch_does_not_enable_orientation(self):
        session = ImuSession()
        session.receive(2, PRODUCT, 10)
        bad = bytearray(FEATURE)
        bad[5] += 1
        self.assert_health(session.receive(2, bad, 20)[1], "feature_mismatch")
        self.assertEqual(session.receive(3, cargo(), 30), ([], []))

    def test_startup_reset_accepted_runtime_reset_invalidates(self):
        session = ImuSession()
        self.assertEqual(session.receive(1, b"\x01", 1), ([], []))
        init = bytearray(16)
        init[0], init[2], init[6] = 0xF1, 0x84, 1  # sh2.c: INITIALIZE|UNSOLICITED, SYSTEM.
        self.assertEqual(session.receive(2, init, 2), ([], []))
        self.assertEqual(session.state, "WAIT_PRODUCT")
        session.receive(2, PRODUCT, 10)
        self.assert_health(session.receive(1, b"\x01", 11)[1], "sensor_reset")
        for command, reason in ((0x84, "sensor_reset"), (0x04, "sensor_reset"),
                                (0x85, "unexpected_control_report")):
            init[2] = command
            self.assert_health(configured().receive(2, init, 30)[1], reason)
        init[2] = 0x04
        self.assertEqual(ImuSession().receive(2, init, 2), ([], []))

    def test_concatenated_product_id_entries_use_first_and_fail_closed(self):
        second = bytearray(PRODUCT)
        second[4:8] = b"\x99\x00\x00\x00"
        session = ImuSession()
        commands, events = session.receive(2, PRODUCT + bytes(second) * 3, 10)
        self.assertEqual(commands, [(2, set_feature()), (2, get_feature())])
        self.assertEqual(events, [])
        self.assertEqual(session.product, parse_product_id(PRODUCT))
        self.assertEqual(session.receive(2, bytes(second) * 2, 15), ([], []))
        for bad in (PRODUCT + PRODUCT[:8], PRODUCT + FEATURE[:16]):
            self.assert_health(ImuSession().receive(2, bad, 10)[1], "product_id_length")

    def test_sequence_duplicate_gap_and_wrap(self):
        for next_seq in (7, 9):
            session = configured()
            session.receive(3, cargo(), 30)
            self.assert_health(session.receive(3, cargo(next_seq), 40)[1], "report_sequence")
            self.assertEqual(session.receive(3, cargo(8), 50), ([], []))
        session = configured()
        self.assertTrue(session.receive(3, cargo(255), 30)[1][0]["ok"])
        self.assertTrue(session.receive(3, cargo(0), 40)[1][0]["ok"])

    def test_invalid_batch_never_partly_emits_orientation(self):
        session = configured()
        self.assert_health(session.receive(3, cargo() + rotation(9), 30)[1], "report_sequence")

    def test_unreliable_accuracy_has_no_quaternion_and_can_recover(self):
        session = configured()
        self.assert_health(session.receive(3, cargo(status=0), 30)[1], "accuracy_unreliable")
        self.assertIsNone(session.fault)
        self.assertTrue(session.receive(3, cargo(8), 40)[1][0]["fresh"])

    def test_unconfigured_report_and_excess_latency(self):
        self.assert_health(configured().receive(3, cargo(report_id=8), 30)[1], "unconfigured_report")
        for latency in (True, -1, 500):
            self.assert_health(configured().receive(3, cargo(), 30, latency)[1], "transport_latency")
        self.assert_health(configured().receive(3, cargo(), 30, 490)[1], "stale_sensor_report")

    def test_configuration_timeout_stale_and_clock_regression(self):
        session = ImuSession()
        self.assertIsNone(session.tick(2999))
        self.assert_health([session.tick(3000)], "configuration_timeout")
        session = configured()
        session.receive(3, cargo(), 30)
        self.assertIsNone(session.tick(529))
        self.assert_health([session.tick(530)], "sample_timeout")
        self.assertIsNone(session.tick(531))
        self.assertEqual(session.receive(3, cargo(8), 532), ([], []))
        session = configured()
        session.tick(200)
        self.assert_health(session.receive(3, cargo(), 199)[1], "clock_regression")


class FakeClock:
    def __init__(self):
        self.now = 0

    def now_ms(self):
        return self.now

    def sleep_ms(self, milliseconds):
        self.now += milliseconds

    def sleep_us(self, microseconds):
        pass


class FakePin:
    def __init__(self, value=1, read=None):
        self.current, self.read = value, read
        self.writes = []

    def value(self, value=None):
        if value is not None:
            self.current = value
            self.writes.append(value)
        return self.read() if self.read is not None else self.current


class FakeSPI:
    def __init__(self, responses, cs):
        self.responses, self.cs, self.writes = list(responses), cs, []

    def write_readinto(self, outgoing, incoming):
        assert self.cs.value() == 0
        self.writes.append(bytes(outgoing))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        assert len(response) == len(incoming)
        incoming[:] = response


def transport_for(responses=(), interrupt=0):
    clock, cs, wake, reset = FakeClock(), FakePin(), FakePin(), FakePin()
    int_pin = FakePin(interrupt)
    spi = FakeSPI(responses, cs)
    adapter = SPITransport(spi, cs, int_pin, wake, reset, clock)
    return adapter, spi, clock, cs, int_pin, wake, reset


class DeviceTests(unittest.TestCase):
    def test_reset_holds_ps0_high_through_first_interrupt(self):
        adapter, _, clock, _, interrupt, wake, reset = transport_for()
        interrupt.read = lambda: 0 if clock.now >= 50 else 1
        adapter.hardware_reset()
        self.assertEqual(clock.now, 50)
        self.assertTrue(adapter.booted)
        self.assertTrue(all(wake.writes))
        self.assertEqual(reset.writes[-3:], [1, 0, 1])

    def test_reset_timeout_cannot_enable_spi_or_drive_wake_low(self):
        adapter, _, clock, cs, _, wake, _ = transport_for(interrupt=1)
        with self.assertRaisesRegex(ImuError, "spi_before_first_interrupt"):
            adapter.transaction()
        with self.assertRaisesRegex(ImuError, "interrupt_timeout"):
            adapter.hardware_reset()
        self.assertFalse(adapter.booted)
        self.assertEqual(clock.now, 1030)
        self.assertEqual(cs.value(), 1)
        self.assertTrue(all(wake.writes))

    def test_read_header_and_body_in_one_cs_assertion(self):
        packet = make_packet(2, 0, PRODUCT)
        adapter, spi, _, cs, _, wake, _ = transport_for([packet[:4], packet[4:]])
        adapter.hardware_reset()
        before = len(cs.writes)
        self.assertEqual(adapter.transaction(), (packet, 30))
        self.assertEqual(cs.writes[before:], [0, 1])
        self.assertEqual(spi.writes, [bytes(4), bytes(16)])
        self.assertEqual(wake.value(), 1)

    def test_command_captures_simultaneous_packet_and_pads_shorter_cargo(self):
        packet = make_packet(2, 0, PRODUCT)
        adapter, spi, _, _, _, wake, _ = transport_for([packet[:4], packet[4:]])
        adapter.hardware_reset()
        result, _ = adapter.transaction((2, b"\xf9\x00"))
        self.assertEqual(result, packet)
        self.assertEqual(spi.writes[0], b"\x06\x00\x02\x00")
        self.assertEqual(spi.writes[1], b"\xf9\x00" + bytes(14))
        self.assertEqual(wake.writes[-2:], [0, 1])

    def test_longer_command_with_no_sensor_packet_and_sequence_increment(self):
        adapter, spi, _, _, _, _, _ = transport_for([bytes(4), bytes(17), bytes(4), bytes(2)])
        adapter.hardware_reset()
        self.assertIsNone(adapter.transaction((2, set_feature()))[0])
        self.assertIsNone(adapter.transaction((2, b"\xfe\x05"))[0])
        self.assertEqual(spi.writes[2], b"\x06\x00\x02\x01")

    def test_spi_error_releases_cs_wake_and_invalid_length_is_bounded(self):
        for response in (OSError("bus"), b"\xff\xff\x00\x00", b"\x01\x02\x00\x00"):
            adapter, spi, _, cs, _, wake, _ = transport_for([response])
            adapter.hardware_reset()
            with self.assertRaises((ImuError, OSError)):
                adapter.transaction((2, b"\xf9\x00"))
            self.assertEqual(cs.value(), 1)
            self.assertEqual(wake.value(), 1)
            self.assertEqual(len(spi.writes), 1)

    def test_no_pending_interrupt_and_invalid_command(self):
        adapter, _, _, _, interrupt, _, _ = transport_for()
        adapter.hardware_reset()
        interrupt.current = 1
        self.assertIsNone(adapter.transaction()[0])
        for channel in (-1, 6, True):
            with self.assertRaisesRegex(ImuError, "bad_channel"):
                adapter.transaction((channel, b""))

    def test_interrupt_edge_age_is_preserved_instead_of_read_time(self):
        packet = make_packet(2, 0, PRODUCT)
        adapter, _, clock, _, _, _, _ = transport_for([packet[:4], packet[4:]])
        adapter.hardware_reset()
        clock.now = 100
        adapter.interrupt_time = lambda: 65
        self.assertEqual(adapter.transaction(), (packet, 65))

    def test_invalid_interrupt_timestamp_does_not_assert_cs(self):
        for edge in (None, True, -1, 31):
            adapter, spi, _, cs, _, _, _ = transport_for()
            adapter.hardware_reset()
            adapter.interrupt_time = lambda: edge
            with self.assertRaisesRegex(ImuError, "interrupt_timestamp"):
                adapter.transaction()
            self.assertEqual(cs.value(), 1)
            self.assertEqual(spi.writes, [])


class FakeUART:
    def __init__(self, returns=()):
        self.returns, self.sent, self.chunks = list(returns), bytearray(), []
        self.idle = True

    def txdone(self):
        return self.idle

    def write(self, chunk):
        self.chunks.append(bytes(chunk))
        count = self.returns.pop(0) if self.returns else len(chunk)
        if type(count) is int and 0 < count <= len(chunk):
            self.sent.extend(chunk[:count])
        return count


def drain(publisher, clock=0):
    for now in range(clock, clock + 99):
        if not publisher.pending_frames:
            return
        publisher.pump(now)
    raise AssertionError("publisher did not drain")


class PublisherTests(unittest.TestCase):
    def test_partial_nonblocking_writes_roundtrip_and_each_call_bounded(self):
        uart = FakeUART([None, 0, 3, 5])
        publisher = UARTPublisher(uart, 123)
        publisher.send("HELLO", {"role": "imu", "protocol": 1}, 0)
        publisher.send("EVENT", {"imu": {"ok": False, "fresh": False, "quaternion": None}}, 0)
        drain(publisher)
        frames = FrameDecoder().feed(bytes(uart.sent))
        self.assertEqual([frame["q"] for frame in frames], [0, 1])
        self.assertEqual([frame["t"] for frame in frames], ["HELLO", "EVENT"])
        self.assertTrue(all(len(chunk) <= 32 for chunk in uart.chunks))

    def test_queue_is_two_frames_and_serial_deadline_fails_closed(self):
        publisher = UARTPublisher(FakeUART([None] * 100), 1)
        publisher.send("HELLO", {}, 0)
        publisher.send("EVENT", {}, 0)
        self.assertLessEqual(publisher.pending_bytes, 1024)
        with self.assertRaisesRegex(ImuError, "uart_queue_full"):
            publisher.send("EVENT", {}, 0)
        publisher.pump(99)
        with self.assertRaisesRegex(ImuError, "uart_tx_timeout"):
            publisher.pump(100)

    def test_uart_busy_never_calls_write_or_waits_unbounded(self):
        uart = FakeUART()
        uart.idle = False
        publisher = UARTPublisher(uart, 1)
        publisher.send("HELLO", {}, 0)
        publisher.pump(0)
        publisher.pump(99)
        self.assertEqual(uart.chunks, [])
        with self.assertRaisesRegex(ImuError, "uart_tx_timeout"):
            publisher.pump(100)

    def test_drop_unsent_preserves_started_line_and_forces_visible_sequence_gap(self):
        uart = FakeUART()
        publisher = UARTPublisher(uart, 1)
        publisher.send("HELLO", {}, 0)
        publisher.pump(0)
        publisher.send("EVENT", {}, 1)
        publisher.drop_unsent()
        publisher.send("HELLO", {"role": "imu", "protocol": 1}, 2)
        drain(publisher, 2)
        self.assertEqual([frame["q"] for frame in FrameDecoder().feed(bytes(uart.sent))], [0, 2])

    def test_invalid_uart_results_session_and_no_sequence_wrap(self):
        for session in (0, -1, True, 0x100000000):
            with self.assertRaises(ImuError):
                UARTPublisher(FakeUART(), session)
        publisher = UARTPublisher(FakeUART(), 1)
        with self.assertRaisesRegex(ImuError, "hello_required"):
            publisher.send("EVENT", {}, 0)
        publisher.sequence = 0xffffffff
        with self.assertRaisesRegex(ImuError, "serial_sequence_exhausted"):
            publisher.send("HELLO", {}, 0)
        for value in (True, False, -1, 33, "32"):
            publisher = UARTPublisher(FakeUART([value]), 1)
            publisher.send("HELLO", {}, 0)
            with self.assertRaisesRegex(ImuError, "uart_write_result"):
                publisher.pump(0)

    def test_real_orientation_and_product_hello_fit_wire_limit(self):
        uart = FakeUART()
        publisher = UARTPublisher(uart, 0xffffffff)
        session = configured()
        event = session.receive(3, cargo(quat=(-8192, 8192, -8192, 8192)), 0xffffffff)[1][0]
        event["age_ms"] += TX_BUDGET_MS
        publisher.send("HELLO", {"role": "imu", "protocol": 1, "report_interval_us": 200000,
                                 "freshness_ms": 500, "clock_hz": 125000000,
                                 "product": session.product}, 0)
        publisher.send("EVENT", {"imu": event}, 0)
        self.assertTrue(all(len(item[0]) <= 512 for item in publisher._queue))
        drain(publisher)
        frames = FrameDecoder().feed(bytes(uart.sent))
        self.assertEqual(len(frames), 2)
        self.assertTrue(frames[1]["p"]["imu"]["fresh"])


if __name__ == "__main__":
    unittest.main()
