# Receiver location

`srrx.location` implements receive parsing and a location state model using only
the Python standard library. It locates the receiver from its configured GNSS
input or explicit manual coordinates. It contains no city table, emitter lookup,
network geolocation request or automatic serial-device guess.

The module and tests are implemented. They have not been run against the
assembled LC76G, Q6A UART6 or a live gpsd installation. The tests use synthetic
records, Quectel's published LC76G examples, and mocked nonblocking sockets.

## Public API

```python
from srrx.location import LocationTracker, GpsdClient

tracker = LocationTracker(
    fresh_ms=3000,
    max_speed_mps=100.0,
    jump_slack_m=100.0,
    utc_tolerance_s=2.0,
    device=None,
    utc_reference=None,
)

new_fix = tracker.ingest_gpsd(decoded_object, now_ms)
new_fix_count = tracker.ingest_nmea(received_bytes, now_ms)
current = tracker.manual(latitude_degrees, longitude_degrees, now_ms)
current = tracker.status(now_ms)
```

`now_ms` is a nonnegative integer from a monotonic clock. On Linux prefer the
suspend-aware `CLOCK_BOOTTIME`: `CLOCK_MONOTONIC` stops during suspend, so after
resume the receiver's UTC looks like a time jump. Calls may share the
same timestamp but must never go backwards. A backwards timestamp latches a
clock fault: GNSS becomes unavailable as a live source and fallback ages become
unknown. Construct a new tracker after repairing the caller's clock domain;
do not relabel an old monotonic value as a new boot's age.

`ingest_gpsd` returns True only for a newly accepted position epoch. Partial
reports and same-epoch metadata enrichment return False. `ingest_nmea` returns
the number of newly accepted positions in the chunk. Bytes are a fragmented
stream and need a newline to finish a sentence. A string is treated as complete
text records and gets a final newline if absent. Neither method opens a device.

`manual` validates finite decimal degrees and returns the selected status. It
does not override a fresh GNSS fix or claim satellite lock. Once GNSS is stale
or invalid, the newest manual entry or last good GNSS position wins; a manual
entry wins a timestamp tie. Manual input is a position entered at that moment,
not a permanent fixed-station override. No valid location exists at startup
until one is supplied. Last-good and manual entries live only in this tracker
instance; monotonic ages are not silently persisted across process/boot resets.

## Status contract

| Field | Meaning |
|---|---|
| `available` | Coordinates exist, including a clearly labelled fallback |
| `source` | `gpsd`, `nmea`, `last_good`, `manual`, or `none` |
| `origin` | Original source; e.g. a stale gpsd position retains `origin=gpsd` |
| `fresh`, `live_fix` | True only for a currently healthy, recently received GNSS position |
| `lat`, `lon` | Decimal degrees, or None; zero is a valid coordinate |
| `age_ms` | Time since position acceptance/manual entry; None if clock invalid |
| `utc` | Receiver-reported/dated UTC, or None when a GGA date is unavailable |
| `utc_verified` | Requires an explicit trusted UTC reference and three distinct consistent 3D fixes; otherwise False |
| `mode` | gpsd dimension or recent matching NMEA GSA dimension; NMEA defaults to the lower bound of 2D |
| `uncertainty_m` | Current reported horizontal estimate; None when unknown or using fallback |
| `fix_uncertainty_m` | Estimate associated with the original fix, retained when stale |
| `uncertainty_basis` | Report source, absence of an estimate, manual input, or unbounded stale movement |
| `uncertainty_confidence` | `unknown`; no invented 95% confidence or HDOP-to-metre conversion |
| `alt_msl_m`, `alt_hae_m` | Distinct altitude references, never the deprecated ambiguous gpsd `alt` |
| `speed_mps`, `track_deg` | Reported ground motion for live fixes; None for fallback |
| `hdop`, `satellites` | Reported GGA geometry/count; optional, not an accuracy guarantee |
| `device` | Actual/explicit gpsd device identity, not a guessed path |
| `reason`, `last_error` | `reason` is None for a live fix; for a fallback it is the still-unrecovered fault, otherwise `MANUAL_FALLBACK`, `STALE` or `NO_LOCATION`. `last_error` keeps the latest diagnostic code even after recovery |
| `rejected_count`, `ignored_count` | Rejected input and irrelevant/partial/duplicate records |

An available fallback is **not** a current GNSS fix. Stale position uncertainty
is unbounded because subsequent receiver movement is unknown. Its old error
estimate is preserved separately rather than reused as a current radius.
Manual input has unspecified uncertainty. Consumers must make their own policy
decision about fallback age and accuracy; a map marker must display its source.

## Plausibility and time handling

Coordinates must be finite and within latitude +/-90 and longitude +/-180.
The default portable-receiver movement policy allows a 100 m position slack
plus 100 m/s times elapsed receipt time. It checks transitions across GNSS
sources as well as reported speed. These are configurable application filters,
not LC76G specifications or proof against GNSS spoofing. Dateline crossing uses
great-circle distance; poles and latitude/longitude zero are accepted.

Receiver epoch progression must agree with monotonic receipt progression to
within two seconds by default. Backwards epochs and larger time jumps are
rejected. Repeated epochs can enrich uncertainty/altitude metadata but never
refresh position age. Contradictory same-epoch positions are rejected. A bad
fix does not destroy the last good coordinates or turn them into a fresh fix.
A single jump never passes and never moves the time reference. A source
reacquires only after three consecutive distinct epochs that progress
consistently with monotonic receipt on the new timeline, e.g. after a host
suspend under `CLOCK_MONOTONIC`, a receiver UTC correction, or an undated GGA
outage longer than 12 h. That source then drops its old reference and NMEA date
anchor, and the next epoch is a first fix again: it is still checked against the
last good position, and `utc_verified` restarts from zero. Unstable or
alternating timelines never reacquire. A ZDA is compared with the date anchor
only within the same 120 s window in which that anchor may date GGA/RMC.

There is no assumed trustworthy system wall clock. The first coherent received
position may be accepted while `utc_verified` remains False. If an independent
trusted clock is available, provide `utc_reference` as a callable returning
current Unix seconds. Matching that reference and three distinct 3D epochs are
required before UTC is marked verified. This is not a PPS timing qualification
and does not authenticate satellite signals or set the system clock.

RMC's two-digit date uses an explicit 1980..2079 convention without a recent
full-year anchor. ZDA supplies an unambiguous full year; a recent anchor resolves
the matching RMC century. GGA can work without a date using time-of-day
progression, but then `utc=None`. A recent date anchor permits midnight rollover.
A leap-second label is handled explicitly and never certified as verified UTC.

## LC76G NMEA receive subset

The parser validates ASCII framing and XOR checksum, latitude/longitude minute
fields, hemisphere, numbers and dates. It implements:

- RMC: position, valid/warning status, date, speed and ground course. Autonomous
  and differential modes are accepted; estimated/no-fix modes are rejected.
- GGA: quality, position, satellite count, HDOP, MSL altitude and geoid separation.
  Quality 1/2 is accepted; quality0/6 is not a fresh GNSS fix. At least three
  satellites are required, or four with matching 3D GSA. HDOP99.99 is invalid;
  the application filter rejects HDOP above20 rather than assigning accuracy.
- GSA: matching talker fix dimension and explicit loss of fix.
- GST: same-epoch axis-error estimates enrich the position without refreshing age.
  Empty time or axis-error fields mean "estimate unavailable" and are ignored;
  malformed non-empty values still invalidate the source. A gpsd GST without
  `time`, `lat` or `lon` is ignored in the same way.
- ZDA: full date/time anchor; it never creates a position alone. A ZDA with empty
  time/date fields (receiver without time yet) is ignored.

LC76G's RMC trailing NavStatus `V` is documented as unsupported and is not confused
with the separate RMC validity Status. Unknown talkers/proprietary commands and
unimplemented sentences are ignored; the code sends no LC76G configuration or
reset command. GGA altitude is a reported MSL value; without a matching 3D GSA,
the parser does not infer a 3D fix solely from its presence. When a fresh
matching GSA explicitly reports 2D, GGA altitude is held or assumed, so
`alt_msl_m` and `alt_hae_m` are None, as for a gpsd 2D TPV.

## Optional live gpsd transport

```python
client = GpsdClient(tracker, host=config["gpsd_host"], port=config["gpsd_port"])
client.start(monotonic_ms())

# Called regularly by the application's existing loop, e.g. every100 ms:
client.poll(monotonic_ms())
location = tracker.status(monotonic_ms())

# Deliberate disconnect, no automatic reconnection:
client.close()
```

Both endpoint fields are required. Only explicit numeric loopback addresses or
`localhost` are accepted; `localhost` maps directly to127.0.0.1 without DNS.
There is no default `/dev` path or automatic port probing. To filter multiple
gpsd sensors, supply `LocationTracker(device=the_exact_configured_identity)`.
Otherwise the tracker binds the first accepted reported device identity and
ignores other devices. The caller remains responsible for configuring gpsd to
read the actual LC76G UART/udev identity.

The client uses nonblocking connect/read/write, checks protocol major3, sends
JSON WATCH, and waits for its acknowledgement before ingesting TPV/GST. The
connection and VERSION must arrive within 3 seconds of `start`, and the WATCH
acknowledgement within 3 seconds of VERSION. Each poll drains already-received
bytes before checking the deadline, so a late first poll does not discard a
waiting handshake. Short WATCH writes are retained for the next poll.
Each poll reads at most four4096-byte chunks. Disconnect, malformed JSON or an
explicit server error invalidates live gpsd data immediately; the tracker can
still select another healthy GNSS source or a labelled fallback. Reconnection
requires an explicit `start` or a newly constructed client.

This is a deliberately small protocol3 client required for a stdlib-only
integration. It does not claim full libgps compatibility. The official gpsd
documentation recommends its client libraries for broad protocol support; test
this subset against the actual installed gpsd release before deployment.

`GpsdJSONDecoder.feed(bytes)` is also available to callers with an existing
transport. It rejects invalid UTF-8, duplicate keys, nonfinite values, excessive
nesting and overlong lines. Its returned objects still need `ingest_gpsd`.
No AIS, ATT, IMU, receiver-emitter association or other non-position gpsd report
creates receiver coordinates.

## Bounds and validation

NMEA lines are limited to256 bytes, with at most128 records processed per call.
gpsd JSON lines are limited to10240 bytes including line termination, and at
most64 objects are decoded per feed. Input chunks are capped at65536 bytes;
JSON trees have depth/node bounds. Overlong streams are discarded until a
delimiter and the next valid record can recover. There are no blocking sleeps,
serial reads, filesystem writes or external network calls in the tracker.

Run:

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_location.py -v
```

Tests cover official NMEA examples, every fragmentation boundary, malformed and
nonfinite data, checksum failure, missing fields, duplicate/stale epochs,
impossible coordinates/movement, dateline crossing, midnight and leap labels,
manual/last-good selection and fallback reasons, time jumps and three-epoch
timeline reacquisition, empty optional GST/ZDA fields, explicit 2D altitude,
bounded JSON and mocked gpsd handshake including late polls, short writes and
disconnect. Device qualification still requires real UART
recordings and live gpsd tests; no satellite lock or accuracy result is claimed.

## Primary sources checked20 October2026

- [Quectel LC26G/LC26G-T/LC76G/LC86G GNSS Protocol Specification v1.5](https://www.quectel.com/content/uploads/2024/04/Quectel_LC26GLC26G-TLC76GLC86G_Series_GNSS_Protocol_Specification_V1.5.pdf), sections2.1/2.2: checksum and supported standard message fields.
- [gpsd JSON protocol](https://gpsd.io/gpsd_json.html), TPV/GST/VERSION/WATCH: optional fields, dimensions, epoch updates and unknown error-estimate confidence.
- [gpsd Client HOWTO](https://gpsd.io/client-howto.html): asynchronous fixes, WATCH negotiation and client-library guidance.
