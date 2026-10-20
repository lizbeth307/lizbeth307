"""Deployed MicroPython entry point. No automatic ARM and no nominal ADC unlock."""


def hello_payload(supervisor, serial, calibration_crc32=None):
    result = supervisor.status()
    result.update({"revision": "E3-v2.1", "serial": serial,
                   "calibration_crc32": calibration_crc32})
    return result


def status_payload(supervisor, adc_raw):
    result = supervisor.status()
    result["adc_raw"] = adc_raw
    return result


def run():
    import machine
    import time
    import os
    from adapter import Hardware, TickClock, write_all

    hardware = Hardware()  # Safe pins first, even if later imports/files fail.
    machine.freq(125000000)
    # RP2040 hardware WDT stays enabled after construction. Do not feed it from
    # a timer/IRQ: interpreter or UART-loop hangs must cause a reset.
    wdt = machine.WDT(timeout=1000)
    try:
        from supervisor import Supervisor
        from calibration import load, validate, commissioning_valid
        from wire import encode_frame, FrameDecoder
        from imu_relay import IMURelay

        serial = machine.unique_id().hex()
        calibration_record = {}
        calibration_valid = False
        commissioned = False
        calibration_error = None
        try:
            calibration_record = load("calibration.json")
            hardware.calibration = validate(calibration_record, serial)
            calibration_valid = True
        except (OSError, ValueError, KeyError, TypeError) as exc:
            calibration_error = str(exc)
        if calibration_valid:
            try:
                commissioned = commissioning_valid(load("commissioning.json"),
                                                    calibration_record, serial)
            except (OSError, ValueError, KeyError, TypeError):
                commissioned = False
        local_cal_crc = hardware.calibration.record["crc32"] if calibration_valid else None

        def new_session():
            return int.from_bytes(os.urandom(4), "little") or 1

        supervisor = Supervisor(calibration_valid=calibration_valid,
                                session_factory=new_session,
                                hardware_commissioned=commissioned)
        decoder = FrameDecoder()
        imu_decoder = FrameDecoder()
        imu_relay = IMURelay()
        imu_uart = machine.UART(1, baudrate=115200, bits=8, parity=None,
                                stop=1, tx=machine.Pin(8), rx=machine.Pin(9),
                                timeout=0, timeout_char=0, rxbuf=1024)
        clock = TickClock(time.ticks_ms, time.ticks_diff)
        tx_session = None
        tx_seq = 0
        status_at = -200
        hello_at = -1000
        previous_state = None
        previous_link = False
        imu_loop_at = None
        imu_errors = 0

        def transmit(kind, payload):
            nonlocal tx_seq, tx_session
            # UART telemetry must not postpone a safety deadline. Re-sense and
            # apply before every bounded transmit, including a burst of events.
            moment = clock.now_ms()
            supervisor.step(moment, hardware.sample(moment))
            hardware.apply(supervisor.outputs)
            if hardware.uart is None:
                return
            if tx_session != supervisor.session and kind != "HELLO":
                transmit("HELLO", hello_payload(supervisor, serial, local_cal_crc))
            if kind == "HELLO":
                payload = hello_payload(supervisor, serial, local_cal_crc)
            elif kind == "STATUS":
                payload = status_payload(supervisor, hardware.raw)
            if tx_session != supervisor.session:
                tx_session = supervisor.session
                tx_seq = 0
            # Never wrap a sequence within a session. A failure here causes a
            # watchdog reset, yielding a new boot nonce and held MCP reset.
            if tx_seq >= 0xffffffff:
                raise RuntimeError("outgoing sequence exhausted")
            packet = encode_frame({"v": 1, "t": kind, "s": supervisor.session,
                                   "q": tx_seq, "p": payload})
            tx_seq += 1
            write_all(hardware.uart, packet, time.ticks_ms, time.ticks_diff,
                      time.sleep_ms)

        while True:
            now = clock.now_ms()
            supervisor.step(now, hardware.sample(now))
            hardware.apply(supervisor.outputs)
            pending_imu = []
            # Keep draining the pack while Q6A is off. Otherwise an old UART
            # buffer could be relabelled fresh when Linux finally boots.
            if imu_loop_at is not None and now - imu_loop_at > 100:
                imu_uart.read(1024)
                imu_decoder.reset()
                event = imu_relay.invalidate("IMU_RX_SCHEDULING_GAP", now)
                if event is not None:
                    pending_imu.append((event, now))
            imu_loop_at = now
            if imu_uart.any():
                data = imu_uart.read(512)
                if data:
                    frames = imu_decoder.feed(data)
                    if imu_decoder.errors != imu_errors:
                        imu_errors = imu_decoder.errors
                        event = imu_relay.invalidate("IMU_WIRE_ERROR", now)
                        if event is not None:
                            pending_imu.append((event, now))
                    for frame in frames:
                        # Source age already includes its transmit budget. Add
                        # 100ms for this RX scheduling/partial-frame envelope.
                        event = imu_relay.receive(frame, now, rx_age_ms=100)
                        if event is not None:
                            pending_imu.append((event, now))
            stale = imu_relay.step(now)
            if stale is not None:
                pending_imu.append((stale, now))
            linked = hardware.uart is not None
            if linked != previous_link:
                decoder.reset()
                previous_link = linked
                hello_at = -1000
            if linked:
                # Bounded UART work prevents hostile/noisy RX from starving the
                # state machine. Protocol frames are <=512 bytes.
                if hardware.uart.any():
                    data = hardware.uart.read(512)
                    if data:
                        for frame in decoder.feed(data):
                            # Resample before each command; readiness must use
                            # current local measurements, never host values.
                            now = clock.now_ms()
                            supervisor.step(now, hardware.sample(now))
                            supervisor.receive(frame, now)
                            hardware.apply(supervisor.outputs)
                # HELLO must be the first outbound frame of every Pico session.
                changed = previous_state != supervisor.state
                if (tx_session != supervisor.session or now - hello_at >= 1000
                        and supervisor.state in ("SAFE", "TRIPPED", "OFF")):
                    transmit("HELLO", hello_payload(supervisor, serial, local_cal_crc))
                    hello_at = now
                for event, received_at in pending_imu:
                    event = imu_relay.forwarding(event, received_at, clock.now_ms())
                    if event is not None:
                        transmit("EVENT", event)
                for event in supervisor.drain_events():
                    kind = "TRIP" if event["event"] == "TRIP" else "EVENT"
                    transmit(kind, event)
                if changed or now - status_at >= 200:
                    payload = status_payload(supervisor, hardware.raw)
                    # Never forward NaN/Inf; the model stores None on failed ADC.
                    transmit("STATUS", payload)
                    status_at = now
                previous_state = supervisor.state
            else:
                # Bound event storage while no host is powered.
                supervisor.drain_events()
            wdt.feed()  # Only after sensing, model deadlines and physical outputs.
            time.sleep_ms(20)
    finally:
        hardware.fail_safe()
        # Leave hardware WDT unfed; an exception must not strand safe GPIOs in
        # an unmonitored REPL. Powered pad reset/high-Z asserts Q306 via R395.
        while True:
            time.sleep_ms(50)


if __name__ == "__main__":
    run()
