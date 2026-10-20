"""MicroPython entry point for the external RP2040-Zero / BNO085 pack.

No automatic calibration, tare, saved-DCD writes or true-north/heading output.
Copy shtp.py, session.py, device.py and shared wire.py alongside this main.py.
"""


def run():
    import machine
    import micropython
    import os
    import time
    # Hold hardware SPI selection before any sensor reset or lengthy imports.
    # An external 1k PS0 pull-up also holds this strap while the MCU boots.
    ps0 = machine.Pin(8, machine.Pin.OUT, value=1)
    cs = machine.Pin(5, machine.Pin.OUT, value=1)
    reset = machine.Pin(7, machine.Pin.OUT, value=1)
    interrupt = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_UP)
    try:
        from .shtp import SHTPDecoder, ImuError, REPORT_INTERVAL_US, FRESHNESS_MS
        from .session import ImuSession
        from .device import SPITransport, UARTPublisher, TX_BUDGET_MS
    except ImportError:
        from shtp import SHTPDecoder, ImuError, REPORT_INTERVAL_US, FRESHNESS_MS
        from session import ImuSession
        from device import SPITransport, UARTPublisher, TX_BUDGET_MS

    machine.freq(125000000)
    uart = machine.UART(0, baudrate=115200, bits=8, parity=None, stop=1,
                        tx=machine.Pin(0), rx=machine.Pin(1), timeout=0,
                        timeout_char=0, rxbuf=128, txbuf=512)
    spi = machine.SPI(0, baudrate=1000000, polarity=1, phase=1, bits=8,
                      firstbit=machine.SPI.MSB, sck=machine.Pin(2),
                      mosi=machine.Pin(3), miso=machine.Pin(4))
    wdt = machine.WDT(timeout=2000)
    micropython.alloc_emergency_exception_buf(100)

    class Clock:
        def __init__(self):
            self.previous = time.ticks_ms()
            self.total = 0
            self.last_interrupt = None

        def now_ms(self):
            current = time.ticks_ms()
            elapsed = time.ticks_diff(current, self.previous)
            if elapsed < 0:
                raise ImuError("clock_regression")
            self.total += elapsed
            self.previous = current
            return self.total

        def sleep_ms(self, value):
            time.sleep_ms(value)

        def sleep_us(self, value):
            time.sleep_us(value)

        def mark_interrupt(self, pin):
            # Hard IRQ: only assign a small ticks integer; no allocation or I/O.
            self.last_interrupt = time.ticks_ms()

        def interrupt_ms(self):
            # Snapshot edge first: a later edge can only make this timestamp
            # older/conservative, never make delayed cargo appear newer.
            edge = self.last_interrupt
            now = self.now_ms()
            if edge is None:
                raise ImuError("interrupt_timestamp")
            age = time.ticks_diff(self.previous, edge)
            if age < 0:
                raise ImuError("interrupt_timestamp")
            return now - age

    clock = Clock()
    interrupt.irq(handler=clock.mark_interrupt, trigger=machine.Pin.IRQ_FALLING, hard=True)
    transport = SPITransport(spi, cs, interrupt, ps0, reset, clock, clock.interrupt_ms)
    decoder = SHTPDecoder()
    session = ImuSession(clock.now_ms())
    nonce = int.from_bytes(os.urandom(4), "little") or 1
    publisher = UARTPublisher(uart, nonce)
    commands = []
    last_hello = -1000
    need_hello = True
    retry_at = 0
    boot_needed = True

    def hello(now):
        nonlocal last_hello, need_hello
        payload = {"role": "imu", "protocol": 1,
                   "report_interval_us": REPORT_INTERVAL_US,
                   "freshness_ms": FRESHNESS_MS, "clock_hz": 125000000}
        if session.product is not None:
            payload["product"] = session.product
        publisher.send("HELLO", payload, now)
        last_hello, need_hello = now, False

    def publish(event, now):
        nonlocal need_hello
        if event["ok"]:
            # Covers the 100ms enqueue deadline plus UART buffer/FIFO drain
            # at 115200. Downstream adds any further forwarding delay.
            event["age_ms"] += TX_BUDGET_MS
            if event["age_ms"] >= FRESHNESS_MS:
                event = session.failure("serial_age_budget", now)
        if event["ok"] and need_hello:
            hello(now)
        if not event["ok"]:
            need_hello = True
            publisher.drop_unsent()
        publisher.send("EVENT", {"imu": event}, now)

    def consume(packet, noticed):
        if packet is None:
            return
        now = clock.now_ms()
        for channel, payload in decoder.feed(packet):
            outgoing, events = session.receive(channel, payload, now, now - noticed)
            if len(commands) + len(outgoing) > 4:
                raise ImuError("command_queue_full")
            commands.extend(outgoing)
            for event in events:
                publish(event, now)

    try:
        hello(clock.now_ms())
        # Establish HELLO as first UART frame before a potentially slow reset.
        while publisher.pending_frames:
            publisher.pump(clock.now_ms())
            time.sleep_ms(1)
        while True:
            now = clock.now_ms()
            if boot_needed and now >= retry_at and not publisher.pending_frames:
                try:
                    decoder.reset()
                    session.reset(now)
                    commands = []
                    transport.hardware_reset()
                    # Drain startup ads/reset/init, requiring 10ms quiet; all waits bounded.
                    boot_at = clock.now_ms()
                    quiet_at = boot_at
                    while clock.now_ms() - boot_at < 250:
                        packet, noticed = transport.transaction()
                        if packet is not None:
                            consume(packet, noticed)
                            quiet_at = clock.now_ms()
                        elif clock.now_ms() - quiet_at >= 10:
                            break
                        time.sleep_ms(1)
                    session.reset(clock.now_ms())
                    commands = [session.first_command()]
                    boot_needed = False
                except (ImuError, OSError, ValueError) as error:
                    publish(session.failure(str(error), clock.now_ms()), clock.now_ms())
                    retry_at = clock.now_ms() + 1000
            if not boot_needed:
                try:
                    now = clock.now_ms()
                    failure = session.tick(now)
                    if failure is not None:
                        publish(failure, now)
                    if session.fault:
                        boot_needed, retry_at = True, now + 1000
                        commands = []
                    else:
                        # Bounded SPI service before UART; a simultaneous packet
                        # during command writes is consumed rather than discarded.
                        for _ in range(4):
                            command = commands.pop(0) if commands else None
                            packet, noticed = transport.transaction(command)
                            consume(packet, noticed)
                            if packet is None and not commands:
                                break
                        if session.fault:
                            boot_needed, retry_at = True, clock.now_ms() + 1000
                            commands = []
                except (ImuError, OSError, ValueError) as error:
                    publish(session.failure(str(error), clock.now_ms()), clock.now_ms())
                    boot_needed, retry_at = True, clock.now_ms() + 1000
                    commands = []
            now = clock.now_ms()
            if now - last_hello >= 1000 and publisher.pending_frames == 0:
                hello(now)
            publisher.pump(now)
            # Pack has no command API. Bound/discard unwanted RX; never interpret
            # a UART command as calibration, tare, GPIO or flash-write permission.
            if uart.any():
                uart.read(64)
            wdt.feed()
            time.sleep_ms(2)
    finally:
        cs.value(1)
        ps0.value(1)
        reset.value(0)
        # An interpreter/UART error must not keep stale orientation streaming.
        # Pico relay times out; WDT resets this pack into a new random session.
        while True:
            time.sleep_ms(50)


if __name__ == "__main__":
    run()
