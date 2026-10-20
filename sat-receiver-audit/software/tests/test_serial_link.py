"""UART termios failures reach the real Engine's safe transport boundary."""
import errno
import os
from pathlib import Path
import termios
import unittest
from unittest.mock import patch

from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SerialLink, SimLink
from srrx.wire import FrameDecoder, encode_frame


PROJECT = Path(__file__).resolve().parents[2]


def partial_decoder():
    frame = {"v": 1, "t": "STATUS", "s": 17, "q": 4, "p": {"state": "ACTIVE"}}
    wire = encode_frame(frame)
    decoder = FrameDecoder()
    decoder.feed(wire[:-5])
    return decoder, frame, wire


class SerialTermiosTests(unittest.TestCase):
    def test_discard_eio_preserves_errno_cause_and_drops_partial_frame(self):
        link = SerialLink.__new__(SerialLink)
        link.fd = 71  # Never used: the kernel failure is injected at tcflush.
        link.decoder, frame, wire = partial_decoder()
        self.assertGreater(link.decoder.buffered_bytes, 0)
        failure = termios.error(errno.EIO, os.strerror(errno.EIO))
        with patch("srrx.link.termios.tcflush", side_effect=failure) as flush:
            with self.assertRaises(OSError) as raised:
                link.discard_input()
        flush.assert_called_once_with(71, termios.TCIFLUSH)
        self.assertEqual(raised.exception.errno, errno.EIO)
        self.assertIs(raised.exception.__cause__, failure)
        self.assertEqual(link.decoder.buffered_bytes, 0)
        self.assertEqual(link.decoder.feed(wire[-5:]), [])
        self.assertEqual(link.decoder.feed(wire), [frame])

    def test_constructor_closes_fd_at_each_termios_failure_boundary(self):
        for point in ("tcgetattr", "tcsetattr", "tcflush"):
            with self.subTest(point=point):
                failure = termios.error(errno.EIO, os.strerror(errno.EIO))
                attributes = [0, 0, 0, 0, 0, 0, [0] * 32]
                with patch("srrx.link.os.open", return_value=72), \
                     patch("srrx.link.os.close") as close, \
                     patch("srrx.link.termios.tcgetattr", return_value=attributes) as get, \
                     patch("srrx.link.termios.tcsetattr") as set_, \
                     patch("srrx.link.termios.tcflush") as flush:
                    {"tcgetattr": get, "tcsetattr": set_, "tcflush": flush}[point].side_effect = failure
                    with self.assertRaises(OSError) as raised:
                        SerialLink("/dev/in-memory-test-only")
                    close.assert_called_once_with(72)
                self.assertEqual(raised.exception.errno, errno.EIO)
                self.assertIs(raised.exception.__cause__, failure)

    def test_constructor_cancellation_still_closes_without_reclassifying(self):
        cancelled = KeyboardInterrupt("fixture cancellation")
        with patch("srrx.link.os.open", return_value=73), \
             patch("srrx.link.os.close") as close, \
             patch("srrx.link.termios.tcgetattr", side_effect=cancelled):
            with self.assertRaises(KeyboardInterrupt) as raised:
                SerialLink("/dev/in-memory-test-only")
            close.assert_called_once_with(73)
        self.assertIs(raised.exception, cancelled)

    def test_delayed_engine_tick_flush_eio_latches_all_outputs_off(self):
        class ModelWithSerialFlush(SimLink):
            # Real handshakes/model/Engine, with the actual SerialLink method at
            # the failing kernel boundary. No UART or acceptance is fabricated.
            discard_input = SerialLink.discard_input

            def __init__(self):
                super().__init__(PROJECT)
                self.fd = 74  # Only passed to the injected tcflush call below.
                self.decoder = FrameDecoder()

        hardware, link = SimHardware(), ModelWithSerialFlush()
        hardware.set_inputs({name: False for name in hardware.inputs if name.startswith("DCS_")})
        engine = Engine(hardware, link, simulated=True)
        try:
            engine.tick(0)
            self.assertTrue(engine.request({"op": "arm"})["ok"])
            for now in range(20, 821, 20):
                engine.tick(now)
            self.assertTrue(engine.policy.armed)
            self.assertTrue(engine.request({"op": "control", "name": "EN_LNA1", "value": True})["ok"])
            self.assertTrue(hardware.outputs["EN_LNA1"])
            link.decoder, _, _ = partial_decoder()
            failure = termios.error(errno.EIO, os.strerror(errno.EIO))
            with patch("srrx.link.termios.tcflush", side_effect=failure) as flush:
                engine.tick(941)  # >100 ms gap takes the real discard_input path.
            flush.assert_called_once_with(74, termios.TCIFLUSH)
            self.assertFalse(engine.policy.armed)
            self.assertEqual(link.decoder.buffered_bytes, 0)
            self.assertIn("OSError", engine.last_error)
            self.assertIn("Input/output error", engine.last_error)
            self.assertTrue(hardware.outputs["CHG_INHIBIT"])
            self.assertFalse(any(v for n, v in hardware.outputs.items() if n != "CHG_INHIBIT"))
            # Restored normal model traffic must not clear the physical-I/O trip.
            for now in range(961, 1762, 20):
                engine.tick(now)
            self.assertFalse(engine.policy.armed)
            self.assertFalse(hardware.outputs["EN_LNA1"])
            self.assertFalse(engine.request({"op": "control", "name": "EN_LNA1", "value": True})["ok"])
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
