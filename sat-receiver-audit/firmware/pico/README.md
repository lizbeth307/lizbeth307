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

Use a genuine Pico UF2 from the official
[RPI_PICO download](https://micropython.org/download/RPI_PICO/). The API reference
target is MicroPython **v1.26.0**; record the actual UF2 version and SHA-256 in the
unit acceptance log. Run the device tests with that exact build. Do not deploy a
Pico W/Pico 2 or overclocked build. The code explicitly sets 125 MHz and leaves
GP23 and USB clocks at their default settings pending the STACK RF A/B test.

With the main switch on or the Pico physically isolated from LAB5, copy these
files to the Pico filesystem root using your installed `mpremote`:

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
| Q6A key transistor | GP12 (16) | LOW; physical button already reaches PMIC through BAT54 |
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
   one observation. Host sends HB every 200 ms.
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
| Q6A 3V3 falls after being observed on | Reset immediately; Pololu OFF after 3 s |
| Calibrated battery <=13.05 V with no fresh HB | Pololu OFF after continuous 5 s; recovery or fresh HB resets dwell. Same 13050 mV as the host graceful cutoff, above the 12.8 V hardware UV trip |
| Battery low with live HB | Host implements the INA228/Linux graceful shutdown policy; this fallback does not replace it |
| Physical button | 30 ms debounce; short release emits POWER_BUTTON, 1.5 s hold requests graceful shutdown |
| Restart after OFF | Physical button edge and battery >=13.6 V clear software latch; remote ARM alone cannot restart |
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
points, GPIO polarity/order, short UART writes, ticks wrap and IMU stale recovery.
`test_pico_main.py` drives the real `main.run()` loop with injected `machine`/`time`
(TRIP diagnostics sent as EVENT, GP8 high-Z, GP16 level checked against the model
state at each write; every sleep counts, so an early exception fails instead of
hanging) and checks that HMI
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
