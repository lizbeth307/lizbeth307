"""Concrete SPI adapter and bounded UART publisher; hardware objects injected."""
try:
    from .shtp import MAX_PACKET_BYTES, ImuError, header_length, make_packet
except ImportError:
    from shtp import MAX_PACKET_BYTES, ImuError, header_length, make_packet
try:
    from srrx.wire import encode_frame
except ImportError:
    from wire import encode_frame

# 100ms enqueue deadline plus conservative UART buffer/FIFO allowance. pump()
# writes only with an idle transmitter, in chunks of 32. Verify the RP2 port's
# txdone()/buffer timing on the device before accepting this 150ms budget.
TX_BUDGET_MS = 150


class SPITransport:
    """SPI mode3, one CS assertion per full-duplex transaction.

    GPIO objects expose value(); clock exposes now_ms/sleep_ms/sleep_us.
    Both device read and command write capture any simultaneous sensor packet.
    """
    def __init__(self, spi, cs, interrupt, wake, reset, clock, interrupt_time=None):
        self.spi, self.cs, self.interrupt = spi, cs, interrupt
        self.wake, self.reset_pin, self.clock = wake, reset, clock
        self.interrupt_time = interrupt_time
        self.booted = False
        self._tx_sequence = [0] * 6
        self.cs.value(1)
        self.wake.value(1)  # SPI strap BEFORE reset; never low through first INT.
        self.reset_pin.value(1)

    def _wait_interrupt(self, timeout_ms):
        started = self.clock.now_ms()
        while self.interrupt.value():
            if self.clock.now_ms() - started >= timeout_ms:
                raise ImuError("interrupt_timeout")
            self.clock.sleep_ms(1)

    def hardware_reset(self):
        self.booted = False
        self._tx_sequence = [0] * 6
        self.cs.value(1)
        self.wake.value(1)
        self.reset_pin.value(1)
        self.clock.sleep_ms(10)
        self.reset_pin.value(0)
        self.clock.sleep_ms(10)
        self.reset_pin.value(1)
        self.clock.sleep_ms(10)
        self._wait_interrupt(1000)
        self.booted = True  # First post-reset INT observed while PS0 remained high.

    def transaction(self, command=None):
        """command=(channel,payload) or None. Return (sensor_packet, INT-noticed-ms)."""
        if not self.booted:
            raise ImuError("spi_before_first_interrupt")
        tx = None
        if command is not None:
            channel, payload = command
            if type(channel) is not int or not 0 <= channel < 6:
                raise ImuError("bad_channel")
            tx = make_packet(channel, self._tx_sequence[channel], payload)
            self.wake.value(0)
            try:
                self._wait_interrupt(500)
            except Exception:
                self.wake.value(1)
                raise
        elif self.interrupt.value():
            return None, self.clock.now_ms()
        try:
            noticed = self.clock.now_ms()
            if self.interrupt_time is not None:
                edge = self.interrupt_time()
                if type(edge) is not int or not 0 <= edge <= self.clock.now_ms():
                    raise ImuError("interrupt_timestamp")
                noticed = edge
        except Exception:
            self.wake.value(1)
            raise
        incoming = None
        self.cs.value(0)
        try:
            self.clock.sleep_us(1)
            rx_header = bytearray(4)
            self.spi.write_readinto(tx[:4] if tx is not None else bytes(4), rx_header)
            rx_length = header_length(rx_header)
            tx_remaining = len(tx) - 4 if tx is not None else 0
            rx_remaining = rx_length - 4 if rx_length else 0
            remaining = max(tx_remaining, rx_remaining)
            rx_body = bytearray(remaining)
            if remaining:
                outgoing = bytearray(remaining)
                if tx_remaining:
                    outgoing[:tx_remaining] = tx[4:]
                self.spi.write_readinto(outgoing, rx_body)
            if rx_length:
                incoming = bytes(rx_header) + bytes(rx_body[:rx_remaining])
            if tx is not None:
                self._tx_sequence[channel] = (self._tx_sequence[channel] + 1) & 255
        finally:
            self.cs.value(1)
            self.wake.value(1)
        return incoming, noticed


class UARTPublisher:
    """At most two encoded frames; pump at most 32 bytes per main-loop pass.

    No sequence wrap or unbounded TX retry. A short/None write retains the
    remainder. Caller must service BNO SPI before each next pump.
    """
    def __init__(self, uart, session):
        if type(session) is not int or not 0 < session <= 0xFFFFFFFF:
            raise ImuError("serial_session")
        self.uart = uart
        self.session = session
        self.sequence = 0
        self._queue = []

    @property
    def pending_frames(self):
        return len(self._queue)

    @property
    def pending_bytes(self):
        return sum(len(item[0]) - item[1] for item in self._queue)

    def send(self, kind, payload, now_ms):
        if len(self._queue) >= 2:
            raise ImuError("uart_queue_full")
        if self.sequence >= 0xFFFFFFFF:
            raise ImuError("serial_sequence_exhausted")
        if self.sequence == 0 and kind != "HELLO":
            raise ImuError("hello_required")
        encoded = encode_frame({"v": 1, "t": kind, "s": self.session,
                                "q": self.sequence, "p": payload})
        self.sequence += 1
        self._queue.append([encoded, 0, now_ms])

    def drop_unsent(self):
        # Do not truncate a started line. Dropped reserved q values deliberately
        # cause a receiver sequence-gap fault until the following HELLO.
        self._queue = [item for item in self._queue if item[1]]

    def pump(self, now_ms):
        if not self._queue:
            return
        item = self._queue[0]
        if now_ms - item[2] >= 100:
            raise ImuError("uart_tx_timeout")
        # RP2 txdone() includes both software ring and hardware transmitter.
        # Starting idle guarantees space for this <=32B write, avoiding the
        # per-character busy wait of a write to a full MicroPython TX buffer.
        if not self.uart.txdone():
            return
        chunk = item[0][item[1]:item[1] + 32]
        written = self.uart.write(chunk)
        if written is None:
            return
        if type(written) is not int or not 0 <= written <= len(chunk):
            raise ImuError("uart_write_result")
        if written == 0:
            return
        item[1] += written
        if item[1] == len(item[0]):
            self._queue.pop(0)
