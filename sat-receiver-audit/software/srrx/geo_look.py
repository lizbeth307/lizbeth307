"""Geostationary look angles from the receiver's own fix (stdlib only).

QO-100 / Es'hail-2 sits at the nominal slot 25.9E (STACK.md:24, :185). There is
no city table, emitter lookup or network request: the observer is a
srrx.location status, and tests use only unnamed lat/lon points.

Models (both return az from true north, clockwise, and elevation):
- "sphere": the STACK model, a spherical Earth with Re/r = 0.15127 and GEO
  radius 42164 km: cos g = cos(lat)cos(dlon), el = atan((cos g - 0.15127)/sin g).
  Azimuth is the great-circle bearing to the sub-satellite point,
  atan2(sin dlon, -sin(lat)cos(dlon)); in the northern hemisphere this equals
  STACK's 180 - atan2(tan dlon, sin lat), and the same expression covers the
  southern hemisphere. Skew is STACK's tan(psi) = sin(dlon)/tan(lat).
- "wgs84" (default): geodetic observer on the WGS84 ellipsoid (optional HAE
  height) in ECEF, satellite at (r cos lon_s, r sin lon_s, 0) with r = 42164 km,
  ENU az/el. Skew comes from vector projection (below), not the tan formula.
dlon = lon_s - lon is normalised to (-180, 180].

Skew sign (STACK gives only the magnitude): the satellite's vertical (V) linear
polarisation is parallel to Earth's spin axis; projected onto the plane normal to
the line of sight it is compared with the local vertical plane. Positive skew means
the incoming V polarisation appears rotated COUNTER-CLOCKWISE as seen from behind
the LNB looking toward the satellite, so the LNB is turned CCW by that amount on
the +/-45 deg neck scale. For a northern observer west of the satellite the skew is
positive; it flips sign in the southern hemisphere. The tan formula and the vector
projection agree in sign (unit-tested independently); the bench peak search on the
beacon C/N0 in 5 deg steps (09-testy.md, P-09) is the final authority.
Near the equator (|lat| < 1 deg) skew is undefined here (SKEW_UNDEFINED_NEAR_EQUATOR).

Location gate (build/07:503, STACK.md:880): a fix is qualified only when it is a
fresh live GNSS fix (gpsd/nmea), 3D, with >= 6 reported satellites, after the
first-run stability window (3D, >= 8 satellites, within 50 m for 5 min,
FirstFixGate) and with no unconfirmed jump of more than 100 km from the last good
fix. srrx.location itself accepts as few as 3 satellites, so this gate is
mandatory. Conservative choices: an unknown satellite count never qualifies (gpsd
fixes carry the SKY satellites-used count, a TPV alone has none), the first-run
window is per process, never persisted and restarted by any gap over 5 s or a
provider failure, a jump stays unqualified until the operator confirms it, and a
backwards clock latches the gate closed. Manual and last-good
positions still give angles, labelled "not a GNSS fix". A monotonic clock fault
gives no angles. Output carries no observer coordinates.
"""
import math

QO100_LON_DEG = 25.9
GEO_RADIUS_KM = 42164.0
SPHERE_RATIO = 0.15127
WGS84_A_KM = 6378.137
WGS84_F = 1 / 298.257223563
MIN_VISIBLE_EL_DEG = 5.0
EQUATOR_GUARD_DEG = 1.0
NECK_SCALE_DEG = 45.0
QUALIFIED_MIN_SATELLITES = 6
FIRST_FIX_MIN_SATELLITES = 8
FIRST_FIX_RADIUS_M = 50.0
FIRST_FIX_WINDOW_MS = 300000
FIRST_FIX_MAX_GAP_MS = 5000
JUMP_CONFIRM_M = 100000.0  # STACK.md:880 "стрибок понад 100 km — з підтвердженням"
GNSS_SOURCES = ("gpsd", "nmea")
BISECTOR_NS, TIPS_NS = "BISECTOR_NS", "TIPS_NS"
DIPOLE_TEXT = {BISECTOR_NS: "V-dipole bisector N-S (tips E-W)", TIPS_NS: "V-dipole tips N-S (side toward the pass)"}
NOMINAL_TLE_STATUS = "nominal slot 25.9E; TLE not verified"
FINAL_AUTHORITY = "bench peak search by beacon C/N0 in 5 deg steps (09-testy.md P-09)"


def _number(value, low, high, label):
    if type(value) not in (int, float):
        raise ValueError(label + " must be a finite number, not boolean")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(label + " must be finite") from exc
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(label + " out of range")
    return number


def _wrap180(degrees):
    value = math.fmod(degrees, 360.0)
    if value <= -180.0:
        value += 360.0
    elif value > 180.0:
        value -= 360.0
    return value


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    size = math.sqrt(_dot(a, a))
    return (a[0] / size, a[1] / size, a[2] / size)


def _reject(a, axis):
    k = _dot(a, axis)
    return (a[0] - k * axis[0], a[1] - k * axis[1], a[2] - k * axis[2])


def _sphere(lat, dlon):
    phi, d = math.radians(lat), math.radians(dlon)
    cos_g = max(-1.0, min(1.0, math.cos(phi) * math.cos(d)))
    sin_g = math.sqrt(1.0 - cos_g * cos_g)
    el = math.degrees(math.atan2(cos_g - SPHERE_RATIO, sin_g))
    az = math.degrees(math.atan2(math.sin(d), -math.sin(phi) * math.cos(d))) % 360.0
    earth = SPHERE_RATIO * GEO_RADIUS_KM
    rng = math.sqrt(GEO_RADIUS_KM ** 2 + earth ** 2 - 2 * GEO_RADIUS_KM * earth * cos_g)
    skew = math.degrees(math.atan(math.sin(d) / math.tan(phi))) if abs(lat) >= EQUATOR_GUARD_DEG else None
    return az, el, rng, skew


def _wgs84(lat, lon, alt_m, sat_lon):
    phi, lam, sat = math.radians(lat), math.radians(lon), math.radians(sat_lon)
    e2 = WGS84_F * (2 - WGS84_F)
    n = WGS84_A_KM / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    h = alt_m / 1000.0
    observer = ((n + h) * math.cos(phi) * math.cos(lam), (n + h) * math.cos(phi) * math.sin(lam),
                (n * (1 - e2) + h) * math.sin(phi))
    target = (GEO_RADIUS_KM * math.cos(sat), GEO_RADIUS_KM * math.sin(sat), 0.0)
    line = (target[0] - observer[0], target[1] - observer[1], target[2] - observer[2])
    east = (-math.sin(lam), math.cos(lam), 0.0)
    north = (-math.sin(phi) * math.cos(lam), -math.sin(phi) * math.sin(lam), math.cos(phi))
    up = (math.cos(phi) * math.cos(lam), math.cos(phi) * math.sin(lam), math.sin(phi))
    rng = math.sqrt(_dot(line, line))
    el = math.degrees(math.asin(max(-1.0, min(1.0, _dot(line, up) / rng))))
    az = math.degrees(math.atan2(_dot(line, east), _dot(line, north))) % 360.0
    skew = None
    if abs(lat) >= EQUATOR_GUARD_DEG:
        sight = _unit(line)
        polarisation = _unit(_reject((0.0, 0.0, 1.0), sight))  # V-pol parallel to Earth's spin axis.
        vertical = _unit(_reject(up, sight))  # Unrotated LNB: probe in the local vertical plane.
        # Counter-clockwise for a viewer looking along +sight is a positive turn about -sight.
        back = (-sight[0], -sight[1], -sight[2])
        angle = math.degrees(math.atan2(_dot(_cross(vertical, polarisation), back), _dot(vertical, polarisation)))
        skew = math.fmod(angle + 90.0, 180.0)  # A linear polarisation is defined modulo 180 deg.
        skew = (skew + 180.0 if skew < 0 else skew) - 90.0
    return az, el, rng, skew


def geo_look_angles(lat, lon, alt_m=0.0, sat_lon_deg=QO100_LON_DEG, model="wgs84"):
    """Return az/el/range/skew from one observer point to a GEO slot."""
    lat = _number(lat, -90.0, 90.0, "latitude")
    lon = _number(lon, -180.0, 180.0, "longitude")
    alt_m = _number(alt_m, -1000.0, 20000.0, "altitude")
    sat_lon_deg = _number(sat_lon_deg, -180.0, 180.0, "satellite longitude")
    if model not in ("wgs84", "sphere"):
        raise ValueError("model must be wgs84 or sphere")
    dlon = _wrap180(sat_lon_deg - lon)
    az, el, rng, skew = _sphere(lat, dlon) if model == "sphere" else _wgs84(lat, lon, alt_m, sat_lon_deg)
    above = el > 0.0
    reason = None
    if abs(lat) < EQUATOR_GUARD_DEG:
        skew, reason = None, "SKEW_UNDEFINED_NEAR_EQUATOR"
    elif not above:
        skew, reason = None, "SATELLITE_BELOW_HORIZON"
    return {"model": model, "sat_lon_deg": sat_lon_deg, "delta_lon_deg": dlon, "az_deg": az, "el_deg": el,
            "range_km": rng, "skew_deg": skew, "skew_reason": reason, "above_horizon": above,
            "visible_5deg": el >= MIN_VISIBLE_EL_DEG}


def lnb_hint(skew_deg):
    """Operator text for the printed +/-45 deg neck scale; + = CCW viewed from behind."""
    if skew_deg is None:
        return "LNB skew unavailable"
    skew = round(_number(skew_deg, -90.0, 90.0, "skew"), 1) + 0.0  # No "-0.0".
    if abs(skew) > NECK_SCALE_DEG:
        return f"skew {skew:+.1f}° is beyond the ±45° neck scale"
    return f"rotate LNB {skew:+.1f}° (+ = CCW viewed from behind, toward the satellite)"


def v_dipole_hint(max_el_deg):
    """STACK.md:191/:238: >=35 deg bisector N-S, <=30 deg tips N-S; 30-35 deg is not
    specified, so the unattended default (bisector N-S) is used."""
    elevation = _number(max_el_deg, 0.0, 90.0, "maximum elevation")
    return TIPS_NS if elevation <= 30.0 else BISECTOR_NS


def _distance_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(min(1.0, math.sqrt(a)))


def _position(status):
    if (type(status) is not dict or status.get("available") is not True
            or type(status.get("lat")) not in (int, float) or type(status.get("lon")) not in (int, float)):
        return None
    try:
        return _number(status["lat"], -90.0, 90.0, "latitude"), _number(status["lon"], -180.0, 180.0, "longitude")
    except ValueError:
        return None


def _count(value):
    return value if type(value) is int and 0 <= value <= 1000 else None


def _live_gnss(status):
    return (status.get("source") in GNSS_SOURCES and status.get("fresh") is True
            and status.get("live_fix") is True)


class FirstFixGate:
    """First-run stability window: live 3D GNSS, >= 8 satellites, within 50 m for 5 min.

    Feed every live provider status with one nondecreasing monotonic ms clock; feed
    None when the provider fails. Any failed sample restarts the window, as does a
    gap of more than 5 s between samples (unobserved time is not stable time); a
    move beyond 50 m restarts it at the new point. Once stable it stays stable for
    this instance (not persisted). A backwards clock latches the gate closed;
    construct a new gate after repair.

    Jump confirmation (STACK.md:880): after the window, each live 3D GNSS fix is
    compared with the last good one; a fix more than 100 km away sets
    jump_pending and stays unqualified, as do all later fixes, until
    confirm_jump() (an explicit operator confirmation) makes the newest such fix
    the last good position. Returning near the old position does not clear it.
    feed() returns stable and not jump_pending.
    """
    def __init__(self):
        self.stable, self.clock_fault, self.jump_pending = False, False, False
        self._anchor = self._start_ms = self._last_ms = self._last_ok_ms = None
        self._good = self._moved = None

    def feed(self, status, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a nonnegative integer")
        if self._last_ms is not None and now_ms < self._last_ms:
            self.clock_fault, self.stable = True, False
        self._last_ms = now_ms
        if self.clock_fault:
            return False
        position = _position(status)
        if self.stable:
            if position is not None and _live_gnss(status) and status.get("mode") == 3:
                if self.jump_pending or _distance_m(*self._good, *position) > JUMP_CONFIRM_M:
                    self.jump_pending, self._moved = True, position
                else:
                    self._good = position
            return not self.jump_pending
        satellites = _count(status.get("satellites")) if type(status) is dict else None
        if (position is None or not _live_gnss(status) or status.get("mode") != 3
                or satellites is None or satellites < FIRST_FIX_MIN_SATELLITES):
            self._anchor = self._start_ms = self._last_ok_ms = None
            return False
        if (self._anchor is None or now_ms - self._last_ok_ms > FIRST_FIX_MAX_GAP_MS
                or _distance_m(*self._anchor, *position) > FIRST_FIX_RADIUS_M):
            self._anchor, self._start_ms = position, now_ms
        self._last_ok_ms = now_ms
        self.stable = now_ms - self._start_ms >= FIRST_FIX_WINDOW_MS
        if self.stable:
            self._good = position
        return self.stable

    def confirm_jump(self):
        """Operator confirmed the move: the newest far fix becomes the last good one."""
        if not self.jump_pending or self.clock_fault:
            return False
        self._good, self._moved, self.jump_pending = self._moved, None, False
        return True


def qualification(status, first_fix_stable=False, *, jump_unconfirmed=False):
    """Return (qualified, failures) for the pointing/location gate.

    jump_unconfirmed: FirstFixGate.jump_pending, a live fix more than 100 km from
    the last good position that the operator has not confirmed yet.
    """
    failures = []
    if status.get("source") not in GNSS_SOURCES:
        failures.append("NOT_A_GNSS_FIX")
    elif not _live_gnss(status):
        failures.append("GNSS_FIX_NOT_FRESH")
    if status.get("mode") != 3:
        failures.append("FIX_NOT_3D")
    satellites = _count(status.get("satellites"))
    if satellites is None:
        failures.append("SATELLITE_COUNT_UNKNOWN")
    elif satellites < QUALIFIED_MIN_SATELLITES:
        failures.append("FEWER_THAN_6_SATELLITES")
    if first_fix_stable is not True:
        failures.append("FIRST_FIX_STABILITY_NOT_ESTABLISHED")
    if jump_unconfirmed is not False:
        failures.append("POSITION_JUMP_UNCONFIRMED")
    return not failures, failures


def _fix_label(status, qualified):
    source = status.get("source")
    if source == "manual":
        return "not a GNSS fix (manual entry)"
    if source == "last_good":
        return "not a GNSS fix (last known position)"
    return "qualified GNSS fix (3D, >=6 satellites)" if qualified else "GNSS fix not qualified"


def observer_from_status(status, first_fix_stable=False, *, jump_unconfirmed=False):
    """Validated observer for look-angle/pass use, or None with a reason."""
    if type(status) is not dict:
        return None, "NO_LOCATION"
    if status.get("reason") == "MONOTONIC_TIME_REVERSED":
        return None, "MONOTONIC_TIME_REVERSED"
    position = _position(status)
    if position is None:
        if status.get("available") is True:
            return None, "INVALID_POSITION"
        reason = status.get("reason")
        return None, reason if type(reason) is str and 0 < len(reason) <= 64 else "NO_LOCATION"
    qualified, failures = qualification(status, first_fix_stable, jump_unconfirmed=jump_unconfirmed)
    alt = status.get("alt_hae_m")
    alt_basis = "HAE"
    # Range first: a codec-valid huge int (10**400) must not reach float() and raise OverflowError.
    if (status.get("mode") != 3 or type(alt) not in (int, float) or not -1000 <= alt <= 20000
            or not math.isfinite(alt)):
        alt, alt_basis = 0.0, "ASSUMED_0M"
    age = status.get("age_ms")
    return {"lat": position[0], "lon": position[1], "alt_m": float(alt), "alt_basis": alt_basis,
            "source": status.get("source") if type(status.get("source")) is str else "none",
            "age_ms": age if type(age) is int and age >= 0 else None,
            "fresh": _live_gnss(status), "qualified_fix": qualified, "qualification_failures": failures,
            "fix_label": _fix_label(status, qualified)}, None


def pointing_from_status(status, *, first_fix_stable=False, qo100_omm=None, sat_lon_deg=QO100_LON_DEG, model="wgs84",
                         jump_unconfirmed=False):
    """Read-only QO-100 pointing for display: angles, skew hint and gate labels.

    qo100_omm is an srrx.orbits record whose allowlist role is QO100. Without a
    stationary one, visible_from_here stays False and the geometry is labelled
    "nominal slot 25.9E; TLE not verified". Angles always use the nominal slot.
    """
    observer, reason = observer_from_status(status, first_fix_stable, jump_unconfirmed=jump_unconfirmed)
    result = {"available": observer is not None, "reason": reason, "target": "QO-100", "sat_lon_deg": sat_lon_deg,
              "model": model, "observer_source": None, "observer_age_ms": None, "qualified_fix": False,
              "qualification_failures": [], "fix_label": "no position", "az_deg": None, "el_deg": None,
              "range_km": None, "skew_deg": None, "skew_reason": None, "lnb_hint": lnb_hint(None),
              "above_horizon": False, "geometry_visible_5deg": False, "tle_verified": False,
              "tle_status": NOMINAL_TLE_STATUS, "omm_age_days": None, "omm_age_warning": None,
              "visible_from_here": False, "auto_pointing_allowed": False, "final_authority": FINAL_AUTHORITY}
    if observer is None:
        return result
    look = geo_look_angles(observer["lat"], observer["lon"], observer["alt_m"], sat_lon_deg, model)
    result.update(observer_source=observer["source"], observer_age_ms=observer["age_ms"],
                  qualified_fix=observer["qualified_fix"], qualification_failures=observer["qualification_failures"],
                  fix_label=observer["fix_label"], az_deg=look["az_deg"], el_deg=look["el_deg"],
                  range_km=look["range_km"], skew_deg=look["skew_deg"], skew_reason=look["skew_reason"],
                  lnb_hint=lnb_hint(look["skew_deg"]), above_horizon=look["above_horizon"],
                  geometry_visible_5deg=look["visible_5deg"])
    time_verified = False
    if qo100_omm is not None:
        from .orbits import is_stationary, validate_record
        record = validate_record(qo100_omm)
        if record["role"] != "QO100":
            raise ValueError("QO-100 elements must come from the allowlist entry with role QO100")
        stationary, time_verified = is_stationary(record), record["time_verified"]
        result.update(tle_verified=stationary, omm_age_days=record["age_days"], omm_age_warning=record["age_warning"],
                      tle_status=("stationary allowlisted OMM; angles for the nominal slot 25.9E" if stationary
                                  else "allowlisted OMM is not stationary; not shown as visible"))
    result["visible_from_here"] = result["tle_verified"] and look["visible_5deg"]
    # Stale elements or an unverified clock disable auto-pointing, never reception or display.
    result["auto_pointing_allowed"] = (result["visible_from_here"] and observer["qualified_fix"]
                                       and result["omm_age_warning"] is False and time_verified)
    return result
