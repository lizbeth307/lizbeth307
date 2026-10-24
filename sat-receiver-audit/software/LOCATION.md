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
resume the receiver's UTC looks like a time jump and an old fix looks fresh.
`srrx.hmi` passes one `CLOCK_BOOTTIME` millisecond clock (monotonic only where
it is absent) to both the tracker and its `GpsdClient`. Calls may share the
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
| `reason`, `last_error` | `reason` is None for a live fix. For a fallback it is a still-unrecovered fault: first that of the fallback record's own source, else that of another GNSS source; otherwise `MANUAL_FALLBACK`, `STALE` or `NO_LOCATION`. Faults are kept per source, and only an accepted fix from the same source clears one: an NMEA fix does not hide an unrecovered gpsd handshake timeout. `last_error` keeps the latest diagnostic code even after recovery |
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
A single jump never passes and never moves the time reference. Rejected jump
epochs form a candidate chain per source: each new distinct epoch must progress,
relative to the previous candidate, consistently with monotonic receipt (to the
same two seconds), or the chain restarts at one. The third consistent candidate,
e.g. after a host suspend under `CLOCK_MONOTONIC`, a receiver UTC correction, or
an undated GGA outage longer than 12 h, is still rejected, but the source then
drops its old reference and NMEA date anchor. The next record, including a
same-epoch repeat of that third epoch, is a first fix again: it is still checked
against the last good position, and `utc_verified` restarts from zero. Only an
accepted fix clears the chain; other rejections of the same source in between
and the time between candidates do not reset it, but every candidate must still
agree with receipt time. Unstable or alternating timelines never reacquire.

A ZDA is compared with the date anchor only within the same 120 s window in
which that anchor may date GGA/RMC. A disagreeing ZDA is rejected
(`NMEA_DATE_JUMP`) and never moves the anchor alone. Three distinct ZDAs that
agree with each other on one new timeline retire the anchor: the third becomes
the new anchor and the next NMEA position is a first fix on that date. A
GGA+ZDA stream (no RMC) thus follows a receiver date correction, which accepted
GGAs, dated from the old anchor, would otherwise hide indefinitely. A ZDA that
agrees with the anchor restarts the ZDA chain.

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

In the deployed time/location chain from STACK (STACK.md:124, :879), gpsd
(`-n -b -s 115200`) reads `/dev/lab/gnss` and chrony disciplines the clock from
gpsd's SHM NMEA and from PPS on `/dev/pps-gnss`; this client is how a consumer
(`srrx-locationd`, below, and the touch console) reads that gpsd. The raw `srrx.gnss_uart` reader ([GNSS-UART.md](GNSS-UART.md))
is only the alternative when gpsd is not used; the two never read the UART at
the same time.

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

## Location service (srrx-locationd)

`srrx.locationd` runs as `srrx-locationd.service` (user `srrx-loc`) and is the
one GNSS position reader of the deployed system: one `LocationTracker` fed either
by a loopback `GpsdClient` (`--gnss gpsd`) or by the read-only
`srrx.gnss_uart.NmeaUartReader` (`--gnss raw`, refused while gpsd lists or runs
the UART). Consumers ask for a snapshot on `/run/srrx-loc/location.sock`, one
JSON line each way:

```python
from srrx.gnss_orchestrator import UnixLineRequest   # nonblocking; or any AF_UNIX client
job = UnixLineRequest("/run/srrx-loc/location.sock", b'{"op":"snapshot"}\n', now_ms, 2000, "LOCATIOND")
reply = job.poll(now_ms)   # None until the reply line arrives
```

The snapshot's `location` is exactly `tracker.status()` above. It adds
`qualified_fix` (live fresh fix, `mode == 3`, a known satellite count of at least
six and no jamming flag; build/07:503), the LC76G jamming flag from
`$PAIRSPF`/`$PQTMJAMMINGSTATUS` (status 2 or more, or a malformed status, held
60 s), the reader state and the `GNSS_RESET` count. In gpsd mode the client asks
gpsd for `"raw":1` so that those proprietary sentences arrive next to the JSON;
JSON lines go unchanged to `GpsdJSONDecoder`, `$` lines only to the jamming
monitor. `{"op":"invalidate","reason":"GNSS_RESET"}` invalidates both sources;
the last good position then stays available only as a stale `last_good` with
reason `GNSS_RESET`. Authorization is the kernel peer credential: labd's UID may
invalidate, labd and members of its group (the console operators) may read
snapshots, anyone else is closed before a byte is read. Positions never reach a
log, a file or the network.

labd itself never opens the UART or gpsd: its time orchestration around
`gnss_reset` (`srrx.gnss_orchestrator`) reads these snapshots, and PPS is selected
in chrony only through `srrx-timegate` after a matching LC76G read-back
(`srrx-gnss-config`) and a qualified fix held for 10 s, each sample with a fresh
"good" jamming report (`jamming.status == 1`, at most 5 s old). After a jamming
flag only a `gnss_reset` with a proven release re-opens that gate, also across
labd restarts; raw mode never selects PPS, because without gpsd chrony's NMEA SHM
refclock gets no samples. Details, units and the
deployment steps are in [GNSS-UART.md](GNSS-UART.md). The touch console still
reads gpsd directly through `GpsdClient` (gpsd mode only); moving it to these
snapshots is not done. None of this has run against a live gpsd, chrony or
LC76G.

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
manual/last-good selection and per-source fallback reasons, time jumps and
three-epoch timeline reacquisition, GGA+ZDA date correction, single or unstable
ZDA date jumps, empty optional GST/ZDA fields, explicit 2D altitude,
bounded JSON and mocked gpsd handshake including late polls, short writes and
disconnect. Device qualification still requires real UART
recordings and live gpsd tests; no satellite lock or accuracy result is claimed.

## Pointing from the receiver's own fix

`srrx.geo_look` (stdlib) turns a tracker status into QO-100 / Es'hail-2 look
angles for the nominal slot 25.9E (STACK.md:24, :185). There is still no city
table: the observer is this tracker's status, and tests use unnamed lat/lon
points only.

```python
from srrx.geo_look import FirstFixGate, geo_look_angles, pointing_from_status

look = geo_look_angles(lat, lon, alt_m=0.0, sat_lon_deg=25.9, model="wgs84")  # or model="sphere"
gate = FirstFixGate(); gate.feed(tracker.status(now_ms), now_ms)              # same monotonic clock
view = pointing_from_status(tracker.status(now_ms), first_fix_stable=gate.stable, qo100_omm=None)
```

- `sphere` is the STACK model (Re/r = 0.15127, GEO radius 42164 km); `wgs84`
  (default) places a geodetic observer in ECEF and the satellite at
  (r cos lon_s, r sin lon_s, 0). Azimuth is from true north, not magnetic.
  Over 34-70N, 25W-45E both agree within 0.04 deg in elevation and azimuth.
- Skew: STACK gives only `tan psi = sin dlon / tan lat`. The sign convention is
  derived by vector projection (the satellite's V polarisation is parallel to
  Earth's spin axis, compared with the local vertical plane): **+ means the LNB is
  turned counter-clockwise as seen from behind it, looking toward the satellite**,
  on the +/-45 deg neck scale. A northern observer west of 25.9E gets a positive
  value; the southern hemisphere flips the sign. Within 1 deg of the equator skew
  is undefined (`SKEW_UNDEFINED_NEAR_EQUATOR`); below the horizon it is not
  given. The tan formula (sphere) and the projection (WGS84) agree in sign and
  within 0.31 deg over the same area. The bench peak search on the beacon C/N0 in 5 deg steps (P-09) is the
  final authority; the hint is a starting point.
- Qualified fix (build/07:503): fresh live `gpsd`/`nmea`, `mode == 3`,
  `satellites >= 6`, and the first-run window (3D, >= 8 satellites, within
  50 m for 5 min, `FirstFixGate`). The tracker itself accepts as few as three
  satellites, so the gate is not optional. Conservative choices: an unknown
  satellite count never qualifies (a gpsd TPV carries no count: it comes from the
  same epoch's SKY, so a gpsd fix without one stays unqualified); the first-run window is per
  process, never persisted, and restarts after any failed sample or a gap of more
  than 5 s between samples; a backwards clock latches the gate closed.
- Manual and last-good positions still give angles, labelled "not a GNSS fix".
  No position or a monotonic clock fault (`MONOTONIC_TIME_REVERSED`) gives no
  angles. The pointing result carries no observer coordinates.
- "Visible from here" needs a stationary allowlisted QO100 OMM record
  (`|n - 1.00274| < 0.0005` rev/day, both edges exclusive) and elevation
  >= 5 deg. Without one the geometry is shown as "nominal slot 25.9E; TLE not
  verified" and `visible_from_here` stays false. Old elements or an unverified
  clock clear `auto_pointing_allowed`; display and reception are unaffected.
- `v_dipole_hint(max_el)`: >= 35 deg bisector N-S, <= 30 deg tips N-S; 30-35 deg
  is not specified by STACK, so the unattended default (bisector N-S) is used.

## Orbit elements and pass prediction

`srrx.orbits` (stdlib) reads a local CelesTrak OMM file copied in over home Wi-Fi
or USB/microSD; it has no network code. It accepts a JSON array or a CSV whose
header names the 17 OMM fields, at most 4 MiB, rejects duplicate keys,
NaN/Infinity, missing or extra fields, out-of-range values, non-SGP4
`EPHEMERIS_TYPE`, classified sets and NORAD ids outside 1..999999. Only NORAD ids
from the allowlist file survive:

```json
{"schema_version": 1, "kind": "srrx_orbit_allowlist",
 "targets": [{"norad_id": 12345, "name": "ALIAS", "role": "LRPT"}]}
```

Roles: `QO100` (at most one), `ISS` (3-day age warning), `LRPT` (V-dipole hint),
`GEO`, `OTHER` (7-day warning). No real ids are shipped or hard-coded. One record
per NORAD id survives (newest epoch; identical duplicates dropped; the same epoch
with different elements rejects the file). Age is a warning, never a refusal.
`export_satdump_csv(records, path)` atomically replaces the SatDump OMM CSV
(header plus 17 columns in CelesTrak order). That column order has not yet been
checked against SatDump 1aedd60's reader (POL-10, BUILDER).

`srrx.passes` is the reference predictor for the lab venv only: Skyfield 1.55
and sgp4 2.27 (`EarthSatellite.from_omm`, `find_events`), imported lazily;
without them `PassDependencyError` is raised and labd stays stdlib-only. The
timescale is Skyfield's built-in table (no download) and no ephemeris file is
used. The observer is rounded to 0.1 deg before prediction, so a saved plan holds
only the rounded position. Every pass carries AOS/TCA/LOS UTC, azimuths, maximum
elevation, OMM epoch/age/warning, `time_verified` (false unless the caller's UTC
is verified), observer source/age and, for LRPT, the V-dipole hint. Only complete
passes are listed; passes cut by the window edge are counted. sgp4 2.27 accepts
NORAD ids up to 339999 (Alpha-5); larger ids are listed in `skipped`. CLI for a
bounded lab-venv subprocess (refuses an existing output):

```sh
python3 -m srrx.passes --omm gp.json --allowlist orbit-allowlist.json --location where.json \
  --start-utc 2026-10-24T00:00:00Z --hours 24 --output new-plan.json
```

Agreement with Gpredict within 1 s is POL-11 (BUILDER) and is not claimed.
The guest lock pins `skyfield==1.55`, `sgp4==2.27`, `jplephem==2.24` and
`certifi==2026.10.19` with hashes (`deployment/linux_lab/wheelhouse-requirements.txt`).

```sh
for name in geo_look orbits passes; do
  PYTHONPATH=software python -m unittest discover -s software/tests -p "test_$name.py" -v
done
```

## Primary sources checked20 October2026

- [Quectel LC26G/LC26G-T/LC76G/LC86G GNSS Protocol Specification v1.5](https://www.quectel.com/content/uploads/2024/04/Quectel_LC26GLC26G-TLC76GLC86G_Series_GNSS_Protocol_Specification_V1.5.pdf), sections2.1/2.2: checksum and supported standard message fields.
- [gpsd JSON protocol](https://gpsd.io/gpsd_json.html), TPV/GST/VERSION/WATCH: optional fields, dimensions, epoch updates and unknown error-estimate confidence.
- [gpsd Client HOWTO](https://gpsd.io/client-howto.html): asynchronous fixes, WATCH negotiation and client-library guidance.
