"""Bounded, nonblocking Pico UART and model transports."""
import fcntl
import importlib.util
import os
from pathlib import Path
import termios
from .wire import FrameDecoder, encode_frame


class SerialLink:
    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            # Exclusive owner before any termios change or flush: a second
            # writer must never discard the live daemon's queued TRIP/HB.
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.ioctl(self.fd, termios.TIOCEXCL)
            a = termios.tcgetattr(self.fd)
            a[0] = a[1] = a[3] = 0
            a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            a[4] = a[5] = termios.B115200
            a[6][termios.VMIN] = a[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, a)
            termios.tcflush(self.fd, termios.TCIOFLUSH)
        except BaseException as exc:
            os.close(self.fd)
            self.fd = None
            # CPython termios.error is not an OSError. Present one transport
            # failure contract to daemon/Engine even during partial startup.
            if isinstance(exc, termios.error):
                raise OSError(*exc.args) from exc
            raise
        self.decoder, self.pending = FrameDecoder(), bytearray()

    def send(self, frame, now_ms=None):
        payload = encode_frame(frame)
        if len(self.pending) + len(payload) > 2048:
            raise OSError("Pico transmit queue full")
        self.pending.extend(payload)

    def poll(self, now_ms, inputs=None):
        if self.pending:
            try:
                n = os.write(self.fd, self.pending)
                del self.pending[:n]
            except BlockingIOError:
                pass
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return []
        return self.decoder.feed(data) if data else []

    def close(self):
        if self.fd is not None:
            # The independent Pico timeout is the final fallback if this write
            # cannot be delivered. Never block shutdown waiting for UART drain.
            try:
                if self.pending:
                    os.write(self.fd, self.pending)
            except OSError:
                pass
            os.close(self.fd)
            self.fd = None

    def discard_input(self):
        try:
            termios.tcflush(self.fd, termios.TCIFLUSH)
        except termios.error as exc:
            # HUP can report EIO here after a delayed host tick. Engine must
            # latch that failure and de-energize, rather than lose the exception.
            raise OSError(*exc.args) from exc
        finally:
            self.decoder.reset()


class SimLink:
    """Run the same supervisor model through both real wire codecs, without GPIO."""
    def __init__(self, project):
        path = Path(project) / "firmware/pico/supervisor.py"
        spec = importlib.util.spec_from_file_location("srrx_pico_model", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.model = module.Supervisor(calibration_valid=True, hardware_commissioned=True)
        # The firmware's own HELLO shape: state/readiness fields, no readings, and
        # no serial, calibration CRC or qualification_record for a model.
        spec = importlib.util.spec_from_file_location("srrx_pico_main_model", path.with_name("main.py"))
        main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main)
        self.hello_payload = main.hello_payload
        self.host_decoder, self.device_decoder = FrameDecoder(), FrameDecoder()
        self.tx_seq, self.last_status_ms, self.last_session = 0, -1000, None
        self.inputs = {"q6a_on": True, "battery_mv": 14800,
                       "panel_temp_c": 25.0, "case_temp_c": 25.0, "button_pressed": False}
        self.drop_link = False

    def send(self, frame, now_ms=None):
        if self.drop_link:
            return
        for accepted in self.host_decoder.feed(encode_frame(frame)):
            self.model.receive(accepted, now_ms)

    def poll(self, now_ms, inputs=None):
        self.model.step(now_ms, self.inputs)
        if self.drop_link:
            return []
        session = self.model.session
        if session != self.last_session:
            # The firmware sends STATUS in its next 20 ms loop after a HELLO;
            # the model delivers both in this poll. HELLO is not repeated.
            self.last_session, self.tx_seq = session, 0
            kinds = ("HELLO", "STATUS")
        elif now_ms - self.last_status_ms >= 100:
            kinds = ("STATUS",)
        else:
            return []
        frames = []
        for kind in kinds:
            payload = self.hello_payload(self.model, None) if kind == "HELLO" else self.model.status()
            frame = {"v": 1, "t": kind, "s": session, "q": self.tx_seq, "p": payload}
            self.tx_seq += 1
            frames.extend(self.device_decoder.feed(encode_frame(frame)))
        self.last_status_ms = now_ms
        return frames

    def close(self):
        pass
