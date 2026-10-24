# Pico supervisor firmware

This directory contains implemented Python firmware and an executable host-side
state model for genuine non-wireless Raspberry Pi Pico SC0915 (RP2040). It has
**not been flashed, measured, or qualified on the assembled receiver**. Unit tests
prove software transitions with simulated inputs; they do not close E3 hardware
acceptance gates. Both the Pico and host must refuse ARM until their separate
commissioning records pass. No valid calibration or commissioning record ships
in this repository.

## Files and deployment

`supervisor.py` has no hardware dependency. `adapter.py` implements GPIO/ADC,
tachometer edges, tick unwrapping and bounded UART writes. `boot.py` establishes
safe outputs before application imports. `main.py` runs the 20 ms nominal loop
with a 1000 ms RP2040 hardware watchdog. `calibration.py` validates device-bound
records and provides a CPython calibration CLI. `imu_relay.py` validates the
separate IMU-pack stream; its SPI/sensor firmware lives in `firmware/imu/`.

Use the pinned official UF2 `RPI_PICO-20250809-v1.26.0.uf2` from the
[RPI_PICO download](https://micropython.org/download/RPI_PICO/) (MicroPython
**v1.26.0**, the API reference target): 668,672 bytes, SHA-256
`3fb807524074c75694bd4b13a587dc8673e0815d393a5bdfc250c7cd561b34df`, recorded with
the erase image and the mpremote version in `firmware/runtime.lock.json`. Copy the
SHA-256 into the unit acceptance log and run the device tests with that exact build.
Do not deploy a Pico W/Pico 2 or overclocked build. The code explicitly sets 125 MHz
and leaves GP23 and USB clocks at their default settings pending the STACK RF A/B test.

With the main switch on or the Pico physically isolated from LAB5, and no receiver
load connected, flash with `tools/flash_mcu.py` (software/DEPLOYMENT.md, "Прошивання
MCU"). Every command is a dry run without `--execute`; mpremote must be the locked
1.26.0 from `firmware/mpremote-requirements.txt`:

```sh
# 1. BOOTSEL held while plugging USB: the RPI-RP2 drive appears. A Pico that already
#    runs main.py has a 1000 ms WDT that a REPL cannot stop, so erase it first:
python3 tools/flash_mcu.py uf2 --role pico --image erase --file nuke_universal.uf2 --drive /media/$USER/RPI-RP2 --execute
# 2. When RPI-RP2 is back (or after BOOTSEL again), the pinned MicroPython:
python3 tools/flash_mcu.py uf2 --role pico --file RPI_PICO-20250809-v1.26.0.uf2 --drive /media/$USER/RPI-RP2 --execute
# 3. Serial for provisioning (srrx.provision prepare, calibration.py --serial):
python3 tools/flash_mcu.py serial --port /dev/ttyACM0
# 4. Files from firmware/dist/pico-micropython-files.zip in order, records only if they
#    validate for this unit_id, on-device SHA-256 of every file, then reset:
python3 tools/flash_mcu.py install --role pico --port /dev/ttyACM0 [--records /path/to/provisioned] --execute
```

`install` refuses a different mpremote, MicroPython release or board name, a
non-empty filesystem, records sealed for another serial and any extra or different
file after copying. The manual equivalent it replaces, for review only:

```sh
mpremote fs cp firmware/pico/boot.py :boot.py
mpremote fs cp firmware/pico/supervisor.py :supervisor.py
mpremote fs cp firmware/pico/calibration.py :calibration.py
mpremote fs cp firmware/pico/adapter.py :adapter.py
mpremote fs cp firmware/pico/imu_relay.py :imu_relay.py
mpremote fs cp firmware/pico/hmi.py :hmi.py
mpremote fs cp software/srrx/wire.py :wire.py
mpremote fs cp firmware/pico/main.py :main.py
mpremote reset
```

Copy the reviewed `boot.py` first and `main.py` last. No receiver load should be
connected during first flash. GP17 must remain HIGH and the display supply OFF.
With no records, HELLO/STATUS report false commissioning/calibration gates and
HELLO a null `qualification_record`; STATUS supplies `adc_raw` for bench work. Use UART7/115200 8N1 with the host, not
REPL text. USB REPL remains a service path, subject to the LAB5 isolation rule.

## Hardware outputs

The authoritative connection list is `design/E3.json`, U305. GPIO numbers below
are RP2040 GPIO, with physical Pico header numbers in parentheses.

| Function | GPIO (header) | State and polarity |
|---|---|---|
| MCP reset actuator | GP17 (22) | HIGH asserts all three MCP pin18 RESET low; actively LOW releases |
| Display eFuse | GP16 (21) | HIGH enables with Q6A 3V3 present in SAFE/WARMING/CONFIGURING/ACTIVE/TRIPPED; LOW in SHUTTING_DOWN/OFF, after a CASE_HOT or FAN_STALLED trip until the next accepted ARM or physical restart, at panel NTC >=68 C or invalid/stale, re-enabled at <=60 C |
| SAFE_BOOT | GP15 (20) | HIGH asserts; input/high impedance while Q6A is off |
| Noctua high-side driver | GP18 (24) | HIGH enables DC power; no fan PWM |
| Delta two-wire blower | GP19 (25) | HIGH enables DC power |
| Pololu OFF | GP13 (17) | HIGH for 250 ms when cutting power |
| Q6A key transistor | GP12 (16) | HIGH turns Q302 on and pulls J21 pin 3 (PWR_ON_KEY) low: bounded 900 ms boot-assist pulses only while Q6A 3V3 is absent (see "Q6A power-on key" below); LOW otherwise. The physical button reaches the same node through D303 |
| Piezo/status LED | GP20 (26)/GP21 (27) | Piezo silent; LED high outside ACTIVE |
| Q6A power sense | GP14 (19) | Active high, external 10k/100k network |
| Power button | GP11 (15) | Active low, external pullup/BAT54 |
| Fan tachometer | GP22 (29) | Falling-edge IRQ, external pullup to Pico 3V3 |
| ADC panel/battery/case | GP26/27/28 (31/32/34) | Three external ADC inputs; battery divider belongs to E1 |
| Host UART0 TX/RX | GP0/1 (1/2) | 115200; TX input/high impedance while Q6A is off |
| IMU UART1 RX | GP9 (12); GP8 (11) | 115200 RX-only framed pack telemetry, independent of Q6A power; GP8 (pack RX) is returned to high-Z input after UART1 setup |

GP2/3 and GP6/7 read the two encoders; GP4/5 and GP10 serve the local HMI
I2C/interrupt. `hmi.py` implements the PI4IOE5V9555 keys and VEML7700 sensor,
with bounded EVENT telemetry documented in `software/PERIPHERALS.md`. These
inputs never authorize power outputs. GP17 is committed to reset and must
never be used for display brightness. Physical HMI timing and wiring remain
subject to unit acceptance.

## Session, ARM and trip contract

Frames use the shared `software/PROTOCOL.md` codec. `Supervisor.receive(frame,
now_ms)` accepts HB, ARM, CONFIGURED, TRIP and SHUTDOWN. `step(now_ms, inputs)`
requires fresh local inputs; `status()` returns a plain payload. `outputs` is a
dictionary of logical assertions. All model times must be nonnegative,
monotonically increasing milliseconds. `TickClock` uses `ticks_diff` to unwrap
MicroPython's wrapping counter before calling the model. Its sampling gap must
remain below half the ticks period; a reversed/ambiguous clock fails closed.

1. Boot is SAFE: MCP reset asserted, both fans on. DISP12 powers the operator
   console whenever Q6A 3V3 is present and the panel NTC is valid and cool
   (Display eFuse row above); it is never an ARM output. The Pico chooses a
   new nonzero uint32 session using `os.urandom`. HELLO is the first frame of
   each session. It carries the STATUS state/readiness fields
   (`main.HELLO_FIELDS`) but no sensor readings, plus the actual Pico serial,
   the exact local `calibration_crc32` (None if invalid) and the
   `qualification_record` of a valid local commissioning record (None
   otherwise). Battery, temperatures, fan and brightness follow in STATUS
   within 200 ms. The worst-case HELLO is at most 452 of 512 bytes and holds
   no float. labd must match serial, calibration CRC and qualification record
   against its acceptance file before ARM.
2. Host sends ARM with `p.qualified=true`, current Pico session and a strictly
   increasing uint32 sequence. Pico separately requires a validated local ADC
   calibration, a local commissioning record, Q6A power, fresh valid sensors,
   battery above 13.05 V, panel below 68 C and case at most 60 C. Refused ARM
   leaves reset asserted and reports its reason.
3. WARMING holds reset for at least 100 ms and waits for two distinct fresh HB
   observations after ARM. Multiple packets received at one timestamp count as
   one observation. Host sends HB every 200 ms while its STATUS readings are
   fresh (<=500 ms).
4. Pico actively drives GP17 LOW and enters CONFIGURING. Host must write safe
   MCP registers and reply CONFIGURED with `p.safe=true` within 1000 ms. Reset
   defaults and application pulldowns must be measured, not inferred from ACK.
   Write the safe OLAT image (CHG_INHIBIT=1, other controls=0) before IODIR outputs;
   configure IOCON ODR/MIRROR before GPINTEN;
   honor the MCP23017 IO7 output restriction. CONFIGURED is a host assertion,
   not an independent Pico readback of the I2C bus.
5. ACTIVE keeps reset released; host independently controls its qualified MCP
   loads. An HB gap of **750 ms or greater**, stale/invalid local sensor, loss
   of Q6A, hot panel/case, tach stall, bad configuration or host TRIP asserts
   reset and restores full cooling. Low battery while armed is left to the host
   dwell, but never masks the panel/case/tach trips. DISP12 stays on in TRIPPED
   so the console can show the fault and RECOVER + ARM, unless Q6A is off, the
   panel is hot, or the trip was CASE_HOT or FAN_STALLED. Those two remove the
   display load until a new ARM is accepted (which itself needs case <=60 C and
   no stall) or a physical restart; a later host TRIP relabelling the fault does
   not relight it. With the console dark, recover through the local CLI
   (`labctl recover` or `labctl arm`). The trip rotates the nonce and
   clears accepted host sequence/HB state. Old-session frames and duplicate or
   decreasing sequences cannot refresh HB. Sequence numbers never wrap.
6. New-session heartbeat alone never recovers power. A new explicit, qualified
   ARM and the entire initialization handshake are required.

These are state-machine deadlines. Physical assertion includes loop/UART/ADC
latency, which must be scoped and recorded. Before each bounded UART transmit,
the firmware re-samples safety inputs and applies the current outputs. The
1000 ms hardware WDT is fed only after the loop's safety work; interpreter hangs
must reset the MCU rather than keep a timer-based feeder alive.

## Shutdown, button and cooling

The bounded subset of STACK sections 5.1/5.6 is implemented as follows:

| Condition | Action |
|---|---|
| SHUTDOWN `phase=ARM_OFF` | SHUTTING_DOWN, immediate MCP reset and DISP off; emit SHUTDOWN_REQUEST |
| SHUTDOWN `phase=OFF_NOW`, after ARM_OFF | Cut Pololu after exactly 20 s model grace; repeated OFF_NOW cannot postpone it; each new ARM_OFF or button shutdown starts without a previous OFF_NOW timestamp |
| No HB after ARM_OFF | Cut after 60 s from last shutdown HB or ARM_OFF, whichever is later |
| Q6A 3V3 falls after being observed on, or is absent at the first sample after a WDT reboot | Reset immediately; Pololu OFF after 3 s |
| Calibrated battery <=13.05 V with no fresh HB | Pololu OFF after continuous 5 s; recovery or fresh HB resets dwell. Same 13050 mV as the host graceful cutoff, above the 12.8 V hardware UV trip |
| Battery low with live HB | Host implements the INA228/Linux graceful shutdown policy; this fallback does not replace it. labd sends HB only while it holds STATUS readings no older than 500 ms (a HELLO carries none), so a host that cannot see the battery leaves this fallback active |
| Physical button | 30 ms debounce; short release emits POWER_BUTTON, 1.5 s hold requests graceful shutdown |
| Restart after OFF | Physical button edge and battery >=13.6 V clear software latch and re-arm the PWR_ON_KEY assist; remote ARM alone cannot restart |
| Q6A 3V3 absent after a Pico power-on or restart | Bounded PWR_ON_KEY pulses on GP12, below |
| Host maximum SoC temperature | In hardware mode labd sends `soc_temp_c` in every HB: the hottest Linux thermal zone in C, 0.1 C steps, re-read at most once a second on a separate labd thread (`SocTempSampler`), outside the 20 ms safety tick (`software/PROTOCOL.md`). Fan on at60 C, off at50 C. labd omits the field when a zone is unreadable or out of range, when the cached sample is older than 3 s, and in simulation; a missing/nonfinite value or stale HB forces full cooling (fan on) |
| Panel NTC | Blower on at45 C, off at40 C; invalid sensor forces full cooling |
| Fan tach | Ignore while off and first2 s on; no edge for >2 s thereafter is FAN_STALLED |

OFF is software latched after a 250 ms GP13 pulse; physical hardware must remove
LAB5. Software does not claim that case NTC is a battery-cell sensor. Cell
temperature and charger inhibition remain host/charger/AON responsibilities.
`brightness_limit_pct` requests 50% at60 C and20% at68 C, but there is no proven
DDC/KEY path here. The supervisor instead removes DISP12 at68 C, or when the
panel NTC reading is missing, invalid or older than 250 ms, and restores it only
after a fresh valid reading of at most60 C. It does not pretend to dim GP17 or
modify an undocumented panel interface.

## Q6A power-on key (PWR_ON_KEY, B11)

GP12 drives Q302 (2N7002, R331 100k gate pulldown), which pulls J21 pin 3
(PWR_ON_KEY) low. The case button reaches the same node through D303, so both
press the Q6A PMIC key; D303 keeps the Pico pulse off GP11. The supervisor
implements the STACK D3 boot assist as a bounded state machine (the `KEY_*`
constants in `supervisor.py`):

| Rule | Behavior |
|---|---|
| Armed by | The first supervisor sample after a Pico power-on (LAB5 on: `main.run()` passes `power_on_reset` when `machine.reset_cause() == machine.PWRON_RESET`), and a PHYSICAL_RESTART from OFF |
| Not armed | After a WDT reboot or `machine.reset()` (`WDT_RESET` on rp2): Q6A 3V3 absent at the first sample counts as a Q6A that just went off, so no pulse and the 3 s Pololu OFF follows unless 3V3 appears. Such a reboot can land inside the 3 s window of a poweroff or J21 UVLO trip; a press there would restart the Q6A the user just shut down. MicroPython reports a RUN-pin reset as PWRON_RESET; RUN is a service line from the Q6A, which has 3V3 then |
| First pulse | Q6A 3V3 (GP14) still absent 1500 ms later. STACK allows 1-2 s; the wait counts from the first sample, MicroPython boot time comes on top and is measured in B11 |
| Pulse | GP12 HIGH for 900 ms (STACK 0.8-1.0 s, never 2 s; a 6 s hold is the Q6A hard power-off) |
| Retries | Next pulse 5000 ms after each release, at most 3 pulses; then Q6A_KEY_GAVE_UP and no pulse until a physical restart or the next power-on |
| Released at once | GP14 high (`Hardware.apply` re-reads it just before the write), any state but SAFE, no sample within 250 ms (that press ends and counts; the next try waits 5000 ms), reversed clock, case button pressed, or, on a calibrated Pico only, battery invalid or <=13.05 V |
| Postponed | While the case button is pressed (below 1.5 s) or a calibrated battery is invalid or <=13.05 V; the full wait restarts after the release |
| Ended | A case-button hold of 1.5 s or more, timed from the Pico's first debounced sample, requests the graceful BUTTON shutdown (SHUTTING_DOWN), which ends the assist for this boot; without HB #2813 opens 60 s later (ARM_OFF_HEARTBEAT_LOST). A long power-on press still held when the Pico starts sampling counts too, so keep the power-on press shorter than 1.5 s |
| Never | After Q6A 3V3 was seen since this power-on or restart: a later loss (poweroff, J21 UVLO) leads to the 3 s Pololu OFF, never to a key press, even if the Pico WDT-reboots in between |

Uncalibrated, the Pico trusts no battery value and pulses anyway; E1's hardware
UV trip still applies. A calibrated Pico never presses below the 13.05 V cutoff,
because the no-HB UV fallback would cut a booting Q6A. A hung loop leaves GP12
HIGH only until the 1000 ms hardware WDT returns the pads to high impedance and
R331 turns Q302 off: at most 880 + 1000 = 1880 ms, still below 2 s (module-lab
case `pico_q6a_power_key_pulse`). A Pico that keeps resetting never presses
again: WDT reboots do not arm the assist, and the first one that finds 3V3
absent opens #2813 after 3 s, which also ends a WDT boot loop with the Q6A off.
A WDT reboot during a cold start therefore ends in OFF, and the operator
restarts with the case button. `boot.py`, `Hardware()` and `fail_safe()` drive
GP12 LOW.

STATUS reports `q6a_key_pulses` (0..3 since this power-on or restart), so
`labctl status` shows whether the Q6A started after the Pico pulse (1..3) or
without one (0): by itself on the 12 V ramp, or from the case-button press,
which reaches J21 pin 3 through D303. The counter cannot tell those two apart;
judge 12 V auto-start (Ж-02) with 12 V applied and no button press. Events
emitted while the Q6A is off are dropped with the unpowered link, so this
counter is the only record that reaches labd.

J21 UVLO restart path (`design/E2.json` R-E2-20): a UVLO trip removes Q6A power;
the Pico sees 3V3 fall after it was on, holds MCP reset and opens #2813 after
3 s (latched OFF), with no key press in that window, also when the Pico
WDT-reboots inside it. The button restart at >=13.6 V powers LAB5 again and the
new Pico power-on runs this assist, so a Q6A that does not start by itself on the 12 V
ramp (11-54 ms in the E2 model, inside the wait) gets the bounded pulse. If the Pico is still
powered in OFF (LAB5 not removed), the PHYSICAL_RESTART edge re-arms the same
assist. Model, adapter and deployed loop are host-tested; the pulse width at J21
pin 3, the PMIC response and the B11 20/20 start stay OPEN (`build/09-testy.md`
Ж-02 and Ж-02a).

## Calibration and commissioning

Before recording ADC points, verify factory R7 is removed, LM4040 3.0 V is the
sole reference, and E1's 100k/20k divider samples E1_SW. Measure two pack-equivalent
voltages at least2 V apart (for example12.6 V and16.4 V) with a calibrated meter.
Record `ADC.read_u16()` counts, not12-bit datasheet codes. Use independently
measured panel/case temperature offsets and an instrument/log identifier:

```sh
python firmware/pico/calibration.py --serial ACTUAL_PICO_HEX_ID \
  --raw-low MEASURED_U16 --mv-low MEASURED_MV \
  --raw-high MEASURED_U16 --mv-high MEASURED_MV \
  --panel-offset-c MEASURED_OFFSET --case-offset-c MEASURED_OFFSET \
  --reference-id INSTRUMENT_AND_LOG_ID --output calibration.json
```

The helper derives the fit and seals integer fixed-point fields: `scale_nv_per_count`
(220000..340000 nV/count), `offset_uv` (+/-1000000 uV) and `panel_offset_mc`/`case_offset_mc`
(+/-10000 milli-C). It writes a CRC32 record bound to exact revision `E3-v2.1` and
Pico serial, with no nominal valid defaults. The fixed canonical CRC field order is
in `calibration.py`. The record contains no floats: single-precision RP2040
MicroPython cannot reproduce CPython float text, so a float field cannot be sealed
and fails validation. Integer canonical text and the integer battery-mV formula are
identical on CPython and the Pico. Records sealed with the old float fields must be
regenerated. CRC is corruption detection, not authentication.

NTC conversion interpolates logarithmic resistance between selected points in
the actual Semiware MF52A103F3950 RevA2.0 R/T table. It never substitutes a generic
beta curve or extrapolates outside -20..120 C. Rail counts and implausible values
become None, inhibit ARM and trip an active system. Mounted-sensor lag/offset
must still pass25/60/68 C acceptance.

Initial divider/reference tolerance can contribute about +/-0.28 V near13.05 V.
**Two coefficients alone do not prove the cutoff gate.** Independently verify
the physical13.05 V cutoff to +/-0.1 V at12.95/13.05/13.15 V, including5 s dwell,
load and temperature, so it stays above the 12.8+/-0.1 V hardware UV trip.
Cross-check INA228 against the meter. Record results, not a nominal checkbox.
E1's AON UV protection is independent backup.

After all host acceptance gates pass, provision the separately sealed local
`commissioning.json` with fields `v`, `revision`, `serial`,
`calibration_crc32`, `hardware_commissioned=true`, `qualification_record` and
`crc32`. Use `seal(record, commissioning=True)` from this module. The serial,
revision and calibration CRC must match. `qualification_record` is the SHA256
(exactly 64 lowercase hex) of the validated acceptance file bytes, as
`srrx.provision prepare` writes it; any other value leaves the Pico
uncommissioned. HELLO reports it, and labd compares it with the SHA256 of the
bytes it validated from `--acceptance` at start
(`commissioning.load_acceptance_bound`). A mismatch, a missing field (older
firmware) or `hardware_commissioned=false` refuses ARM with
`pico_qualification_record_mismatch`. The Pico therefore pins exactly one
acceptance file: a re-saved or different `/etc/srrx/acceptance.json` blocks ARM
until the Pico is provisioned again. Like the UART CRC this detects a wrong
pairing, not a forged Pico. Implemented and host-tested in software; the check
on a flashed Pico over the real UART7 stays OPEN under the E3 gates. Do not
provision this record from a model run or CLI simulation. Copy records only
through the trusted service path; no UART message can create or override
them. Replacing a calibrated
Pico, reference, divider, or sensor requires recalibration and acceptance again.

## IMU forwarding

The separate pack supplies Rotation Vector0x05 at5 Hz. UART1 uses a separate
bounded frame decoder and pack session/sequence tracking. New session, replay,
sequence gap, malformed data or a pack health error requires a fresh pack HELLO
before valid reports resume. Each new report carries its original source
`age_ms`, plus a100 ms Pico RX scheduling allowance and actual forward waiting
time; at500 ms it becomes `fresh=false`, `quaternion=null`. No valid orientation
is retransmitted from cache. The receiver is drained while Q6A is off. A loop
scheduling gap over100 ms discards buffered pack bytes and requires HELLO again.
Host UART short writes are retried within100 ms; exhaustion fails safe.

Forwarded EVENT `p.imu` includes `pack_session` and `pack_q`. BNO status1/2/3 is
sensor calibration accuracy, not project PASS; status0 or missing reports are
invalid. Quaternion data establishes neither true-north heading nor a GNSS fix.
Host consumers must age the forwarded event further and reject stale data.

## Protection boundary and validation

R395 makes powered Pico reset/high impedance assert the common MCP reset. Three
10k MCP reset pullups are only on Q6A3V3; the insulated Q306 gate bridges no DC
rail. Internal MCP outputs become high impedance, so application pulldowns make
EN off, HMC00 and relays off. GPIO reset also loses MCP fault history. The Pico
cannot command CHG_INHIBIT high while those expanders are in reset: charger
behavior then follows its autonomous controller, NTC and hardware KSD protection.

**Complete loss of Pico supply with Q6A alive is not independently covered by
Q306/R394/R395.** R394 turns Q306 off and the MCP reset pullups release it. The
firmware does not claim to solve that hardware boundary or simultaneous power
loss and Linux hang. WDT/boot reset coverage must be scoped separately from a
complete supply loss. Verify Q6A-off/Pico-on UART and SAFE_BOOT high impedance,
absence of backfeed,3.3 mA GP17 sink, reset low/high thresholds, EN/HMC/relay states,
20 cold/20 warm boots, sensor faults, UART removal, Linux kill, WDT reset,
brownout and calibrated cutoff before commissioning.

Run host tests from the repository root:

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_supervisor.py -v
```

The tests exercise ARM gates, exact deadline edges, replay/session rejection,
sensor/clock faults, shutdown/UV behavior, ADC record corruption, NTC reference
points, GPIO polarity/order, short UART writes, ticks wrap, IMU stale recovery and
the PWR_ON_KEY timing, retry bound and release conditions (`PowerKeyTests`).
`test_pico_main.py` drives the real `main.run()` loop with injected `machine`/`time`
(TRIP diagnostics sent as EVENT, GP8 high-Z, GP16 level checked against the model
state at each write; every sleep counts, so an early exception fails instead of
hanging), the GP12 pulse sequence with Q6A 3V3 absent at boot, and checks that HMI
key-bus errors and lux failures stay separate.
Actual GPIO, ADC accuracy, interrupt latency, UART timing and watchdog reset
behavior require device tests and remain unqualified.

## Primary references checked

- [MicroPython v1.26.0 RP2 quick reference](https://docs.micropython.org/en/v1.26.0/rp2/quickref.html): GPIO, UART mappings,125 MHz and ADC APIs.
- [MicroPython Pin API](https://docs.micropython.org/en/latest/library/machine.Pin.html): initial output values, input mode and edge IRQ.
- [MicroPython UART API](https://docs.micropython.org/en/latest/library/machine.UART.html): buffers, timeouts, read/write and deinit.
- [MicroPython time API](https://docs.micropython.org/en/latest/library/time.html): ticks_diff half-period and wrap semantics.
- [MicroPython v1.26.0 WDT](https://docs.micropython.org/en/v1.26.0/library/machine.WDT.html): non-stoppable watchdog; RP2040 maximum8388 ms.
- [Semiware MF52A103F3950 RevA2.0](https://semiware.com/uploads/datasheet/MF52A103F3950.pdf): selected R/T table and operating range.
- Project `STACK.md`5.1/5.2/5.6 and `design/E3.json` provide system thresholds and physical wiring; GP17 watchdog assignment supersedes the older brightness row. The DISP12 policy, the 13.05 V cutoff with its per-unit ordering against the hardware UV trip (E3-07/E1-04) and the integer fixed-point calibration record above are recorded in the STACK v2.1 notice block; the D1 and #15 rows that still say 12.9 V carry a v2.1 remark.
