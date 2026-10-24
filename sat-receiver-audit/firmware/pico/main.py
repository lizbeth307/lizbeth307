"""Deployed MicroPython entry point. No automatic ARM and no nominal ADC unlock."""

# HELLO repeats the STATUS state/readiness fields but no sensor readings, so
# the 64-hex qualification_record fits the 512-byte frame with no float text.
# STATUS follows within 200 ms with battery, temperatures, fan and brightness.
HELLO_FIELDS = ("state", "fault", "mcp_reset", "calibration_valid",
                "hardware_commissioned", "reject_reason", "hb_fresh", "q6a_on")


def hello_payload(supervisor, serial, calibration_crc32=None, qualification_record=None):
    status = supervisor.status()
    result = {key: status[key] for key in HELLO_FIELDS}
    result.update({"revision": "E3-v2.1", "serial": serial,
                   "calibration_crc32": calibration_crc32,
                   "qualification_record": qualification_record})
    return result


def status_payload(supervisor, adc_raw):
    result = supervisor.status()
    result["adc_raw"] = adc_raw
    return result


def hmi_payload(poller, now_ms):
    result = poller.snapshot(now_ms)
    # Budget the bounded source UART transmit before the host adds its RX budget.
    result["age_ms"] = min(65535, result["age_ms"] + 100)
    if result["lux_age_ms"] is not None:
        result["lux_age_ms"] = min(65535, result["lux_age_ms"] + 100)
    return {"hmi": result}


class TelemetrySchedule:
    """One bounded frame per loop; status cannot be starved by optional input."""
    def __init__(self):
        self.status_at = -200
        self.hello_at = -1000
        self.hmi_at = -200
        self.state = None
        self._auxiliary = "IMU"

    def choose(self, now_ms, state, needs_hello, has_imu, has_events):
        if needs_hello:
            return "HELLO"
        if state != self.state or now_ms - self.status_at >= 200:
            return "STATUS"
        hmi_due = now_ms - self.hmi_at >= 200
        if hmi_due and (not has_imu or self._auxiliary == "HMI"):
            return "HMI"
        if has_imu:
            return "IMU"
        if hmi_due:
            return "HMI"
        if has_events:
            return "EVENT"
        return None

    def sent(self, kind, now_ms, state):
        if kind == "HELLO":
            self.hello_at = now_ms
        elif kind == "STATUS":
            self.status_at, self.state = now_ms, state
        elif kind == "HMI":
            self.hmi_at, self._auxiliary = now_ms, "IMU"
        elif kind == "IMU":
            self._auxiliary = "HMI"


def run():
    import machine
    import time
    import os
    from adapter import Hardware, PicoHMITransport, TickClock, write_all

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
        from hmi import PeripheralPoller

        serial = machine.unique_id().hex()
        calibration_record = {}
        calibration_valid = False
        commissioned = False
        local_qualification = None
        try:
            calibration_record = load("calibration.json")
            hardware.calibration = validate(calibration_record, serial)
            calibration_valid = True
        except (OSError, ValueError, KeyError, TypeError):
            pass  # Missing, corrupt or legacy float record: ARM stays refused.
        if calibration_valid:
            try:
                commission_record = load("commissioning.json")
                commissioned = commissioning_valid(commission_record,
                                                    calibration_record, serial)
                if commissioned:
                    # labd pairs this digest with the sha256 of its acceptance file.
                    local_qualification = commission_record["qualification_record"]
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
        # Pack link is RX-only. tx= must stay (UART1 default TX is GP4, HMI
        # SDA); return GP8 to SIO high-Z so it never drives the pack's RX.
        machine.Pin(8, machine.Pin.IN)
        clock = TickClock(time.ticks_ms, time.ticks_diff)
        hmi = PeripheralPoller(PicoHMITransport())
        tx_session = None
        tx_seq = 0
        schedule = TelemetrySchedule()
        previous_link = False
        imu_loop_at = None
        imu_errors = 0
        imu_latest = None
        diagnostic_events = []

        def transmit(kind, payload):
            nonlocal tx_seq, tx_session
            # UART telemetry must not postpone a safety deadline. Re-sense and
            # apply before every bounded transmit, including a burst of events.
            moment = clock.now_ms()
            supervisor.step(moment, hardware.sample(moment))
            hardware.apply(supervisor.outputs)
            if hardware.uart is None:
                return False
            if tx_session != supervisor.session and kind != "HELLO":
                transmit("HELLO", hello_payload(supervisor, serial, local_cal_crc,
                                                local_qualification))
                return False
            if kind == "HELLO":
                payload = hello_payload(supervisor, serial, local_cal_crc,
                                        local_qualification)
            elif kind == "STATUS":
                payload = status_payload(supervisor, hardware.raw)
            elif kind == "EVENT" and "hmi" in payload:
                payload = hmi_payload(hmi, moment)
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
            return True

        while True:
            now = clock.now_ms()
            supervisor.step(now, hardware.sample(now))
            hardware.apply(supervisor.outputs)
            # Fixed-size I2C transactions only; integration waits are scheduled,
            # never slept. HMI has no reference to Supervisor.receive/ARM.
            hmi.poll(now)
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
            if pending_imu:
                imu_latest = pending_imu[-1]
            diagnostic_events.extend(supervisor.drain_events())
            if len(diagnostic_events) > 8:
                diagnostic_events = diagnostic_events[-8:]
            linked = hardware.uart is not None
            if linked != previous_link:
                decoder.reset()
                previous_link = linked
                schedule.hello_at = -1000
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
                # One outbound frame per iteration avoids routine UART bursts
                # exceeding the 100ms HMI/IMU scheduling-gap guard.
                needs_hello = (tx_session != supervisor.session or
                    now - schedule.hello_at >= 1000 and supervisor.state in ("SAFE", "TRIPPED", "OFF"))
                choice = schedule.choose(now, supervisor.state, needs_hello,
                                         imu_latest is not None, bool(diagnostic_events))
                sent = False
                if choice == "HELLO":
                    sent = transmit("HELLO", hello_payload(supervisor, serial, local_cal_crc,
                                                           local_qualification))
                elif choice == "STATUS":
                    sent = transmit("STATUS", status_payload(supervisor, hardware.raw))
                elif choice == "HMI":
                    sent = transmit("EVENT", {"hmi": {}})
                elif choice == "IMU":
                    event, received_at = imu_latest
                    event = imu_relay.forwarding({"imu": dict(event["imu"])}, received_at, clock.now_ms())
                    if event is not None:
                        sent = transmit("EVENT", event)
                    if sent or event is None:
                        imu_latest = None
                elif choice == "EVENT":
                    # TRIP is a host->Pico command; Pico diagnostics are EVENTs.
                    sent = transmit("EVENT", diagnostic_events[0])
                    if sent:
                        diagnostic_events.pop(0)
                if sent:
                    schedule.sent(choice, clock.now_ms(), supervisor.state)
            else:
                # Bound event storage while no host is powered.
                supervisor.drain_events()
                diagnostic_events = []
                imu_latest = None
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
