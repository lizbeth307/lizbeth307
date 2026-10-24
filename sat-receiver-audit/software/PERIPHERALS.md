# Pico HMI peripherals

Implemented source code covers the actual E3 key expander, two incremental
encoders and ambient-light sensor. It has portable register/IRQ tests, but has
**not been loaded onto or qualified on the assembled hardware**.
`physical_qualified` remains false. Physical inputs only navigate the HMI; they
never authorize ARM, renew an operator lease, or operate power outputs.

## Ownership and actual wiring

`design/E3.json` is the wiring authority. The CPython wrapper
`software/srrx/peripherals.py` derives its mapping from that graph and refuses a
different controller, physical expander pin mapping, supply domain, address
strap, or GPIO connection before doing I/O. The portable deployed core is
`firmware/pico/hmi.py`. Its mapping is compared with the derived graph in tests.

| Function | E3 part/net | Pico connection |
| --- | --- | --- |
| Keys | U306 PI4IOE5V9555LEX, address 0x20, A0/A1/A2 grounded | SDA GP4, SCL GP5; separate Pico I2C0 bus |
| Key interrupt | U306 INT_N, physical pin 1 | GP10, active low |
| Keys 0 through 7 | IO0_0 through IO0_7, physical pins 4 through 11 | HOME, BACK, REC, MARK, FN, LOCK, ENC1_PRESS, ENC2_PRESS |
| Unused key bank | U306 IO1_0 through IO1_7, NC in graph | Configured outputs with zero latches |
| Encoder 1 | ENC301 A/B through the drawn 10k/10n RC paths | GP2/GP3 |
| Encoder 2 | ENC302 A/B through the drawn 10k/10n RC paths | GP6/GP7 |
| Ambient light | U308 Adafruit 4162 VEML7700, fixed address 0x10 | GP4/GP5 through the drawn 100-ohm series resistors |

Both modules use `E3_PICO3V3`. This bus is not exposed through Q6A's Linux I2C
controller. The number 0x20 also belongs to an unrelated MCP on Q6A's bus; a
Linux `/dev/i2c-*` must never be substituted for the Pico transport. No device
node is guessed. A transport must explicitly declare
`domain = "pico_hmi_i2c0"`; a second poller sharing that transport is refused.
The deployed `PicoHMITransport` is the sole owner. Do not simultaneously enable
another firmware or kernel key driver on these wires.

## Public interfaces

The host/bench wrapper provides:

```python
derive_wiring(project) -> dict
PeripheralPoller(transport, project)
poller.poll(now_ms) -> dict
poller.snapshot(now_ms) -> dict
```

`project` is the repository path containing `design/E3.json` and
`firmware/pico/hmi.py`. Time is a nonnegative unwrapped monotonic integer in
milliseconds. `poll` uses the same `read(address, register, count)` and
`write(address, register, bytes)` methods as the public `I2CTransport` protocol.
The Pico transport additionally provides `recover()`,
`sample_encoders() -> ((delta, error), (delta, error))`, and
`interrupt_pending() -> bool`. A bench transport must implement those methods
and the explicit bus domain; the host wrapper does not own physical encoders.

On MicroPython, `PeripheralPoller(PicoHMITransport())` directly uses the portable
core. `adapter.TickClock` unwraps `ticks_ms()` with `ticks_diff()` before passing
time to it. Reversed time latches invalid input; a poll gap above 100 ms starts a
new input generation and rebaselines held keys.

## Register and input behavior

PI4IOE5V9555 has four register pairs, not a key-event FIFO. Its address pointer
toggles **within the selected pair only**. Initialization therefore uses three
separate two-byte writes and readbacks:

| Starting register | Bytes | Meaning |
| --- | --- | --- |
| 0x02 | 00 00 | Both output latches low before selecting outputs |
| 0x04 | 00 00 | No input polarity inversion |
| 0x06 | FF 00 | Port 0 inputs; unconnected port 1 outputs |

Reading two bytes from 0x00 samples both input ports and clears the corresponding
interrupts. Inputs are polled at least every nominal 20 ms, with extra reads for
asserted INT_N. Each key needs 30 ms of stable state to change its debounced
state. Held keys at boot or after recovery establish a baseline and do not
invent a press. Press counters retain completed debounced presses between
telemetry snapshots. Very short pulses can still be missed: polling and debounce
do not provide a hardware FIFO or a guaranteed minimum pulse capture width.

All six configuration bytes are checked again every second. A NACK, short read,
short write, or changed configuration invalidates input, increments its
generation and schedules recovery. Recovery clocks SCL nine times, sends STOP,
and checks both released lines. Stuck lines fail immediately without an
unbounded wait. Retry delays are scheduled; there is no sleeping for sensor
integration or a retry backoff inside `poll`.

`PicoHMITransport` uses both-edge **hard GPIO interrupts** for encoder A/B and a
bounded integer quadrature accumulator. A full cycle has four legal transitions.
Reversals and contact bounce cancel partial movement; diagonal transitions and
pending-counter overflow invalidate the interval. The main loop drains both
encoders atomically with interrupts disabled, allocating result containers only
after restoring interrupts. Totals are signed 32-bit modular counters. The
truncated PEC11R-4220F graph description does not establish the purchased
variant's detents per revolution or installed direction; both require a bench
check before assigning a UI scale.

The bus adapter uses `machine.SoftI2C(freq=100000, timeout=200)` with 8-bit
register addresses. The 200-microsecond timeout applies to each clock-stretch
wait. Individual fixed-size I2C operations are synchronous; the driver does not
claim an asynchronous controller or measured worst-case execution time. Its
initialization and poll transactions are finite and contain no integration waits.
Measure the complete poll time and scheduler gaps on the selected MicroPython
build with normal operation and disconnected/stuck modules.

## VEML7700 acquisition

Words are transferred least-significant byte first. The driver disables power
saving via register 0x03 and verifies configuration register 0x00. It starts with
gain 1/8, integration 25 ms (`0x1300`, 2.1504 lux/count). Below 40 uncorrected lux
it changes to gain 2, integration 800 ms (`0x08C0`, 0.0042 lux/count); above 90 lux
or saturation it returns to low gain. This hysteresis avoids repeated gain
changes around one threshold. A changed profile clears cached lux until a new
integration completes.

The first-sample wait includes the datasheet's +30% integration tolerance and a
50 ms margin: **83 ms** for the 25 ms profile and **1090 ms** for the 800 ms
profile. Acquisition age conservatively includes 33 or 1040 ms respectively,
plus actual time since reading. The low-gain response above 1000 lux uses the
polynomial from Vishay application note 84323. Saturation, out-of-range values,
configuration changes, and I/O failures produce `lux=null, lux_valid=false`.
Failures clear cached lux; retries do not renew an old sample's timestamp.

Local lux is invalid at 2000 ms. Transport and GUI aging may invalidate a long
integration sample earlier than the next reading; a brief unknown interval is
intentional. This is sensor lux, not an installed-cover calibration certificate.
Optical-window transmission, temperature response and comparison with a reference
light meter remain physical acceptance work. No unverified display brightness
command is issued. LCD controller/firmware and its DDC/CI behavior must first be
identified and tested through an explicitly selected adapter/path. **GP17 remains
the MCP watchdog reset actuator.**

## UART snapshots and freshness

The Pico emits one `EVENT` payload containing `hmi` at up to 5 Hz:

```json
{"hmi":{"ok":true,"fresh":true,"age_ms":100,"keys":0,
"presses":[0,0,0,0,0,0,0,0],"encoders":[0,0],"lux":215.04,
"lux_valid":true,"lux_age_ms":133,"sequence":10,"generation":0,"error":null}}
```

| Field | Contract |
| --- | --- |
| `keys` | Unsigned 8-bit pressed mask; bit order is the table above |
| `presses` | Eight cumulative unsigned 16-bit press counters; deltas modulo 65536 |
| `encoders` | Two cumulative signed 32-bit full-cycle counters; modular deltas |
| `sequence` | Unsigned 32-bit poll sequence, distinct from the UART envelope sequence; refuses wrap |
| `generation` | Unsigned 16-bit discontinuity counter for rebaselining after recovery, poll gaps or invalid encoder intervals |
| `age_ms` | Age of the key sample plus 100 ms source TX budget |
| `lux_age_ms` | Integration budget plus actual sample age plus 100 ms source TX budget, or null |
| `ok`, `fresh` | Current key/encoder validity; lux has its own validity flag |
| `error` | Bounded diagnostic string or null; lux integration may be unknown while keys remain valid |

The host adds its own 100 ms receive allowance and actual elapsed time. The HMI
must clear its input baseline on Pico session changes, generation changes,
invalid data or expiry; it must not replay accumulated presses across those
boundaries. Keys expire at an effective age of 500 ms, lux at 2000 ms. Existing
host/GUI integration enforces those budgets and rejects implausible counter
deltas. Merely receiving a snapshot does not establish operator intent to ARM.

`main.TelemetrySchedule` sends **one total outbound frame per loop**. HELLO and
state-change/200 ms STATUS take priority; HMI and the latest IMU report alternate
when both are pending; bounded diagnostics follow. Pending IMU reports retain
their original receive time and accumulate queue age. HMI snapshots are sampled
again immediately before encoding, preserving press counters while replacing old
key/lux values. Safety inputs are resampled and physical supervisor outputs
applied before every bounded UART transmit; the WDT is fed only after that work.
There is no ordinary STATUS+IMU+HMI burst that would itself exceed the 100 ms
input scheduling-gap guard. UART backpressure or a slow peripheral can still
cause genuine invalid/stale intervals and must be tested on hardware.

Copy `hmi.py` alongside the existing Pico `main.py`, `adapter.py`, `supervisor.py`,
`calibration.py`, `imu_relay.py` and shared `wire.py` when deploying. Source
changes require the host commissioning manifest to be regenerated and accepted;
software tests do not authorize hardware operation.

## Q6A-side LC76G UART and reset (not a Pico peripheral)

The LC76G GNSS receiver (U304) is wired to Q6A UART6 and its RESET_N to MCP23017
#4 GPA1 through Q301; neither passes through the Pico. See
[GNSS-UART.md](GNSS-UART.md) for the receive-only `srrx.gnss_uart` reader
(`/dev/lab/gnss` bound by `KERNELS=="998000.serial"`, `O_RDONLY`, `TIOCEXCL`,
raw 115200 with read-back, bounded nonblocking polls, no reopen) and the
policy-checked labd `gnss_reset` pulse (integer 100..500 ms, 30 s spacing after
release, at most 3 per 15 min, 1000 ms hard deadline). Through labd/labctl the
pulse needs the caller's own lease inside an armed, configured session; a
release counts only when a read-back write proves it (otherwise the status is
`RELEASE_UNCONFIRMED`, never a software-image `IDLE`). The raw
`E3_GNSS_RESET_GATE` net stays outside the control whitelist. These are host
software and PTY/simulation tests only: UART6 pinmux, baud rate, the reset scope
trace and the Pico/Q306/R326 release path remain open hardware items.

## Verification and sources

Run from the repository:

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_peripherals.py -v
PYTHONPATH=software python -m unittest discover -s software/tests -p test_supervisor.py -v
```

The peripheral tests exercise the real paired-register address behavior, byte
order, configuration readbacks, negative bus cases, debounce, quadrature IRQs and
overflow, clock gaps, stale data, source aging, worst-case 512-byte wire envelope,
and scheduling under an auxiliary-event flood. They use fake transport/GPIOs and
provide no device or electrical qualification claim.

Primary specifications used:

- [Diodes PI4IOE5V9555, DS41303 Rev 1-2](https://www.diodes.com/datasheet/download/PI4IOE5V9555.pdf): physical pins, address straps, register pairs, configuration and interrupt clearing.
- [Vishay VEML7700 datasheet, Rev 1.8](https://www.vishay.com/docs/84286/veml7700.pdf): command/word byte order, gain and integration bits, conversion resolution and timing tolerance.
- [Vishay Designing the VEML7700, AN84323](https://www.vishay.com/docs/84323/designingveml7700.pdf): gain selection, high-lux correction and optical installation considerations.
- [Bourns PEC11R](https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf): two-bit quadrature outputs and contact filtering; exact ordered variant remains to be confirmed.
- [MicroPython v1.26 I2C](https://docs.micropython.org/en/v1.26.0/library/machine.I2C.html) and [Pin](https://docs.micropython.org/en/v1.26.0/library/machine.Pin.html): SoftI2C memory transactions, timeout semantics and GPIO IRQ API.
