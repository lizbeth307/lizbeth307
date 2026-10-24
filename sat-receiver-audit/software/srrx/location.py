"""Receive-only, bounded GNSS location tracking; no city or transmitter lookup.

All public timestamps are caller-supplied monotonic integer milliseconds, from
one clock per tracker; on Linux a suspend-aware CLOCK_BOOTTIME (srrx.hmi uses it).
Receiver UTC is checked separately and never sets the system clock.
"""
import calendar
import datetime as dt
import errno
import ipaddress
import json
import math
import re
import select
import socket

MAX_NMEA_BYTES = 256
MAX_GPSD_BYTES = 10240
MAX_INPUT_BYTES = 65536
SKY_CARRY_MS = 1500  # one 1 Hz epoch plus slack: gpsd's SKY follows its TPV
TALKERS = {"GP", "GN", "GL", "GA", "GB", "BD", "GQ"}
_DECIMAL = re.compile(r"^\d+(?:\.\d+)?$")
_UTC = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d{1,9})?(?:Z|\+00:00)$")


def _finite(value, low, high):
    return type(value) in (int, float) and low <= value <= high and math.isfinite(value)


def _coordinate(lat, lon):
    return _finite(lat, -90, 90) and _finite(lon, -180, 180)


def _distance(lat1, lon1, lat2, lon2):
    """Spherical plausibility distance; not a surveying/geodesy result."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlon = phi2 - phi1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlon / 2) ** 2
    return 6371008.8 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def _iso(epoch):
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _dated_epoch(date, hour, minute, second):
    if not 0 <= hour < 24 or not 0 <= minute < 60 or not 0 <= second < 61:
        raise ValueError("UTC_FIELDS")
    leap = second >= 60
    if leap and not (hour == 23 and minute == 59 and date.month in (6, 12)
                     and (date + dt.timedelta(days=1)).day == 1):
        raise ValueError("UTC_LEAP_SECOND")
    epoch = calendar.timegm(date.timetuple()) + hour * 3600 + minute * 60 + second
    return epoch, leap


def _gpsd_time(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("GPSD_UTC")
    match = _UTC.fullmatch(value)
    if match is None:
        raise ValueError("GPSD_UTC")
    year, month, day, hour, minute, second = (int(part) for part in match.groups()[:6])
    fraction = float(match.group(7) or 0)
    return _dated_epoch(dt.date(year, month, day), hour, minute, second + fraction)


def _tod(value):
    if not re.fullmatch(r"\d{6}(?:\.\d{1,9})?", value):
        raise ValueError("NMEA_UTC")
    hour, minute, second = int(value[:2]), int(value[2:4]), float(value[4:])
    if (not 0 <= hour < 24 or not 0 <= minute < 60 or not 0 <= second < 61
            or second >= 60 and (hour != 23 or minute != 59)):
        raise ValueError("NMEA_UTC")
    return hour, minute, second


def _nmea_coordinate(value, hemisphere, latitude):
    digits, limit = (4, 90) if latitude else (5, 180)
    if not re.fullmatch(r"\d{%d}(?:\.\d{1,10})?" % digits, value):
        raise ValueError("NMEA_COORDINATE")
    allowed = ("N", "S") if latitude else ("E", "W")
    if hemisphere not in allowed:
        raise ValueError("NMEA_HEMISPHERE")
    degrees, minutes = int(value[:digits-2]), float(value[digits-2:])
    if degrees > limit or not 0 <= minutes < 60 or degrees == limit and minutes != 0:
        raise ValueError("NMEA_COORDINATE")
    return (degrees + minutes / 60) * (-1 if hemisphere in ("S", "W") else 1)


def _nmea_number(value, low, high, optional=True):
    if not value and optional:
        return None
    # Altitude may be negative; exponent, inf, nan and whitespace are forbidden.
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        raise ValueError("NMEA_NUMBER")
    number = float(value)
    if not _finite(number, low, high):
        raise ValueError("NMEA_RANGE")
    return number


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError("nonfinite JSON constant")


def _bounded_json(value):
    pending, nodes = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > 2048 or depth > 32:
            raise ValueError("JSON structure limit")
        if isinstance(item, dict):
            pending.extend((part, depth + 1) for part in item.values())
        elif isinstance(item, list):
            pending.extend((part, depth + 1) for part in item)
        elif type(item) is float and not math.isfinite(item):
            raise ValueError("nonfinite JSON number")


class GpsdJSONDecoder:
    """Newline-delimited JSON decoder, <=10240 bytes/line and 64 objects/feed."""
    def __init__(self):
        self.errors = 0
        self._buffer = bytearray()
        self._discard = False

    @property
    def buffered_bytes(self):
        return len(self._buffer)

    def reset(self):
        self._buffer.clear()
        self._discard = False

    def feed(self, data):
        if isinstance(data, memoryview):
            if data.nbytes > MAX_INPUT_BYTES:
                self.errors += 1
                self.reset()
                return []
            data = data.tobytes()
        if not isinstance(data, (bytes, bytearray, memoryview)) or len(data) > MAX_INPUT_BYTES:
            self.errors += 1
            self.reset()
            return []
        result = []
        for byte in data:
            if byte == 10:
                if self._buffer and not self._discard:
                    try:
                        if len(result) >= 64:
                            raise ValueError("batch object limit")
                        value = json.loads(self._buffer.decode("utf-8"),
                                           object_pairs_hook=_no_duplicates,
                                           parse_constant=_bad_constant)
                        if not isinstance(value, dict) or len(value) > 128:
                            raise ValueError("JSON object required")
                        _bounded_json(value)
                        result.append(value)
                    except (ValueError, UnicodeError, RecursionError):
                        self.errors += 1
                self.reset()
            elif not self._discard:
                if len(self._buffer) >= MAX_GPSD_BYTES - 1:
                    self.errors += 1
                    self._buffer.clear()
                    self._discard = True
                else:
                    self._buffer.append(byte)
        return result


class LocationTracker:
    def __init__(self, fresh_ms=3000, max_speed_mps=100.0, jump_slack_m=100.0,
                 utc_tolerance_s=2.0, device=None, utc_reference=None):
        if type(fresh_ms) is not int or not 100 <= fresh_ms <= 60000:
            raise ValueError("invalid freshness policy")
        if not _finite(max_speed_mps, 0.1, 1000) or not _finite(jump_slack_m, 0, 10000):
            raise ValueError("invalid movement policy")
        if not _finite(utc_tolerance_s, 0.01, 60):
            raise ValueError("invalid UTC policy")
        if device is not None and (not isinstance(device, str) or not 1 <= len(device) <= 256):
            raise ValueError("explicit gpsd device identity invalid")
        self.fresh_ms = fresh_ms
        self.max_speed_mps = float(max_speed_mps)
        self.jump_slack_m = float(jump_slack_m)
        self.utc_tolerance_s = float(utc_tolerance_s)
        self.device = device
        self.utc_reference = utc_reference
        self._bound_device = device
        self._now = None
        self._clock_fault = False
        self._fixes = {}
        self._healthy = {"gpsd": False, "nmea": False}
        self._good_3d = {"gpsd": 0, "nmea": 0}
        self._last_good = None
        self._manual = None
        self._nmea_buffer = bytearray()
        self._nmea_discard = False
        self._nmea_date = None
        self._gsa = {}
        self._gst = None
        self._sky = None  # (device, epoch, satellites used, received_ms) awaiting its TPV
        self._sky_count = None  # (device, satellites used, received_ms) last applied to a gpsd fix
        self._candidate = {}
        self._zda_candidate = None
        # Per source: an accepted fix clears only its own source's fault.
        self._active_fault = {"gpsd": None, "nmea": None}
        self.last_error = None
        self.rejected_count = 0
        self.ignored_count = 0

    def _clock(self, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be nonnegative monotonic integer ms")
        if self._now is not None and now_ms < self._now:
            self._clock_fault = True
            self.invalidate("gpsd", "MONOTONIC_TIME_REVERSED")
            self.invalidate("nmea", "MONOTONIC_TIME_REVERSED")
            return False
        self._now = now_ms
        return not self._clock_fault

    def invalidate(self, source, reason):
        if source not in self._healthy:
            raise ValueError("unknown GNSS source")
        self._healthy[source] = False
        self._good_3d[source] = 0
        if source == "gpsd":  # no satellite count survives a gpsd fault
            self._sky = self._sky_count = None
        self.last_error = self._active_fault[source] = str(reason)[:64]
        self.rejected_count += 1
        return False

    def _delta(self, previous, record):
        if previous["utc_s"] is not None and record["utc_s"] is not None:
            return record["utc_s"] - previous["utc_s"]
        if previous["tod_s"] is not None and record["tod_s"] is not None:
            return (record["tod_s"] - previous["tod_s"] + 43200) % 86400 - 43200
        return None

    def _discontinuity(self, record, reason):
        # A single jump never passes. Only three distinct epochs that agree with
        # monotonic receipt on the new timeline retire the old time reference;
        # the next epoch is then a first fix again (UTC/3D gates restart).
        source = record["origin"]
        candidate = self._candidate.get(source)
        delta = None if candidate is None else self._delta(candidate[0], record)
        if delta is None or abs(delta) > 0.000001:
            consistent = delta is not None and delta > 0 and abs(
                delta - (record["received_ms"] - candidate[0]["received_ms"]) / 1000) <= self.utc_tolerance_s
            candidate = self._candidate[source] = (record, candidate[1] + 1 if consistent else 1)
        if candidate[1] >= 3:
            self._fixes.pop(source, None)
            self._candidate.pop(source, None)
            if source == "nmea":
                self._nmea_date = self._zda_candidate = None
        return self.invalidate(source, reason)

    def _record(self, source, lat, lon, now_ms, **extra):
        result = {"origin": source, "lat": float(lat), "lon": float(lon),
                  "received_ms": now_ms, "utc": None, "utc_s": None,
                  "tod_s": None, "mode": 2, "uncertainty_m": None,
                  "uncertainty_basis": "not_reported", "alt_msl_m": None,
                  "alt_hae_m": None, "speed_mps": None, "track_deg": None,
                  "hdop": None, "satellites": None, "utc_verified": False,
                  "leap_second": False, "device": None}
        result.update(extra)
        return result

    def _accept(self, record):
        source, now = record["origin"], record["received_ms"]
        previous = self._fixes.get(source)
        if not _coordinate(record["lat"], record["lon"]):
            return self.invalidate(source, "COORDINATE_RANGE")
        if record["speed_mps"] is not None and record["speed_mps"] > self.max_speed_mps:
            return self.invalidate(source, "REPORTED_SPEED_IMPLAUSIBLE")
        if self.utc_reference is not None and record["utc_s"] is not None:
            try:
                reference = self.utc_reference()
                if not _finite(reference, -1e11, 1e11) or abs(record["utc_s"] - reference) > self.utc_tolerance_s:
                    return self.invalidate(source, "UTC_REFERENCE_MISMATCH")
            except (OSError, ValueError, TypeError):
                return self.invalidate(source, "UTC_REFERENCE_UNAVAILABLE")
        duplicate = False
        if previous is not None:
            elapsed = (now - previous["received_ms"]) / 1000
            delta = self._delta(previous, record)
            if delta is not None:
                if delta < -0.000001:
                    return self._discontinuity(record, "UTC_REVERSED")
                duplicate = abs(delta) <= 0.000001
                if not duplicate and abs(delta - elapsed) > self.utc_tolerance_s:
                    return self._discontinuity(record, "UTC_TIME_JUMP")
            if duplicate:
                if _distance(previous["lat"], previous["lon"], record["lat"], record["lon"]) > self.jump_slack_m:
                    return self.invalidate(source, "CONTRADICTORY_EPOCH")
                # gpsd may send several partial TPVs at one epoch. Enrich only;
                # cached/repeated UTC never refreshes position receipt time.
                for key in ("uncertainty_m", "alt_msl_m", "alt_hae_m", "hdop", "satellites"):
                    if record[key] is not None:
                        previous[key] = record[key]
                if record["uncertainty_m"] is not None:
                    previous["uncertainty_basis"] = record["uncertainty_basis"]
                if previous["utc_s"] is None and record["utc_s"] is not None:
                    previous["utc_s"], previous["utc"] = record["utc_s"], record["utc"]
                self.ignored_count += 1
                return False
        if self._last_good is not None:
            elapsed = max(0, now - self._last_good["received_ms"]) / 1000
            distance = _distance(self._last_good["lat"], self._last_good["lon"], record["lat"], record["lon"])
            if distance > self.jump_slack_m + self.max_speed_mps * elapsed:
                return self.invalidate(source, "POSITION_JUMP")
        self._fixes[source] = record
        self._last_good = record
        self._healthy[source] = True
        self._candidate.pop(source, None)
        self._active_fault[source] = None
        self._good_3d[source] = self._good_3d[source] + 1 if record["mode"] == 3 else 0
        record["utc_verified"] = (self.utc_reference is not None and record["utc_s"] is not None
                                  and self._good_3d[source] >= 3 and not record["leap_second"])
        return True

    def ingest_gpsd(self, report, now_ms):
        if not self._clock(now_ms):
            return False
        if not isinstance(report, dict) or len(report) > 128:
            return self.invalidate("gpsd", "GPSD_OBJECT")
        if report.get("class") == "GST":
            current = self._fixes.get("gpsd")
            # Omitted GST fields are unknown estimates, not a fault of the fix.
            if (current is None or report.get("device") != current["device"]
                    or now_ms - current["received_ms"] >= self.fresh_ms
                    or "time" not in report or "lat" not in report or "lon" not in report):
                self.ignored_count += 1
                return False
            try:
                epoch, unused = _gpsd_time(report["time"])
                if abs(epoch - current["utc_s"]) > 0.5:
                    self.ignored_count += 1
                    return False
                if not _finite(report.get("lat"), 0, 1000000) or not _finite(report.get("lon"), 0, 1000000):
                    raise ValueError("GPSD_GST_ERROR")
                current["uncertainty_m"] = math.hypot(report["lat"], report["lon"])
                current["uncertainty_basis"] = "gpsd_gst_axis_rss"
                self.ignored_count += 1
                return False
            except (ValueError, TypeError, OverflowError):
                return self.invalidate("gpsd", "GPSD_GST_ERROR")
        if report.get("class") == "SKY":
            return self._gpsd_sky(report, now_ms)
        if report.get("class") != "TPV":
            self.ignored_count += 1
            return False
        device = report.get("device")
        if device is not None and (not isinstance(device, str) or len(device) > 256):
            return self.invalidate("gpsd", "GPSD_DEVICE")
        if self._bound_device is not None and device != self._bound_device:
            self.ignored_count += 1
            return False
        mode = report.get("mode")
        if type(mode) is not int or mode not in (2, 3):
            return self.invalidate("gpsd", "GPSD_NO_FIX")
        if "status" in report and (type(report["status"]) is not int or not 0 <= report["status"] <= 9):
            return self.invalidate("gpsd", "GPSD_STATUS")
        if report.get("status") in (5, 6, 7, 8):
            return self.invalidate("gpsd", "GPSD_ESTIMATED_OR_SIMULATED")
        if "lat" not in report or "lon" not in report or "time" not in report:
            # Omitted optional fields are not zero and cannot refresh old data.
            self.ignored_count += 1
            return False
        lat, lon = report["lat"], report["lon"]
        if not _coordinate(lat, lon):
            return self.invalidate("gpsd", "GPSD_COORDINATE")
        try:
            epoch, leap = _gpsd_time(report["time"])
            uncertainty, basis = None, "not_reported"
            if any(key in report and not _finite(report[key], 0, 1000000) for key in ("eph", "epx", "epy")):
                raise ValueError("GPSD_UNCERTAINTY")
            if "eph" in report:
                if not _finite(report["eph"], 0, 1000000):
                    raise ValueError("GPSD_UNCERTAINTY")
                uncertainty, basis = float(report["eph"]), "gpsd_eph"
            elif "epx" in report and "epy" in report:
                if not _finite(report["epx"], 0, 1000000) or not _finite(report["epy"], 0, 1000000):
                    raise ValueError("GPSD_UNCERTAINTY")
                uncertainty, basis = math.hypot(report["epx"], report["epy"]), "gpsd_axis_rss"
            extra = {}
            for key, low, high in (("speed", 0, 1000), ("track", 0, 360),
                                   ("altMSL", -12000, 100000), ("altHAE", -12000, 100000)):
                if key in report and not _finite(report[key], low, high):
                    raise ValueError("GPSD_RANGE")
            if "track" in report and report["track"] >= 360:
                raise ValueError("GPSD_TRACK")
            extra.update(speed_mps=report.get("speed"), track_deg=report.get("track"))
            if mode == 3:
                extra.update(alt_msl_m=report.get("altMSL"), alt_hae_m=report.get("altHAE"))
            record = self._record("gpsd", lat, lon, now_ms, utc_s=epoch,
                                  utc=report["time"], leap_second=leap, mode=mode,
                                  uncertainty_m=uncertainty, uncertainty_basis=basis,
                                  device=device, **extra)
            sky, last = self._sky, self._sky_count
            if (sky is not None and sky[0] == device and abs(sky[1] - epoch) <= 0.5
                    and 0 <= now_ms - sky[3] < self.fresh_ms):
                record["satellites"], self._sky = sky[2], None  # a SKY of this epoch came before its TPV
                self._sky_count = (device, sky[2], now_ms)
            elif last is not None and last[0] == device and 0 <= now_ms - last[2] <= SKY_CARRY_MS:
                # gpsd sends SKY after its TPV: the previous epoch's count bridges at most
                # SKY_CARRY_MS until this epoch's SKY replaces it; then it is unknown again.
                record["satellites"] = last[1]
            accepted = self._accept(record)
            if accepted and self._bound_device is None:
                self._bound_device = device
            return accepted
        except (ValueError, OverflowError, TypeError) as exc:
            return self.invalidate("gpsd", str(exc) or "GPSD_INVALID")

    def _gpsd_sky(self, report, now_ms):
        """Satellites used in the solution: SKY uSat, else the count of used=true entries.

        Bound like GST: same device as the gpsd fix and the same epoch (SKY time
        within 0.5 s of the TPV time); a SKY that comes before its TPV waits at
        most fresh_ms. The next TPV keeps the last applied count for at most
        SKY_CARRY_MS (gpsd sends SKY after its TPV), never longer. A SKY without
        time or without a count is ignored, so such a fix keeps an unknown count
        (never a qualified fix). Never a new fix.
        """
        device = report.get("device")
        if ((device is not None and (not isinstance(device, str) or len(device) > 256))
                or (self._bound_device is not None and device != self._bound_device) or "time" not in report):
            self.ignored_count += 1
            return False
        try:
            epoch, unused = _gpsd_time(report["time"])
            counts = []
            if "uSat" in report:
                if type(report["uSat"]) is not int or not 0 <= report["uSat"] <= 1000:
                    raise ValueError("GPSD_SKY")
                counts.append(report["uSat"])
            if "satellites" in report:
                satellites = report["satellites"]
                if (not isinstance(satellites, list) or len(satellites) > 1000
                        or any(not isinstance(item, dict) or type(item.get("used")) is not bool for item in satellites)):
                    raise ValueError("GPSD_SKY")
                counts.append(sum(item["used"] for item in satellites))
        except (ValueError, TypeError, OverflowError):
            return self.invalidate("gpsd", "GPSD_SKY")
        self.ignored_count += 1
        if not counts:
            return False
        used = min(counts)  # uSat and the list disagree: the smaller count (fail closed)
        current = self._fixes.get("gpsd")
        if (current is not None and current["device"] == device and current["utc_s"] is not None
                and abs(epoch - current["utc_s"]) <= 0.5 and now_ms - current["received_ms"] < self.fresh_ms):
            current["satellites"], self._sky = used, None
            self._sky_count = (device, used, now_ms)
        else:
            self._sky = (device, epoch, used, now_ms)
        return False

    def _nmea_epoch(self, value, now_ms, explicit_date=None):
        hour, minute, second = _tod(value)
        tod = hour * 3600 + minute * 60 + second
        date = explicit_date
        if date is None and self._nmea_date is not None:
            anchor_epoch, received = self._nmea_date
            if now_ms - received <= 120000:
                estimate = anchor_epoch + (now_ms - received) / 1000
                midnight = math.floor(estimate / 86400) * 86400
                options = (midnight + tod - 86400, midnight + tod, midnight + tod + 86400)
                epoch = min(options, key=lambda candidate: abs(candidate - estimate))
                return epoch, tod, second >= 60
        if date is not None:
            epoch, leap = _dated_epoch(date, hour, minute, second)
            return epoch, tod, leap
        return None, tod, second >= 60

    def _nmea_line(self, line, now_ms):
        if (not 7 <= len(line) <= MAX_NMEA_BYTES or not line.startswith(b"$")
                or line.count(b"*") != 1 or any(byte < 32 or byte > 126 for byte in line)):
            return self.invalidate("nmea", "NMEA_FRAMING")
        body, checksum = line[1:].split(b"*")
        if not re.fullmatch(b"[0-9A-Fa-f]{2}", checksum):
            return self.invalidate("nmea", "NMEA_CHECKSUM")
        actual = 0
        for byte in body:
            actual ^= byte
        if actual != int(checksum, 16):
            return self.invalidate("nmea", "NMEA_CHECKSUM")
        fields = body.decode("ascii").split(",")
        if len(fields[0]) != 5 or fields[0][:2] not in TALKERS:
            self.ignored_count += 1
            return False
        talker, kind = fields[0][:2], fields[0][2:]
        try:
            if kind == "ZDA":
                if len(fields) < 7:
                    raise ValueError("NMEA_FIELDS")
                if not all(fields[1:5]):
                    # Receiver has no date/time yet; an empty ZDA is not a fault.
                    self.ignored_count += 1
                    return False
                date = dt.date(int(fields[4]), int(fields[3]), int(fields[2]))
                epoch, tod, leap = self._nmea_epoch(fields[1], now_ms, date)
                previous = self._nmea_date
                # Only the same <=120 s anchor window that may date GGA/RMC is checked.
                if (previous and now_ms - previous[1] <= 120000
                        and abs(epoch - previous[0] - (now_ms - previous[1]) / 1000) > self.utc_tolerance_s):
                    # As for positions: one jump never moves the anchor, but three
                    # distinct ZDAs consistent on one new timeline retire it. Accepted
                    # GGAs keep refreshing the old anchor, so a GGA+ZDA stream would
                    # otherwise never follow a receiver date correction.
                    candidate = self._zda_candidate
                    delta = None if candidate is None else epoch - candidate[0]
                    if delta is None or abs(delta) > 0.000001:
                        consistent = delta is not None and delta > 0 and abs(
                            delta - (now_ms - candidate[1]) / 1000) <= self.utc_tolerance_s
                        candidate = self._zda_candidate = (epoch, now_ms, candidate[2] + 1 if consistent else 1)
                    if candidate[2] < 3:
                        raise ValueError("NMEA_DATE_JUMP")
                    # The next NMEA position is a first fix on the new date (UTC/3D restart).
                    self._fixes.pop("nmea", None)
                    self._candidate.pop("nmea", None)
                    self._zda_candidate, self._nmea_date = None, (epoch, now_ms)
                    return self.invalidate("nmea", "NMEA_DATE_JUMP")
                self._zda_candidate = None
                self._nmea_date = (epoch, now_ms)
                self.ignored_count += 1
                return False
            if kind == "GSA":
                if len(fields) < 18 or fields[1] not in ("A", "M") or fields[2] not in ("1", "2", "3"):
                    raise ValueError("NMEA_GSA")
                self._gsa[talker] = (int(fields[2]), now_ms)
                current = self._fixes.get("nmea")
                if fields[2] == "1" and current and current.get("talker") == talker:
                    return self.invalidate("nmea", "NMEA_NO_FIX")
                self.ignored_count += 1
                return False
            if kind == "GST":
                if len(fields) < 9:
                    raise ValueError("NMEA_GST")
                error_lat = _nmea_number(fields[6], 0, 1000000)
                error_lon = _nmea_number(fields[7], 0, 1000000)
                if not fields[1] or error_lat is None or error_lon is None:
                    # Empty estimate fields mean "unknown"; they never invalidate the fix.
                    self.ignored_count += 1
                    return False
                hour, minute, second = _tod(fields[1])
                self._gst = (hour * 3600 + minute * 60 + second,
                             math.hypot(error_lat, error_lon), now_ms)
                current = self._fixes.get("nmea")
                if current is not None and now_ms - current["received_ms"] < self.fresh_ms:
                    difference = abs((self._gst[0] - current["tod_s"] + 43200) % 86400 - 43200)
                    if difference <= 0.5:
                        current["uncertainty_m"] = self._gst[1]
                        current["uncertainty_basis"] = "nmea_gst_axis_rss"
                self.ignored_count += 1
                return False
            if kind not in ("RMC", "GGA"):
                self.ignored_count += 1
                return False
            if kind == "RMC":
                if len(fields) < 10:
                    raise ValueError("NMEA_FIELDS")
                if fields[2] != "A" or len(fields) > 12 and fields[12] not in ("", "A", "D"):
                    return self.invalidate("nmea", "NMEA_NO_FIX")
                if not re.fullmatch(r"\d{6}", fields[9]):
                    raise ValueError("NMEA_DATE")
                year = int(fields[9][4:])
                # NMEA RMC has no century. Explicit conventional 1980..2079
                # window; ZDA supplies an unambiguous full year when available.
                if self._nmea_date is not None and now_ms - self._nmea_date[1] <= 120000:
                    anchor_year = dt.datetime.fromtimestamp(self._nmea_date[0], dt.timezone.utc).year
                    year = min((1900 + year, 2000 + year, 2100 + year), key=lambda candidate: abs(candidate - anchor_year))
                else:
                    year += 1900 if year >= 80 else 2000
                date = dt.date(year, int(fields[9][2:4]), int(fields[9][:2]))
                epoch, tod, leap = self._nmea_epoch(fields[1], now_ms, date)
                lat = _nmea_coordinate(fields[3], fields[4], True)
                lon = _nmea_coordinate(fields[5], fields[6], False)
                speed = _nmea_number(fields[7], 0, 2000)
                track = _nmea_number(fields[8], 0, 359.999999999)
                speed = None if speed is None else speed * (1852 / 3600)
                extra = {"speed_mps": speed, "track_deg": track}
            else:
                if len(fields) < 15:
                    raise ValueError("NMEA_FIELDS")
                if fields[6] not in ("1", "2"):
                    return self.invalidate("nmea", "NMEA_NO_FIX")
                epoch, tod, leap = self._nmea_epoch(fields[1], now_ms)
                lat = _nmea_coordinate(fields[2], fields[3], True)
                lon = _nmea_coordinate(fields[4], fields[5], False)
                if not re.fullmatch(r"\d{1,3}", fields[7]) or not 3 <= int(fields[7]) <= 128:
                    raise ValueError("NMEA_SATELLITES")
                hdop = _nmea_number(fields[8], 0.01, 99.98, False)
                if hdop > 20:
                    raise ValueError("NMEA_POOR_GEOMETRY")
                altitude = _nmea_number(fields[9], -12000, 100000)
                separation = _nmea_number(fields[11], -1000, 1000)
                if altitude is not None and fields[10] != "M" or separation is not None and fields[12] != "M":
                    raise ValueError("NMEA_ALTITUDE_UNITS")
                if altitude is not None and separation is not None and not -12000 <= altitude + separation <= 100000:
                    raise ValueError("NMEA_ALTITUDE_RANGE")
                extra = {"satellites": int(fields[7]), "hdop": hdop,
                         "alt_msl_m": altitude,
                         "alt_hae_m": altitude + separation if altitude is not None and separation is not None else None}
            gsa = self._gsa.get(talker)
            explicit = gsa is not None and now_ms - gsa[1] < self.fresh_ms
            mode = gsa[0] if explicit else 2
            if explicit and mode == 2 and "alt_msl_m" in extra:
                # As for gpsd: an explicit 2D solution holds/assumes altitude.
                extra["alt_msl_m"] = extra["alt_hae_m"] = None
            if mode == 1:
                return self.invalidate("nmea", "NMEA_NO_FIX")
            if mode == 3 and extra.get("satellites", 4) < 4:
                return self.invalidate("nmea", "NMEA_SATELLITES")
            uncertainty, basis = None, "hdop_not_accuracy" if extra.get("hdop") is not None else "not_reported"
            if self._gst is not None:
                gst_tod, gst_error, gst_received = self._gst
                difference = abs((gst_tod - tod + 43200) % 86400 - 43200)
                if difference <= 0.5 and now_ms - gst_received < self.fresh_ms:
                    uncertainty, basis = gst_error, "nmea_gst_axis_rss"
            record = self._record("nmea", lat, lon, now_ms, utc_s=epoch,
                                  utc=_iso(epoch) if epoch is not None else None,
                                  tod_s=tod, leap_second=leap, mode=mode,
                                  uncertainty_m=uncertainty, uncertainty_basis=basis,
                                  talker=talker, sentence=kind, **extra)
            accepted = self._accept(record)
            if accepted and epoch is not None:
                self._nmea_date = (epoch, now_ms)
            elif epoch is not None and self._fixes.get("nmea", {}).get("utc_s") == epoch:
                self._nmea_date = (epoch, self._fixes["nmea"]["received_ms"])
            return accepted
        except (ValueError, TypeError, OverflowError, IndexError) as exc:
            return self.invalidate("nmea", str(exc) or "NMEA_INVALID")

    def ingest_nmea(self, data, now_ms):
        if not self._clock(now_ms):
            return 0
        if isinstance(data, memoryview):
            if data.nbytes > MAX_INPUT_BYTES:
                self.invalidate("nmea", "NMEA_INPUT_LIMIT")
                self._nmea_buffer.clear()
                self._nmea_discard = False
                return 0
            data = data.tobytes()
        if isinstance(data, str):
            if len(data) > MAX_INPUT_BYTES:
                self.invalidate("nmea", "NMEA_INPUT_LIMIT")
                self._nmea_buffer.clear()
                self._nmea_discard = False
                return 0
            try:
                data = data.encode("ascii")
            except UnicodeError:
                self.invalidate("nmea", "NMEA_ASCII")
                self._nmea_buffer.clear()
                self._nmea_discard = False
                return 0
            # Text input is a complete record; bytes input is a streaming chunk.
            if not data.endswith(b"\n"):
                data += b"\n"
        if not isinstance(data, (bytes, bytearray, memoryview)) or len(data) > MAX_INPUT_BYTES:
            self.invalidate("nmea", "NMEA_INPUT_LIMIT")
            self._nmea_buffer.clear()
            self._nmea_discard = False
            return 0
        accepted = lines = 0
        for byte in data:
            if byte == 10:
                lines += 1
                if lines == 129:
                    self.invalidate("nmea", "NMEA_BATCH_LIMIT")
                if lines <= 128 and self._nmea_buffer and not self._nmea_discard:
                    line = bytes(self._nmea_buffer)
                    if line.endswith(b"\r"):
                        line = line[:-1]
                    accepted += int(self._nmea_line(line, now_ms))
                self._nmea_buffer.clear()
                self._nmea_discard = False
            elif byte == 36:
                if self._nmea_buffer or self._nmea_discard:
                    self.invalidate("nmea", "NMEA_RESYNC")
                self._nmea_buffer = bytearray(b"$")
                self._nmea_discard = False
            elif not self._nmea_discard:
                if len(self._nmea_buffer) >= MAX_NMEA_BYTES:
                    self.invalidate("nmea", "NMEA_LINE_LIMIT")
                    self._nmea_buffer.clear()
                    self._nmea_discard = True
                else:
                    self._nmea_buffer.append(byte)
        return accepted

    def manual(self, lat, lon, now_ms):
        if not self._clock(now_ms):
            raise ValueError("monotonic clock fault; construct a new tracker")
        if not _coordinate(lat, lon):
            raise ValueError("manual coordinates must be finite decimal degrees")
        self._manual = self._record("manual", lat, lon, now_ms,
                                    mode=None, uncertainty_basis="manual_unspecified")
        return self.status(now_ms)

    def status(self, now_ms):
        self._clock(now_ms)
        live = [record for source, record in self._fixes.items()
                if not self._clock_fault and self._healthy[source]
                and now_ms - record["received_ms"] < self.fresh_ms]
        if live:
            record = max(live, key=lambda value: (value["received_ms"], value["origin"] == "gpsd"))
            source, fresh, reason = record["origin"], True, None
        else:
            fallback = [record for record in (self._last_good, self._manual) if record is not None]
            record = max(fallback, key=lambda value: (value["received_ms"], value["origin"] == "manual")) if fallback else None
            source = "manual" if record and record["origin"] == "manual" else "last_good" if record else "none"
            fresh = False
            # last_error is history; only an unrecovered fault explains a fallback:
            # first that of the fallback record's own source, else another source's.
            faults = [self._active_fault[name] for name in (record and record["origin"], "gpsd", "nmea")
                      if self._active_fault.get(name)]
            reason = ("MONOTONIC_TIME_REVERSED" if self._clock_fault else faults[0] if faults else
                      "MANUAL_FALLBACK" if source == "manual" else "STALE" if record else "NO_LOCATION")
        result = {"available": record is not None, "source": source,
                  "origin": record["origin"] if record else None,
                  "fresh": fresh, "live_fix": fresh, "age_ms": None,
                  "lat": None, "lon": None, "utc": None, "mode": None,
                  "alt_msl_m": None, "alt_hae_m": None, "speed_mps": None,
                  "track_deg": None, "hdop": None, "satellites": None,
                  "uncertainty_m": None, "fix_uncertainty_m": None,
                  "uncertainty_basis": "unavailable", "uncertainty_confidence": "unknown",
                  "utc_verified": False, "leap_second": False,
                  "device": None, "reason": reason, "last_error": self.last_error,
                  "rejected_count": self.rejected_count, "ignored_count": self.ignored_count}
        if record is not None:
            for key in ("lat", "lon", "utc", "mode", "alt_msl_m", "alt_hae_m",
                        "speed_mps", "track_deg", "hdop", "satellites", "utc_verified",
                        "leap_second", "device"):
                result[key] = record[key]
            result["age_ms"] = None if self._clock_fault else max(0, now_ms - record["received_ms"])
            result["fix_uncertainty_m"] = record["uncertainty_m"]
            if fresh:
                result["uncertainty_m"] = record["uncertainty_m"]
                result["uncertainty_basis"] = record["uncertainty_basis"]
            else:
                result["uncertainty_basis"] = "manual_unspecified" if source == "manual" else "stale_position_unbounded"
                result["utc_verified"] = False
                result["speed_mps"] = result["track_deg"] = None
        return result


class GpsdClient:
    """Explicit loopback-only gpsd connection, nonblocking and no auto reconnect."""
    WATCH = b'?WATCH={"enable":true,"json":true};\n'

    def __init__(self, tracker, host, port):
        if not isinstance(host, str):
            raise ValueError("gpsd host must be explicit text")
        address = "127.0.0.1" if host == "localhost" else host
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            raise ValueError("gpsd endpoint must be explicit numeric loopback or localhost") from None
        if not parsed.is_loopback or type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("gpsd endpoint must be explicit loopback and valid port")
        self.tracker, self.address, self.port = tracker, str(parsed), port
        self.family = socket.AF_INET6 if parsed.version == 6 else socket.AF_INET
        self.decoder = GpsdJSONDecoder()
        self.sock = None
        self.connected = self.watching = False
        self.error = None
        self._pending = bytearray()
        self._started = None
        self._last_now = None
        self._version_ok = False

    def start(self, now_ms):
        if type(now_ms) is not int or now_ms < 0 or self.sock is not None:
            raise ValueError("invalid/already-started gpsd client")
        self._started = self._last_now = now_ms
        self._version_ok = False
        self.error = None
        try:
            self.sock = socket.socket(self.family, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            result = self.sock.connect_ex((self.address, self.port))
        except OSError:
            self.close("GPSD_CONNECT_FAILED")
            return False
        if result == 0:
            self.connected = True
        elif result not in (errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY):
            self.close("GPSD_CONNECT_FAILED")
        return self.sock is not None

    def close(self, reason="GPSD_DISCONNECTED"):
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        self.connected = self.watching = False
        self.error = reason
        self._pending.clear()
        self.decoder.reset()
        self.tracker.invalidate("gpsd", reason)

    def poll(self, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("invalid monotonic time")
        if self.sock is None:
            return 0
        if self._last_now is not None and now_ms < self._last_now:
            self.close("GPSD_MONOTONIC_TIME_REVERSED")
            return 0
        self._last_now = now_ms
        count = 0
        try:
            if not self.connected:
                if select.select([], [self.sock], [], 0)[1]:
                    if self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                        self.close("GPSD_CONNECT_FAILED")
                        return 0
                    self.connected = True
            if not self.connected:
                if now_ms - self._started >= 3000:
                    self.close("GPSD_HANDSHAKE_TIMEOUT")
                return 0
            for unused in range(4):
                try:
                    data = self.sock.recv(4096)
                except BlockingIOError:
                    break
                if not data:
                    self.close("GPSD_DISCONNECTED")
                    return count
                errors = self.decoder.errors
                frames = self.decoder.feed(data)
                if self.decoder.errors != errors:
                    self.tracker.invalidate("gpsd", "GPSD_JSON")
                for frame in frames:
                    if frame.get("class") == "VERSION":
                        if type(frame.get("proto_major")) is not int or frame["proto_major"] != 3:
                            self.close("GPSD_PROTOCOL_UNSUPPORTED")
                            return count
                        if not self._version_ok:
                            self._started = now_ms  # The WATCH acknowledgement gets its own 3 s window.
                        self._version_ok = True
                        if not self.watching and not self._pending:
                            self._pending.extend(self.WATCH)
                    elif frame.get("class") == "WATCH":
                        if self._version_ok and frame.get("enable") is True and frame.get("json") is True:
                            self.watching = True
                        else:
                            self.close("GPSD_WATCH_REFUSED")
                            return count
                    elif frame.get("class") == "ERROR":
                        self.close("GPSD_SERVER_ERROR")
                        return count
                    elif frame.get("class") in ("TPV", "GST", "SKY") and self.watching:
                        count += int(self.tracker.ingest_gpsd(frame, now_ms))
            if self._pending:
                try:
                    sent = self.sock.send(self._pending)
                    if sent <= 0:
                        raise OSError("gpsd short/closed send")
                    del self._pending[:sent]
                except BlockingIOError:
                    pass
            # Checked after draining, so already-received handshake bytes count.
            if not self.watching and now_ms - self._started >= 3000:
                self.close("GPSD_HANDSHAKE_TIMEOUT")
        except OSError:
            self.close("GPSD_IO_ERROR")
        return count
