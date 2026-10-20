"""Bounded, nonblocking Pico UART and model transports."""
import importlib.util
import os
from pathlib import Path
import termios
from .wire import FrameDecoder, encode_frame


class SerialLink:
    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            a = termios.tcgetattr(self.fd)
            a[0] = a[1] = a[3] = 0
            a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            a[4] = a[5] = termios.B115200
            a[6][termios.VMIN] = a[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, a)
            termios.tcflush(self.fd, termios.TCIOFLUSH)
        except BaseException:
            os.close(self.fd)
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
        termios.tcflush(self.fd, termios.TCIFLUSH)
        self.decoder.reset()


class SimLink:
    """Run the same supervisor model through both real wire codecs, without GPIO."""
    def __init__(self, project):
        path = Path(project) / "firmware/pico/supervisor.py"
        spec = importlib.util.spec_from_file_location("srrx_pico_model", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.model = module.Supervisor(calibration_valid=True, hardware_commissioned=True)
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
            self.last_session, self.tx_seq, self.last_status_ms = session, 0, -1000
            kind = "HELLO"
        elif now_ms - self.last_status_ms >= 100:
            kind = "STATUS"
        else:
            return []
        frame = {"v": 1, "t": kind, "s": session, "q": self.tx_seq, "p": self.model.status()}
        self.tx_seq += 1
        self.last_status_ms = now_ms
        return self.device_decoder.feed(encode_frame(frame))

    def close(self):
        pass
