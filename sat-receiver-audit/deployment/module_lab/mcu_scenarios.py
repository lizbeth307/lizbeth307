"""Run actual Pico/IMU drivers against independent MCU interconnect models.

python -m deployment.module_lab.mcu_scenarios [--project PATH] [--output PATH]
Results are EMULATION_PASS, never physical hardware PASS or commissioning.
No valid calibration/commissioning record is created, written or provisioned.
"""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .mcu_bus import EmulatedMachine, VirtualClock, SOURCE_REFS, load_firmware
except ImportError:
    from mcu_bus import EmulatedMachine, VirtualClock, SOURCE_REFS, load_firmware


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def _hmi(firmware):
    clock, machine = VirtualClock(), None
    machine = EmulatedMachine(clock)
    with firmware.activate():
        transport = firmware.adapter.PicoHMITransport(machine, clock)
    poller = firmware.hmi.PeripheralPoller(transport)
    poller.poll(clock.now_ms())
    return clock, machine, transport, poller


def _poll(clock, poller, duration, interval=20):
    target = clock.now_ms() + duration
    result = poller.snapshot(clock.now_ms())
    while clock.now_ms() < target:
        clock.sleep_ms(min(interval, target - clock.now_ms()))
        result = poller.poll(clock.now_ms())
    return result


def graph_connections(fw):
    _check(fw.peripherals.derive_wiring(fw.project) == fw.hmi.DEFAULT_WIRING,
           "actual HMI graph differs from firmware/model")
    graph = json.loads((fw.project / "design/E3.json").read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["components"]}
    pins = {ref: {pin["name"]: pin.get("net") for pin in parts[ref]["pins"]}
            for ref in ("U305", "U309", "U314", "Q306", "R393", "R395")}
    for gpio, net in {0: "UART7_RX", 1: "UART7_TX", 8: "IMU_RX", 9: "IMU_TX",
                      11: "E3_BUTTON_SENSE", 14: "E3_Q6A_ON_SENSE", 15: "SAFE_BOOT",
                      17: "E3_MCP_RESET_ASSERT", 18: "E3_FAN_EN", 19: "E3_BLOWER_EN",
                      22: "E3_FAN_TACH", 26: "E3_PANEL_TEMP", 27: "E1_BAT_ADC", 28: "E3_CASE_TEMP"}.items():
        _check(pins["U305"]["GP%d" % gpio] == net, "Pico graph/model GPIO mismatch")
    bno_links = {"GP2": "SCL_SPI_SCK", "GP3": "DI_SPI_MOSI", "GP4": "SDA_SPI_MISO",
                 "GP5": "CS_N", "GP6": "INT_N", "GP7": "RST_N", "GP8": "PS0"}
    for gpio, sensor in bno_links.items():
        _check(pins["U309"][gpio] == pins["U314"][sensor], "BNO SPI/strap graph link changed")
    _check(pins["U309"]["GP0"] == pins["U305"]["GP9"] == "IMU_TX" and
           pins["U309"]["GP1"] == pins["U305"]["GP8"] == "IMU_RX", "crossed UART graph changed")
    _check(pins["U314"]["PS1"] == pins["U314"]["VIN"] == "E3_IMU3V3", "BNO SPI supply strap changed")
    _check(pins["Q306"] == {"G": "E3_MCP_RESET_GATE", "S": "GND", "D": "E3_MCP_RESET_N"},
           "watchdog NFET graph changed")
    _check(set(pins["R395"].values()) == {"E3_PICO3V3", "E3_MCP_RESET_ASSERT"} and
           parts["R395"]["value"] == "1k" and
           set(pins["R393"].values()) == {"E3_MCP_RESET_ASSERT", "E3_MCP_RESET_GATE"},
           "powered high-Z watchdog bias graph changed")
    return {"graph": "design/E3.json", "hmi_derived_mapping": True,
            "pico_uart_adc_fan_gpio": True, "imu_spi_and_crossed_uart": True,
            "powered_reset_bias": "R395 1k Pico3V3 -> GP17/Q306 gate via R393"}


def pico_safe_gpio_and_adc(fw):
    clock, machine = VirtualClock(), EmulatedMachine()
    clock = machine.clock
    hardware = fw.adapter.Hardware(machine_module=machine)
    _check(machine.mcp_reset_asserted, "GP17 must assert reset at boot")
    _check(hardware.pins["disp_en"].value() == 0, "display enabled at boot")
    _check(hardware.pins["fan_en"].value() == 1 and hardware.pins["blower_en"].value() == 1,
           "fans not fail-safe on boot")
    sample = hardware.sample(clock.now_ms())
    _check(sample["battery_mv"] is None, "nominal ADC fixture became valid calibration")
    _check(abs(sample["panel_temp_c"] - 25) < 0.02, "25C NTC table conversion")
    machine.set_ntc_resistance(26, 2473.4)
    machine.set_ntc_resistance(28, 1862.3)
    sample = hardware.sample(clock.now_ms())
    _check(abs(sample["panel_temp_c"] - 60) < 0.02, "60C NTC point")
    _check(abs(sample["case_temp_c"] - 68) < 0.02, "68C NTC point")
    machine.set_ntc_resistance(26, None)
    machine.set_ntc_resistance(28, 0)
    sample = hardware.sample(clock.now_ms())
    _check(sample["panel_temp_c"] is None and sample["case_temp_c"] is None,
           "open/short NTC reused cached valid data")
    machine.set_battery_mv(12900)
    _check(hardware.sample(1)["battery_mv"] is None, "uncalibrated battery became valid")
    model = fw.supervisor.Supervisor()
    model.step(1, hardware.sample(1))
    accepted = model.receive({"v": 1, "t": "ARM", "s": model.session, "q": 0,
                              "p": {"qualified": True}}, 1)
    _check(not accepted and model.outputs["mcp_reset"], "ARM bypassed local commissioning")
    try:
        fw.calibration.validate({"v": 1, "crc32": "00000000"}, "EMU-PICO")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid ADC calibration accepted")
    return {"uncalibrated_battery": None, "open_short_invalid": True,
            "arm_refused": model.reject_reason, "synthetic_valid_records_created": 0}


def pico_power_uart_and_tach(fw):
    machine = EmulatedMachine()
    hardware = fw.adapter.Hardware(machine_module=machine)
    machine.Pin(14).drive(1)
    hardware.sample(0)
    _check(hardware.uart is not None and machine.Pin(15).mode == machine.Pin.OUT,
           "powered link did not assert SAFE_BOOT/select UART")
    _check(machine.Pin(0).mode == machine.Pin.ALT, "UART TX alternate function missing")
    machine.Pin(14).drive(0)
    hardware.sample(1)
    _check(hardware.uart is None and all(machine.Pin(n).mode == machine.Pin.IN for n in (0, 1, 15)),
           "unpowered Q6A link not high impedance")
    hardware.sample(2)
    _check(hardware.sample(2003)["fan_stalled"], "missing tach not detected")
    machine.Pin(22).drive(0)
    _check(not hardware.sample(2004)["fan_stalled"], "falling tach IRQ not connected")
    return {"q6a_off_pins_hiz": [0, 1, 15], "tach_irq": True,
            "fan_mechanical_performance": "UNSUPPORTED"}


def pico_watchdog_ticks_uart(fw):
    clock = VirtualClock(VirtualClock.TICKS_PERIOD - 5)
    machine = EmulatedMachine(clock)
    hardware = fw.adapter.Hardware(machine_module=machine)
    ticks = fw.adapter.TickClock(clock.ticks_ms, clock.ticks_diff)
    clock.sleep_ms(10)
    _check(ticks.now_ms() == 10, "actual TickClock failed at ticks wrap")
    machine.Pin(17).value(0)
    _check(not machine.mcp_reset_asserted, "model reset release wiring wrong")
    wdt = machine.WDT(timeout=1000)
    clock.sleep_ms(999)
    _check(machine.reset_count == 0, "WDT fired too early")
    wdt.feed()
    clock.sleep_ms(999)
    _check(machine.reset_count == 0, "feed did not move watchdog deadline")
    clock.sleep_ms(1)
    _check(machine.reset_count == 1 and machine.reset_reason == "WDT", "WDT did not expire")
    _check(machine.Pin(17).mode == machine.Pin.IN and machine.mcp_reset_asserted,
           "powered high-Z reset did not assert Q306 via R395")
    # Real firmware write_all sends a >TX-capacity packet through timed bytes.
    left, right = EmulatedMachine(clock), EmulatedMachine(clock, role="imu")
    tx, rx = left.UART(0, baudrate=115200, txbuf=64), right.UART(0, baudrate=115200, rxbuf=1024)
    tx.connect(rx)
    tx.max_write = 17
    packet = b"0123456789" * 40
    fw.adapter.write_all(tx, packet, clock.ticks_ms, clock.ticks_diff, clock.sleep_ms)
    clock.sleep_ms(50)
    _check(rx.read(512) == packet, "short UART writes lost interconnect bytes")
    tx.blocked = True
    start = clock.now_ms()
    try:
        fw.adapter.write_all(tx, b"x", clock.ticks_ms, clock.ticks_diff, clock.sleep_ms)
    except OSError:
        _check(clock.now_ms() - start == 100, "UART backpressure deadline not bounded")
    else:
        raise AssertionError("blocked UART did not time out")
    return {"ticks_wrap": True, "watchdog_pad_reset_ms": 1000,
            "short_write_bytes": len(packet), "backpressure_timeout_ms": 100,
            "instruction_level_restart": "UNSUPPORTED"}


def pi4io_keys_encoders(fw):
    clock, machine, transport, poller = _hmi(fw)
    _check(machine.pi4io.registers[2:] == bytearray((0, 0, 0, 0, 255, 0)),
           "actual firmware did not program separate register pairs")
    # A six-byte read starting2 repeats2/3, independently of driver assumptions.
    _check(machine.pi4io.read(2, 6) == bytes(6), "PI4IO pair pointer model")
    machine.pi4io.set_key(0, True)
    _check(machine.Pin(10).value() == 0 and transport.interrupt_pending(), "key INT disconnected")
    result = _poll(clock, poller, 60)
    _check(result["keys"] == 1 and result["presses"][0] == 1, "debounced HOME not captured")
    _check(machine.Pin(10).value() == 1, "input pair read did not clear INT")
    machine.pi4io.set_key(0, False)
    machine.pi4io.set_key(7, True)
    machine.turn_encoder(1, cycles=3)
    machine.turn_encoder(2, cycles=2, reverse=True)
    result = _poll(clock, poller, 60)
    _check(result["keys"] == 128 and result["presses"] == [1, 0, 0, 0, 0, 0, 0, 1],
           "key wiring order/counters wrong")
    _check(result["encoders"] == [3, -2], "GPIO IRQ quadrature cycles not delivered")
    before = result["generation"]
    # Simultaneous missed diagonal must be rejected rather than movement.
    irq = machine.disable_irq()
    machine.Pin(2).drive(0)
    machine.Pin(3).drive(0)
    machine.enable_irq(irq)
    result = _poll(clock, poller, 20)
    _check(not result["ok"] and result["generation"] != before, "invalid encoder interval reused")
    return {"key_order": list(fw.hmi.KEY_NAMES), "encoder_cycles": [3, -2],
            "active_low_interrupt": True, "invalid_transition_rebaseline": True}


def pi4io_fault_recovery(fw):
    clock, machine, transport, poller = _hmi(fw)
    machine.pi4io.connected = False
    result = _poll(clock, poller, 20)
    _check(not result["ok"], "unplugged expander retained valid input")
    generation = result["generation"]
    machine.pi4io.connected = True
    machine.pi4io.reset()
    machine.pi4io.set_key(2, True)
    result = _poll(clock, poller, 1100)
    _check(result["ok"] and result["keys"] == 4 and result["presses"][2] == 0,
           "reconnection invented held REC press")
    _check(result["generation"] >= generation, "generation lost on recovery")
    machine.pi4io.registers[6] = 0
    result = _poll(clock, poller, 1000)
    _check(not result["ok"] or result["generation"] > generation, "config corruption not detected")
    _poll(clock, poller, 1100)
    for fault in ("short", "nack", "corrupt"):
        # Read corruption targeted at periodic configuration readback.
        if fault == "corrupt":
            poller._verify_at = clock.now_ms()
        machine.i2c_fault = fault
        result = _poll(clock, poller, 20)
        _check(not result["ok"], "fault %s was not invalidated" % fault)
        _poll(clock, poller, 1100)
    machine.Pin(5).drive(0)
    poller._configured, poller._recover = False, True
    poller._retry_at = clock.now_ms()
    result = _poll(clock, poller, 20)
    _check(not result["ok"], "stuck SCL accepted")
    machine.Pin(5).drive(1)
    result = _poll(clock, poller, 1100)
    _check(result["ok"], "SCL release failed recovery")
    _check(not poller.snapshot(clock.now_ms() + 100)["fresh"], "stale keys stayed fresh")
    return {"faults": ["unplug", "register_reset", "short_read", "nack", "corrupt_read", "scl_stuck"],
            "recovery": True, "held_key_replay": False}


def veml_conversion_fault_age(fw):
    clock, machine, transport, poller = _hmi(fw)
    _check(machine.veml.registers[0] == 0x1300, "configuration endian mismatch")
    _check(not poller.snapshot(0)["lux_valid"], "unconverted ALS fixture was fresh")
    result = _poll(clock, poller, 100)
    _check(result["lux_valid"] and abs(result["lux"] - 215.04) < 0.001,
           "independent VEML resolution/byte order mismatch")
    _check(machine.veml.conversions > 0 and result["lux_age_ms"] >= 33, "conversion age absent")
    # Changing ambient scene is not an immediate bus register write.
    machine.veml.lux = 4.2
    result = _poll(clock, poller, 100)
    _check(machine.veml.registers[0] == 0x08c0 and not result["lux_valid"],
           "dark profile switch failed")
    result = _poll(clock, poller, 1080)
    _check(not result["lux_valid"], "long integration read prematurely fresh")
    result = _poll(clock, poller, 20)
    _check(result["lux_valid"] and abs(result["lux"] - 4.2) < 0.001,
           "long integration fixture not decoded")
    payload = fw.main.hmi_payload(poller, clock.now_ms())["hmi"]
    _check(payload["lux_age_ms"] == result["lux_age_ms"] + 100, "source UART age lost")
    _check(not poller.snapshot(clock.now_ms() + 2000)["lux_valid"], "expired ALS remained valid")
    machine.veml.connected = False
    result = _poll(clock, poller, 1100)
    _check(not result["lux_valid"] and result["lux"] is None, "unplug reused cached lux")
    machine.veml.connected = True
    machine.veml.reset()
    machine.veml.lux = 215.04
    result = _poll(clock, poller, 1500)
    _check(result["lux_valid"], "ALS reconnect failed")
    machine.veml.override_raw = 65535
    result = _poll(clock, poller, 100)
    _check(not result["lux_valid"] and result["lux"] is None, "saturated lux retained")
    return {"little_endian": True, "profiles": ["gain1/8_IT25", "gain2_IT800"],
            "integration_tolerance_percent": 30, "source_uart_budget_ms": 100,
            "faults": ["unplug", "stale", "saturation"], "optical_accuracy": "UNSUPPORTED"}


class _IMUHarness:
    def __init__(self, fw):
        self.fw, self.clock = fw, VirtualClock()
        self.machine = EmulatedMachine(self.clock, role="imu")
        pin = self.machine.Pin
        cs, wake, reset = pin(5, pin.OUT, value=1), pin(8, pin.OUT, value=1), pin(7, pin.OUT, value=1)
        interrupt = pin(6, pin.IN, pin.PULL_UP)
        self.edge_at = None
        interrupt.irq(handler=self.mark, trigger=pin.IRQ_FALLING, hard=True)
        spi = self.machine.SPI(0, baudrate=1000000, polarity=1, phase=1, bits=8,
                               firstbit=self.machine.SPI.MSB, sck=pin(2), mosi=pin(3), miso=pin(4))
        self.transport = fw.device.SPITransport(spi, cs, interrupt, wake, reset, self.clock,
                                                lambda: self.edge_at)
        self.restart()

    def mark(self, pin):
        self.edge_at = self.clock.now_ms()

    def restart(self):
        self.transport.hardware_reset()
        self.decoder = self.fw.shtp.SHTPDecoder()
        self.session = self.fw.session.ImuSession(self.clock.now_ms())
        self.commands = [self.session.first_command()]
        for unused in range(16):
            if not self.commands and self.machine.Pin(6).value():
                break
            self.consume()
        _check(self.session.state == "WAIT_FIRST", "Product/GetFeature handshake failed")

    def consume(self):
        command = self.commands.pop(0) if self.commands else None
        packet, noticed = self.transport.transaction(command)
        events = []
        if packet is not None:
            for channel, payload in self.decoder.feed(packet):
                commands, received = self.session.receive(channel, payload, self.clock.now_ms(),
                                  rx_latency_ms=self.clock.now_ms() - noticed)
                self.commands.extend(commands)
                events.extend(received)
        return events

    def rotation(self, **kwargs):
        self.machine.bno.queue_rotation(**kwargs)
        return self.consume()


def bno_spi_handshake_and_reports(fw):
    harness = _IMUHarness(fw)
    _check(harness.machine.bno.first_interrupt_with_wake_high, "PS0 changed before first INT")
    _check([packet[0] for packet in harness.machine.bno.commands] == [0xf9, 0xfd, 0xfe],
           "driver did not execute exact Product/Set/Get feature handshake")
    event = harness.rotation()[0]
    _check(event["ok"] and event["quaternion"] == [0, 0, 0, 1], "Q14 rotation not decoded")
    _check(event["heading_accuracy_rad"] == 0.125, "Q12 accuracy not decoded")
    event = harness.rotation(status=0)[0]
    _check(not event["ok"] and event["quaternion"] is None, "unreliable accuracy passed orientation")
    _check(harness.rotation()[0]["ok"], "new good report did not recover accuracy")
    event = harness.rotation(sample_sequence=7)[0]
    _check(not event["ok"] and event["error"] == "report_sequence", "sensor gap not rejected")
    return {"commands": ["ProductID", "SetFeature0x05", "GetFeature0x05"],
            "synthetic_product_id": hex(0xe0000001), "q14": True, "q12": True,
            "status0_invalid": True, "report_gap_invalid": True,
            "sensor_fusion_and_calibration": "UNSUPPORTED"}


def bno_spi_fault_reset_recovery(fw):
    harness = _IMUHarness(fw)
    harness.rotation()
    harness.machine.bno.connected = False
    harness.machine.Pin(6).drive(0)
    try:
        harness.consume()
    except OSError:
        pass
    else:
        raise AssertionError("disconnected SPI returned valid data")
    harness.machine.bno.connected = True
    harness.restart()
    _check(harness.rotation()[0]["ok"], "reset/rehandshake did not restore new report")
    faults = []
    for length, reason in ((0xffff, "reserved_length"), (0x8017, "continuation_unsupported"), (3, "packet_length")):
        harness.machine.bno.queue_rotation()
        harness.machine.bno.corrupt_next_header(length)
        try:
            harness.consume()
        except fw.shtp.ImuError as error:
            _check(str(error) == reason, "wrong corrupt-header failure")
            faults.append(reason)
        else:
            raise AssertionError("bad SHTP header accepted")
        harness.restart()
    event = harness.rotation(age_ms=500)[0]
    _check(not event["ok"] and event["quaternion"] is None, "expired sensor cargo accepted")
    harness.restart()
    harness.rotation()
    harness.clock.sleep_ms(500)
    event = harness.session.tick(harness.clock.now_ms())
    _check(event and not event["ok"] and event["error"] == "sample_timeout", "silent sensor retained orientation")
    # Disconnected INT must time out the real reset transport, not fake a chip ID.
    harness.machine.bno.connected = False
    harness.machine.Pin(6).drive(1)
    start = harness.clock.now_ms()
    try:
        harness.transport.hardware_reset()
    except fw.shtp.ImuError as error:
        _check(str(error) == "interrupt_timeout", "missing INT wrong failure")
    else:
        raise AssertionError("missing INT accepted")
    _check(harness.clock.now_ms() - start == 1030, "reset/INT timeout not bounded")
    return {"faults": ["spi_unplug", "missing_interrupt", *faults, "sensor_age500", "silence500"],
            "reset_and_exact_rehandshake": True, "startup_timeout_ms": 1030}


def imu_uart_to_pico_relay(fw):
    harness = _IMUHarness(fw)
    clock, machine = harness.clock, harness.machine
    pico = EmulatedMachine(clock)
    pack_uart = machine.UART(0, baudrate=115200, txbuf=512, rxbuf=128)
    pico_uart = pico.UART(1, baudrate=115200, rxbuf=1024)
    pack_uart.connect(pico_uart)
    pack_uart.max_write = 13
    publisher = fw.device.UARTPublisher(pack_uart, 1234)
    decoder, relay = fw.wire.FrameDecoder(), fw.relay.IMURelay()
    publisher.send("HELLO", {"role": "imu", "protocol": 1,
                             "report_interval_us": 200000, "freshness_ms": 500}, clock.now_ms())
    event = harness.rotation()[0]
    event["age_ms"] += fw.device.TX_BUDGET_MS
    publisher.send("EVENT", {"imu": event}, clock.now_ms())
    frames, forwarded = [], []
    for unused in range(50):
        publisher.pump(clock.now_ms())
        clock.sleep_ms(2)
        data = pico_uart.read(512)
        if data:
            for frame in decoder.feed(data):
                frames.append(frame)
                payload = relay.receive(frame, clock.now_ms(), rx_age_ms=100)
                if payload is not None:
                    forwarded.append((payload, clock.now_ms()))
        if not publisher.pending_frames and pack_uart.txdone():
            break
    _check([frame["t"] for frame in frames] == ["HELLO", "EVENT"], "UART fragmentation lost frames")
    _check(decoder.errors == 0 and forwarded[-1][0]["imu"]["ok"], "real relay rejected new report")
    payload, received_at = forwarded[-1]
    _check(payload["imu"]["age_ms"] >= 250, "source+Pico RX ages lost")
    clock.sleep_ms(70)
    aged = relay.forwarding({"imu": dict(payload["imu"])}, received_at, clock.now_ms())
    _check(aged["imu"]["age_ms"] >= 320, "queue age reset on forwarding")
    clock.sleep_ms(250)
    expired = relay.forwarding({"imu": dict(payload["imu"])}, received_at, clock.now_ms())
    _check(expired is None or not expired["imu"]["ok"], "expired forwarded orientation stayed valid")
    replay = relay.receive(frames[-1], clock.now_ms(), rx_age_ms=100)
    _check(replay is not None and not replay["imu"]["ok"], "replayed UART became valid")
    # Cable unplug does not fake an acknowledgement or fresh receive time.
    pico_uart.connected = False
    before = pico_uart.any()
    pack_uart.write(b"unplugged")
    clock.sleep_ms(10)
    _check(pico_uart.any() == before, "disconnected UART delivered bytes")
    blocked = fw.device.UARTPublisher(pack_uart, 999)
    blocked.send("HELLO", {"role": "imu", "protocol": 1}, clock.now_ms())
    pack_uart.blocked = True
    started = clock.now_ms()
    blocked.pump(started)
    clock.sleep_ms(100)
    try:
        blocked.pump(clock.now_ms())
    except fw.shtp.ImuError as error:
        _check(str(error) == "uart_tx_timeout", "bad publisher timeout")
    else:
        raise AssertionError("publisher backpressure did not expire")
    return {"actual_paths": ["SPITransport", "SHTPDecoder", "ImuSession", "UARTPublisher", "FrameDecoder", "IMURelay"],
            "partial_write_limit": 13, "source_budget_ms": 150, "pico_rx_budget_ms": 100,
            "wait_age_added_ms": 70, "replay_rejected": True, "unplug": True,
            "sensor_values": "SYNTHETIC_TEST_FIXTURE"}


CASES = (
    ("graph_connections", ("pico_gpio_supervisor", "pi4io9555_keys", "pico_encoders", "veml7700",
                           "pico_adc_ntc_battery", "pico_fan_tach", "pico_watchdog_clock",
                           "pico_uart", "bno085_spi_shtp", "external_imu_uart"), graph_connections),
    ("pico_safe_gpio_and_adc", ("pico_adc_ntc_battery", "pico_gpio_supervisor"), pico_safe_gpio_and_adc),
    ("pico_power_uart_and_tach", ("pico_gpio_supervisor", "pico_fan_tach"), pico_power_uart_and_tach),
    ("pico_watchdog_ticks_uart", ("pico_watchdog_clock", "pico_uart"), pico_watchdog_ticks_uart),
    ("pi4io_keys_encoders", ("pi4io9555_keys", "pico_encoders"), pi4io_keys_encoders),
    ("pi4io_fault_recovery", ("pi4io9555_keys", "pico_encoders"), pi4io_fault_recovery),
    ("veml_conversion_fault_age", ("veml7700" ,), veml_conversion_fault_age),
    ("bno_spi_handshake_and_reports", ("bno085_spi_shtp",), bno_spi_handshake_and_reports),
    ("bno_spi_fault_reset_recovery", ("bno085_spi_shtp",), bno_spi_fault_reset_recovery),
    ("imu_uart_to_pico_relay", ("external_imu_uart", "pico_uart"), imu_uart_to_pico_relay),
)


def run(project=None):
    """Return deterministic, JSON-serializable module/case emulation evidence."""
    fw = load_firmware(project)
    cases = []
    with fw.activate():
        for name, modules, function in CASES:
            try:
                details = function(fw)
                result = {"case": name, "status": "EMULATION_PASS", "modules": list(modules), "details": details}
            except Exception as error:
                result = {"case": name, "status": "EMULATION_FAIL", "modules": list(modules),
                          "error": type(error).__name__ + ": " + str(error)}
            cases.append(result)
    modules = []
    for name in sorted({name for unused, names, function in CASES for name in names}):
        associated = [case for case in cases if name in case["modules"]]
        modules.append({"module": name,
                        "status": "EMULATION_PASS" if all(case["status"] == "EMULATION_PASS" for case in associated) else "EMULATION_FAIL",
                        "physical_qualified": False, "cases": [case["case"] for case in associated],
                        "source_refs": dict(SOURCE_REFS)})
    actual_sources = ("firmware/pico/adapter.py", "firmware/pico/hmi.py", "firmware/pico/main.py",
                      "firmware/pico/supervisor.py", "firmware/pico/calibration.py",
                      "firmware/pico/imu_relay.py", "firmware/imu/device.py", "firmware/imu/shtp.py",
                      "firmware/imu/session.py", "software/srrx/wire.py", "software/srrx/peripherals.py",
                      "design/E3.json", "design/E5.json")
    source_hashes = {name: hashlib.sha256((fw.project / name).read_bytes()).hexdigest()
                     for name in actual_sources}
    return {"schema": 1, "status": "EMULATION_PASS" if all(case["status"] == "EMULATION_PASS" for case in cases) else "EMULATION_FAIL",
            "physical_qualified": False, "commissioning_records_created": 0,
            "scope": "actual portable Pico/IMU drivers connected to independent host MCU/register models",
            "modules": modules, "cases": cases,
            "unsupported": ["instruction-level RP2040/MicroPython execution", "UF2/USB boot/flash",
                            "complete power loss/brownout/electrical backfeed", "IRQ latency under real GC",
                            "electrical SPI/I2C timing and signal integrity", "ADC calibration or acceptance",
                            "BNO sensor fusion/magnetics/calibration", "optical/thermal/fan mechanics", "USB touch"],
            "source_refs": dict(SOURCE_REFS), "source_sha256": source_hashes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run(args.project)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if report["status"] == "EMULATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
