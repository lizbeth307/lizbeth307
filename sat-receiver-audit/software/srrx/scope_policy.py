"""labd scope rules: TDF data-quality window, LF time-signal allowlists, Artemis stop.

Stdlib only; no network, no receiver access. Every rule here can only add a
flag or a refusal. Spectrum masks stay in srrx.spectrum and are never relaxed.
Sources: STACK.md rows 118, 119, 123, 629, 871, 878; build/09-testy.md ПОЛ-09, П-12.

Conservative choices where STACK is silent (each is documented in SCOPE-POLICY.md):
- TDF: data-quality mask, not "no data" (П-12 must log the window to narrow it).
  Applies when a span touches 162 kHz +/- 1 kHz. Window is half-open Tuesday
  [06:00, 12:00) UTC, widened by the clock uncertainty; unverified UTC counts as
  in the window. Narrowing needs a reviewed root-owned record; widening is free.
- Artemis: any entry overlapping the selected span counts; deny terms match as
  substrings of casefolded text with separators removed, after Cyrillic/Greek
  look-alikes of either case are mapped and, separately, Cyrillic is
  transliterated (false positives such as "OTH" in "other" are accepted: fail
  closed; other scripts and translated words are not covered); masked bands are the union of
  spectrum.MASKED_BANDS_HZ and the STACK bands; a stop latches the span until the
  receiver retunes away; a missing or unaccepted database is UNAVAILABLE, never
  "in scope", and the masked-band stop still applies.
- artemis-db v74 itself is SQLite; labd never parses it: it is detected and
  refused. srrx.artemis_convert checks the v74 schema and writes the reviewed
  normalized mirror (JSON, see SCOPE-POLICY.md), which alone is loaded, by exact SHA256.
"""
from __future__ import annotations

import bisect
from collections import deque, namedtuple
from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import unicodedata

from .spectrum import MASKED_BANDS_HZ as _SPECTRUM_MASKED_BANDS_HZ

OUT_OF_SCOPE = "out of scope"
MAX_ABS_HZ = 1e12
# STACK.md:85/:873 "маска діапазонів" (3-30 kHz, 225-400 MHz, 1544.0-1545.0 MHz) and the
# Cospas-Sarsat 406.0-406.1 MHz uplink (STACK.md:626, :162; scans stop at 405.9 MHz, :600), kept
# here so a scope stop never depends on spectrum.py alone; its 1530-1660 MHz mask is stricter and kept.
STACK_MASKED_BANDS_HZ = ((3_000.0, 30_000.0), (225_000_000.0, 400_000_000.0),
                         (406_000_000.0, 406_100_000.0), (1_544_000_000.0, 1_545_000_000.0))


def _union(bands):
    merged = []
    for low, high in sorted(bands):
        if merged and low <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return tuple(merged)


MASKED_BANDS_HZ = _union(_SPECTRUM_MASKED_BANDS_HZ + STACK_MASKED_BANDS_HZ)
_EVIDENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
# Module-local indirection: tests patch this name, never the process-wide os.lstat.
_lstat = os.lstat
# Never blocks on a FIFO/tty swapped in after lstat, never follows a final symlink.
_READ_FLAGS = (os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0) |
               getattr(os, "O_NOCTTY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0))


class ScopeRefused(ValueError):
    """Stable refusal code; never embeds a frequency, position or input text."""


def _refuse(code):
    raise ScopeRefused(code)


def _finite(value):
    """float of a finite int/float (never bool or an int beyond float range), else None."""
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def _number(value, code):
    number = _finite(value)
    if number is None or abs(number) > MAX_ABS_HZ:
        _refuse(code)
    return number


def _span(low, high):
    low, high = _number(low, "SPAN_INVALID"), _number(high, "SPAN_INVALID")
    if low > high:
        _refuse("SPAN_INVALID")
    return low, high


def _touch(low, high, a, b):
    return a <= high and b >= low  # closed intervals: an edge contact counts


def _hits(low, high, bands):
    # A real input also appears at -f in complex baseband, as in spectrum._hits.
    return any(_touch(lo, hi, a, b) for lo, hi in ((low, high), (-high, -low)) for a, b in bands)


def _strict_json(data, code):
    def reject(_):
        _refuse(code)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _refuse(code)
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), parse_constant=reject, object_pairs_hook=unique)
    except (UnicodeError, ValueError, RecursionError):
        _refuse(code)


def _read_regular(path, info, limit):
    """At most limit + 1 bytes of the regular file that lstat reported as info.

    The open is nonblocking and does not follow a final symlink; fstat must show
    the same regular inode, so a FIFO, device or swapped file is never read.
    """
    if not stat.S_ISREG(info.st_mode):
        _refuse("NOT_REGULAR_FILE")
    descriptor = os.open(path, _READ_FLAGS)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            _refuse("NOT_REGULAR_FILE")
        chunks, size = [], 0
        while size <= limit:
            block = os.read(descriptor, min(1 << 20, limit + 1 - size))
            if not block:
                break
            chunks.append(block)
            size += len(block)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _admin_record(path, limit=8192):
    """Strict JSON from a root-owned regular file without group/world write.

    Every parent directory must be a root-owned directory without group/world
    write (sticky world-writable allowed), so no user can swap the record.
    """
    path = Path(path)
    if not path.is_absolute():
        _refuse("ABSOLUTE_RECORD_PATH_REQUIRED")
    try:
        info = _lstat(path)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022 or
                info.st_size > limit):
            _refuse("TRUSTED_ADMIN_RECORD_REQUIRED")
        for parent in path.parents:
            folder = _lstat(parent)
            if (not stat.S_ISDIR(folder.st_mode) or folder.st_uid != 0 or
                    (folder.st_mode & 0o022 and not folder.st_mode & stat.S_ISVTX)):
                _refuse("ADMIN_OWNED_DIRECTORY_REQUIRED")
        data = _read_regular(path, info, limit)
    except ScopeRefused as error:
        if str(error) == "NOT_REGULAR_FILE":
            _refuse("TRUSTED_ADMIN_RECORD_REQUIRED")
        raise
    except OSError:
        _refuse("RECORD_UNAVAILABLE")
    if len(data) > limit:
        _refuse("TRUSTED_ADMIN_RECORD_REQUIRED")
    return _strict_json(data, "RECORD_SCHEMA")


def _keys(value, expected, code):
    if not isinstance(value, dict) or set(value) != set(expected):
        _refuse(code)


# --- TDF 162 kHz weekly maintenance: data-quality mask --------------------------------
TDF_CARRIER_HZ, TDF_GUARD_HZ = 162_000.0, 1_000.0
TDF_BAND_HZ = ((TDF_CARRIER_HZ - TDF_GUARD_HZ, TDF_CARRIER_HZ + TDF_GUARD_HZ),)
TDF_WEEKDAY = 1  # Tuesday, datetime.weekday() numbering
IN_WINDOW, OUT, UNKNOWN_UTC = "IN_WINDOW", "OUT", "UNKNOWN_UTC"
TDF_MAINTENANCE = "TDF_MAINTENANCE"
CLOCK_BASE_UNCERTAINTY_S, CLOCK_DRIFT_PPM = 120.0, 100.0  # STACK.md:880
_DAY, _WEEK = 86400, 7 * 86400


def clock_uncertainty_s(days_since_sync):
    """120 s + 100 ppm x days since the last approved sync; None = unverified UTC."""
    if days_since_sync is None:
        return None
    days = _finite(days_since_sync)
    if days is None or not 0 <= days <= 1e6:
        _refuse("SYNC_AGE_INVALID")
    return CLOCK_BASE_UNCERTAINTY_S + CLOCK_DRIFT_PPM * 1e-6 * _DAY * days


_REVIEW_TOKEN = object()  # held only by _tdf_window_record()


class TdfReviewedRecord:
    """A validated, reviewed root-owned TDF window record (П-12 evidence).

    Only load_tdf_window() creates one; any other construction is refused.
    """
    __slots__ = ("start_s", "end_s", "evidence_id")

    def __init__(self, token, start_s, end_s, evidence_id):
        if token is not _REVIEW_TOKEN:
            _refuse("TDF_REVIEWED_RECORD_REQUIRED")
        for name, value in (("start_s", start_s), ("end_s", end_s), ("evidence_id", evidence_id)):
            object.__setattr__(self, name, value)

    def __setattr__(self, name, value):
        raise AttributeError("TdfReviewedRecord is immutable")


class TdfWindow:
    """Tuesday [start_s, end_s) UTC, seconds of day. Default 06:00-12:00.

    Narrower than the default anywhere only with reviewed=<TdfReviewedRecord>,
    and never narrower than that record's own window (load_tdf_window()).
    widened() may always grow a window; nothing narrows automatically.
    """
    __slots__ = ("start_s", "end_s", "record")
    DEFAULT_S = (6 * 3600, 12 * 3600)

    def __init__(self, start_s=DEFAULT_S[0], end_s=DEFAULT_S[1], *, reviewed=None):
        if (type(start_s) is not int or type(end_s) is not int or not 0 <= start_s < end_s <= _DAY):
            _refuse("TDF_WINDOW_INVALID")
        if reviewed is not None and type(reviewed) is not TdfReviewedRecord:
            _refuse("TDF_REVIEWED_RECORD_REQUIRED")  # a flag or look-alike object is not a review
        low, high = self.DEFAULT_S if reviewed is None else (reviewed.start_s, reviewed.end_s)
        if start_s > low or end_s < high:
            _refuse("TDF_NARROWING_REQUIRES_REVIEWED_RECORD")
        object.__setattr__(self, "start_s", start_s)
        object.__setattr__(self, "end_s", end_s)
        object.__setattr__(self, "record", reviewed)

    def __setattr__(self, name, value):
        raise AttributeError("TdfWindow is immutable")

    @property
    def reviewed(self):
        return self.record is not None

    @property
    def evidence_id(self):
        return None if self.record is None else self.record.evidence_id

    def widened(self, start_s, end_s):
        if type(start_s) is not int or type(end_s) is not int or start_s > self.start_s or end_s < self.end_s:
            _refuse("TDF_WIDENING_ONLY")
        return TdfWindow(start_s, end_s, reviewed=self.record)


DEFAULT_TDF_WINDOW = TdfWindow()
_CLOCK = re.compile(r"(?:([01]\d|2[0-3]):([0-5]\d)|(24):(00))\Z")
_TDF_FIELDS = ("v", "kind", "weekday", "start_utc", "end_utc", "basis", "evidence_id")


def _clock_s(text):
    match = _CLOCK.fullmatch(text) if isinstance(text, str) else None
    if match is None:
        _refuse("TDF_RECORD_SCHEMA")
    hours, minutes = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
    return int(hours) * 3600 + int(minutes) * 60


def _tdf_window_record(record):
    _keys(record, _TDF_FIELDS, "TDF_RECORD_SCHEMA")
    if (type(record["v"]) is not int or record["v"] != 1 or record["kind"] != "srrx_tdf_maintenance_window" or
            record["weekday"] != "TUE" or record["basis"] != "reviewed_p12_amplitude_log" or
            not isinstance(record["evidence_id"], str) or not _EVIDENCE.fullmatch(record["evidence_id"])):
        _refuse("TDF_RECORD_SCHEMA")
    start, end = _clock_s(record["start_utc"]), _clock_s(record["end_utc"])
    if not 0 <= start < end <= _DAY:
        _refuse("TDF_WINDOW_INVALID")
    # A reviewed window narrows the default; one entirely outside it is a shift,
    # not a narrowing, and is refused (the default stays, fail closed).
    if start >= TdfWindow.DEFAULT_S[1] or end <= TdfWindow.DEFAULT_S[0]:
        _refuse("TDF_RECORD_OUTSIDE_DEFAULT_WINDOW")
    reviewed = TdfReviewedRecord(_REVIEW_TOKEN, start, end, record["evidence_id"])
    return TdfWindow(start, end, reviewed=reviewed)


def load_tdf_window(path):
    """The only way to narrow the default window: a reviewed root-owned record."""
    return _tdf_window_record(_admin_record(path))


def _epoch(value):
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            _refuse("UTC_TIME_REQUIRED")
        return value.timestamp()
    number = _finite(value)
    if number is None or abs(number) > 1e11:
        _refuse("UTC_TIME_REQUIRED")
    return number


def tdf_window_status(span_lo_hz, span_hi_hz, t_start_utc, t_end_utc, utc_uncertainty_s, *, window=None):
    """IN_WINDOW, OUT or UNKNOWN_UTC for samples taken over [t_start, t_end].

    A span without 162 kHz +/- 1 kHz is OUT (no TDF flag applies). For a TDF
    span, unverified time (utc_uncertainty_s or a time is None) is UNKNOWN_UTC,
    which consumers treat exactly like IN_WINDOW. The window is widened on both
    sides by utc_uncertainty_s (see clock_uncertainty_s()).
    """
    low, high = _span(span_lo_hz, span_hi_hz)
    window = DEFAULT_TDF_WINDOW if window is None else window
    if not isinstance(window, TdfWindow):
        _refuse("TDF_WINDOW_INVALID")
    if not _hits(low, high, TDF_BAND_HZ):
        return OUT
    if utc_uncertainty_s is None or t_start_utc is None or t_end_utc is None:
        return UNKNOWN_UTC
    uncertainty = _finite(utc_uncertainty_s)
    if uncertainty is None or uncertainty < 0:
        _refuse("UTC_UNCERTAINTY_INVALID")
    start, end = _epoch(t_start_utc), _epoch(t_end_utc)
    if start > end:
        _refuse("TIME_INTERVAL_INVALID")
    first, last = start - uncertainty, end + uncertainty
    if last - first >= _WEEK:
        return IN_WINDOW
    # 1970-01-01 was a Thursday (weekday 3); POSIX days ignore leap seconds.
    for day in range(math.floor(first / _DAY) - 1, math.floor(last / _DAY) + 2):
        if (day + 3) % 7 == TDF_WEEKDAY:
            opens, closes = day * _DAY + window.start_s, day * _DAY + window.end_s
            if first < closes and last >= opens:  # half-open [opens, closes)
                return IN_WINDOW
    return OUT


def tdf_sample_use(status):
    """In-window samples are kept but flagged and kept out of baselines and results."""
    if status in (IN_WINDOW, UNKNOWN_UTC):
        return {"keep": True, "flags": [TDF_MAINTENANCE], "sid_baseline_allowed": False,
                "derived_products_allowed": False, "decoded_time_result_allowed": False}
    if status == OUT:
        return {"keep": True, "flags": [], "sid_baseline_allowed": True,
                "derived_products_allowed": True, "decoded_time_result_allowed": True}
    _refuse("TDF_STATUS_INVALID")


# --- LF time signals and SID (STACK.md:121) -------------------------------------------
RADIO_CLOCK_DECODE_HZ = {"DCF77": 77_500.0, "MSF": 60_000.0, "TDF": 162_000.0,
                         "WWVB": 60_000.0, "JJY40": 40_000.0}
RADIO_CLOCK_AMPLITUDE_ONLY_HZ = {"JJY60": 60_000.0}
SID_CARRIERS_HZ = dict(RADIO_CLOCK_DECODE_HZ, **RADIO_CLOCK_AMPLITUDE_ONLY_HZ)
RBU_HZ, RBU_GUARD_HZ = 66_666.0, 1_000.0
SID_REFUSED_HZ = ((3_000.0, 30_000.0),)


def _station(name):
    if not isinstance(name, str) or len(name) > 32:
        _refuse("STATION_NOT_ALLOWLISTED")
    return re.sub(r"[\s_-]+", "", name).upper()


def radio_clock_mode(station):
    """DECODE or AMPLITUDE_ONLY; RBU and every unlisted station are refused."""
    name = _station(station)
    if name == "RBU":
        _refuse("RBU_BLOCKED")
    if name in RADIO_CLOCK_DECODE_HZ:
        return "DECODE"
    if name in RADIO_CLOCK_AMPLITUDE_ONLY_HZ:
        return "AMPLITUDE_ONLY"
    _refuse("RADIO_CLOCK_NOT_ALLOWLISTED")


def decoded_time_usable(station, tdf_status):
    """A decoded time is a result only for a DECODE station; TDF never in its window."""
    try:
        if radio_clock_mode(station) != "DECODE":
            return False
    except ScopeRefused:
        return False
    return _station(station) != "TDF" or tdf_status == OUT


def sid_target(station, band_lo_hz, band_hi_hz):
    """SID amplitude target: one allowlisted civil LF carrier inside its band.

    Refuses RBU (66.666 kHz), VLF 3-30 kHz and any band that misses its carrier.
    """
    name = _station(station)
    low, high = _span(band_lo_hz, band_hi_hz)
    if name == "RBU" or _hits(low, high, ((RBU_HZ - RBU_GUARD_HZ, RBU_HZ + RBU_GUARD_HZ),)):
        _refuse("RBU_BLOCKED")
    if name not in SID_CARRIERS_HZ:
        _refuse("SID_NOT_ALLOWLISTED")
    if _hits(low, high, SID_REFUSED_HZ):
        _refuse("SID_VLF_3_30_KHZ_REFUSED")
    carrier = SID_CARRIERS_HZ[name]
    if not low <= carrier <= high:
        _refuse("SID_BAND_MISSES_CARRIER")
    return {"station": name, "carrier_hz": carrier, "amplitude_only": True,
            "tdf_mask_applies": name == "TDF"}


# --- Inmarsat-C demodulation band (STACK.md:120) --------------------------------------
NCS_CANDIDATE_HZ = (1_537_000_000.0, 1_543_900_000.0)
NO_DEMOD_FROM_HZ = 1_544_000_000.0


def demod_allowed(center_hz, bw_hz):
    """Band rule only: NCS candidates 1537.0-1543.9 MHz, nothing at/above 1544.0 MHz.

    Necessary, never sufficient: egc_gate stays disabled and scope_check still
    stops on spectrum.py's stricter 1530-1660 MHz mask.
    """
    try:
        center, width = _number(center_hz, "SPAN_INVALID"), _number(bw_hz, "SPAN_INVALID")
    except ScopeRefused:
        return False
    if width <= 0:
        return False
    low, high = center - width / 2, center + width / 2
    return high < NO_DEMOD_FROM_HZ and NCS_CANDIDATE_HZ[0] <= low and high <= NCS_CANDIDATE_HZ[1]


# --- Artemis stop (STACK.md:125, :631, :873) -------------------------------------------
STOP_CATEGORIES = frozenset(("Military", "Radar", "Numbers Stations"))  # no "Government" in artemis-db
DENY_TERMS = ("military", "navy", "air force", "NATO", "STANAG", "MIL-STD", "Link-11", "Link-16",
              "ALE 4G", "4G ALE", "WALE", "jammer", "jamming", "OTH", "intelligence")
REASONS = ("CATEGORY", "DENY_REGEX", "UNTAGGED_MASKED", "MASKED_BAND")
# Look-alikes by shape, upper and lower case, mapped BEFORE casefold: Greek capital
# Nu is Latin N (its small form ν looks like v), Cyrillic Н looks like H.
_SHAPES = ("Аa Вb Еe Кk Мm Нh Оo Рp Сc Тt Уy Хx Іi Јj Ѕs Ԁd Үy Һh Ԛq Ԝw Ӏl "
           "аa вb еe кk мm нh оo рp сc тt уy хx іi јj ѕs ԁd үy һh ԛq ԝw ӏl "
           "Αa Βb Εe Ζz Ηh Ιi Κk Μm Νn Οo Ρp Τt Υy Χx αa βb εe ιi κk νv οo ρp τt υu χx").split()
_LOOKALIKE = str.maketrans({pair[0]: pair[1] for pair in _SHAPES})
# Cyrillic acronyms are transliterated too (НАТО reads NATO, СТАНАГ reads STANAG).
_TRANSLIT = str.maketrans({key: value for key, value in zip(
    "абвгдежзийклмнопрстуфхцчшщъыьэюяіїєґ",
    ("a", "b", "v", "g", "d", "e", "zh", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
     "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya", "i", "i", "ye", "g"))})


def _keep(text):
    return "".join(character for character in text if character.isalnum())


def _folds(text):
    """NFKC; look-alikes and Cyrillic transliteration, each casefolded; separators dropped."""
    text = unicodedata.normalize("NFKC", text)
    shape = text.translate(_LOOKALIKE).casefold().translate(_LOOKALIKE)
    spoken = text.casefold().translate(_TRANSLIT).translate(_LOOKALIKE)
    return {_keep(shape), _keep(spoken)}


def _fold(text):
    return _keep(unicodedata.normalize("NFKC", text).translate(_LOOKALIKE).casefold().translate(_LOOKALIKE))


_STOP_FOLDED = ("military", "radar", "numbersstation")
_DENY_FOLDED = tuple(_fold(term) for term in DENY_TERMS)
_ARTEMIS_FIELDS = {"v", "kind", "source", "db_version", "entries"}
_ENTRY_TEXT = {"name": 256, "description": 16384, "modulation": 1024, "mode": 1024, "location": 1024}
_ENTRY_REQUIRED = {"name", "categories", "ranges_hz"}
ARTEMIS_FORMAT, SQLITE_MAGIC = "srrx_artemis_mirror_v1", b"SQLite format 3\x00"
_Entry = namedtuple("_Entry", "reasons view")


def detect_format(data):
    """artemis-db's own SQLite file is recognized and refused; srrx.artemis_convert makes the mirror."""
    if bytes(data[:16]) == SQLITE_MAGIC:
        return "sqlite3"
    if bytes(data[:1]) == b"{":
        return ARTEMIS_FORMAT
    return "unknown"


def _entry(raw):
    if not isinstance(raw, dict) or not _ENTRY_REQUIRED <= set(raw) <= _ENTRY_REQUIRED | set(_ENTRY_TEXT):
        _refuse("ARTEMIS_SCHEMA")
    texts = []
    for key, limit in _ENTRY_TEXT.items():
        if key in raw:
            if not isinstance(raw[key], str) or len(raw[key]) > limit or (key == "name" and not raw[key]):
                _refuse("ARTEMIS_SCHEMA")
            texts.append(raw[key])
    categories, ranges = raw["categories"], raw["ranges_hz"]
    if (not isinstance(categories, list) or len(categories) > 32 or
            any(not isinstance(c, str) or len(c) > 128 for c in categories)):
        _refuse("ARTEMIS_SCHEMA")
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 32:
        _refuse("ARTEMIS_SCHEMA")
    checked = []
    for item in ranges:
        if not isinstance(item, list) or len(item) != 2:
            _refuse("ARTEMIS_SCHEMA")
        low, high = _number(item[0], "ARTEMIS_SCHEMA"), _number(item[1], "ARTEMIS_SCHEMA")
        if not 0 <= low <= high:
            _refuse("ARTEMIS_SCHEMA")
        checked.append((low, high))
    folded_categories = [_fold(c) for c in categories]
    reasons = set()
    if any(term in c for category in categories for c in _folds(category) for term in _STOP_FOLDED):
        reasons.add("CATEGORY")
    if any(term in folded for text in texts + categories for folded in _folds(text) for term in _DENY_FOLDED):
        reasons.add("DENY_REGEX")
    untagged = not any(folded_categories)
    if untagged and any(_hits(low, high, MASKED_BANDS_HZ) for low, high in checked):
        reasons.add("UNTAGGED_MASKED")
    if any("trunked" in c for c in folded_categories):
        view = (("occupancy", "anonymous"),)  # STACK: Trunked Radio only as nameless occupancy
    else:
        view = (("name", raw["name"]), ("categories", tuple(categories)))
    return _Entry(frozenset(reasons), view), checked


class ArtemisDB:
    """Identification aid loaded only by exact accepted SHA256; never raises on bad files.

    status is AVAILABLE or a stable UNAVAILABLE_* code. An unavailable database
    identifies nothing; scope_check still applies the masked-band stop. The path
    must be a regular file (lstat, no symlink, FIFO or device: a read never blocks).
    """
    MAX_BYTES, MAX_ENTRIES, MAX_RANGES = 64 * 1024 * 1024, 20000, 100000

    def __init__(self, status, entries=(), ranges=(), sha256=None):
        self.status, self.sha256 = status, sha256
        self._entries = tuple(entries)
        self._ranges = tuple(sorted(ranges))
        self._starts = [low for low, _, _ in self._ranges]

    @property
    def available(self):
        return self.status == "AVAILABLE"

    def __len__(self):
        return len(self._entries)

    @classmethod
    def load(cls, path, accepted_sha256):
        if not isinstance(accepted_sha256, str) or not _HEX.fullmatch(accepted_sha256):
            return cls("UNAVAILABLE_NO_ACCEPTED_SHA256")
        try:
            data = _read_regular(path, _lstat(path), cls.MAX_BYTES)
        except ScopeRefused:
            return cls("UNAVAILABLE_NOT_REGULAR_FILE")
        except (OSError, TypeError, ValueError):
            return cls("UNAVAILABLE_MISSING")
        if len(data) > cls.MAX_BYTES:
            return cls("UNAVAILABLE_SIZE_LIMIT")
        digest = hashlib.sha256(data).hexdigest()
        if not hmac.compare_digest(digest, accepted_sha256):
            return cls("UNAVAILABLE_SHA256_MISMATCH")
        kind = detect_format(data)
        if kind == "sqlite3":
            return cls("UNAVAILABLE_FORMAT_UNVERIFIED_SQLITE")
        if kind != ARTEMIS_FORMAT:
            return cls("UNAVAILABLE_FORMAT_UNKNOWN")
        try:
            document = _strict_json(data, "ARTEMIS_SCHEMA")
            if (not isinstance(document, dict) or set(document) != _ARTEMIS_FIELDS or
                    type(document["v"]) is not int or document["v"] != 1 or
                    document["kind"] != "srrx_artemis_mirror" or document["source"] != "artemis-db" or
                    document["db_version"] != "v74" or not isinstance(document["entries"], list) or
                    len(document["entries"]) > cls.MAX_ENTRIES):
                _refuse("ARTEMIS_SCHEMA")
            entries, ranges = [], []
            for index, raw in enumerate(document["entries"]):
                entry, checked = _entry(raw)
                entries.append(entry)
                ranges.extend((low, high, index) for low, high in checked)
                if len(ranges) > cls.MAX_RANGES:
                    _refuse("ARTEMIS_SCHEMA")
        except (ScopeRefused, TypeError, ValueError, OverflowError, RecursionError):
            return cls("UNAVAILABLE_SCHEMA")
        return cls("AVAILABLE", entries, ranges, digest)

    @classmethod
    def load_accepted(cls, path, record_path):
        try:
            record = load_artemis_acceptance(record_path)
        except ScopeRefused:
            return cls("UNAVAILABLE_NO_ACCEPTANCE_RECORD")
        return cls.load(path, record["sha256"])

    def _overlapping(self, low, high):
        found = set()
        for a, b in ((low, high), (-high, -low)) if low < 0 else ((low, high),):
            for position in range(bisect.bisect_right(self._starts, b)):
                _, end, index = self._ranges[position]
                if end >= a:
                    found.add(index)
        return [self._entries[index] for index in sorted(found)]


_ACCEPT_FIELDS = ("v", "kind", "db", "db_version", "format", "sha256", "evidence_id")


def load_artemis_acceptance(path):
    """Root-owned record naming the locally computed SHA256 of the reviewed mirror."""
    record = _admin_record(path)
    _keys(record, _ACCEPT_FIELDS, "ARTEMIS_ACCEPTANCE_SCHEMA")
    if (type(record["v"]) is not int or record["v"] != 1 or record["kind"] != "srrx_artemis_acceptance" or
            record["db"] != "artemis-db" or record["db_version"] != "v74" or
            record["format"] != ARTEMIS_FORMAT or not isinstance(record["sha256"], str) or
            not _HEX.fullmatch(record["sha256"]) or not isinstance(record["evidence_id"], str) or
            not _EVIDENCE.fullmatch(record["evidence_id"])):
        _refuse("ARTEMIS_ACCEPTANCE_SCHEMA")
    return record


MAX_VIEWS = 16


def scope_check(span_lo_hz, span_hi_hz, db=None):
    """Stop decision for a selected span. display is "out of scope" or entry views.

    identify: UNAVAILABLE (no accepted database), NO_MATCH, MATCHED or WITHHELD
    (stop). The result never says "in scope" and never repeats the span.
    """
    low, high = _span(span_lo_hz, span_hi_hz)
    if db is not None and not isinstance(db, ArtemisDB):
        _refuse("ARTEMIS_DB_REQUIRED")
    reasons = {"MASKED_BAND"} if _hits(low, high, MASKED_BANDS_HZ) else set()
    identify, views = "UNAVAILABLE", []
    if db is not None and db.available:
        identify = "NO_MATCH"
        for entry in db._overlapping(low, high):
            identify = "MATCHED"
            reasons |= entry.reasons
            if entry.view not in views:
                views.append(entry.view)
    if reasons:
        ordered = [reason for reason in REASONS if reason in reasons]
        return {"stop": True, "reason": ordered[0], "reasons": ordered, "identify": "WITHHELD",
                "display": OUT_OF_SCOPE}
    return {"stop": False, "reason": "NONE", "reasons": [], "identify": identify,
            "display": [{key: list(value) if isinstance(value, tuple) else value for key, value in view}
                        for view in views[:MAX_VIEWS]]}


def stop_log_line(utc):
    """UTC plus "out of scope" only: no frequency, position, bearing or entry text."""
    if isinstance(utc, datetime):
        if utc.utcoffset() is None:
            _refuse("UTC_TIME_REQUIRED")
        moment = utc.astimezone(timezone.utc)
    else:
        try:
            moment = datetime.fromtimestamp(_epoch(utc), timezone.utc)
        except (OverflowError, OSError, ValueError):
            _refuse("UTC_TIME_REQUIRED")
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ") + " " + OUT_OF_SCOPE


class ScopeLatch:
    """Session latch: a stop holds its span until the receiver retunes away.

    permits(op, span) is False for an unknown op, an invalid span, any span
    touching a latched span, or a span that scope_check stops now (which then
    latches too). Abort callbacks run on each new latch so an overlapping
    in-progress recording is aborted and its temporary output discarded
    (atomic publish, as decoder_policy.execute). Already-published files are
    not deleted: that needs an explicit operator decision (SCOPE-POLICY.md).
    Each recording registers its abort and unregisters it when it ends, so at
    most MAX_CALLBACKS are live at once over any session length. The journal
    holds MAX_LOG_LINES undrained lines; older ones are counted, never dropped
    silently: the first drained line then says how many were lost.

    Not thread-safe: a background job gets a detached_copy() and the owner
    thread adopt()s it when the job ends.
    """
    OPERATIONS = frozenset(("mark", "record", "label", "decode", "export"))
    MAX_LATCHES, MAX_CALLBACKS, MAX_LOG_LINES = 64, 16, 64

    def __init__(self, db=None, *, clock=time.time):
        if db is not None and not isinstance(db, ArtemisDB):
            _refuse("ARTEMIS_DB_REQUIRED")
        self._db, self._clock = db, clock
        self._latched, self._aborts, self._log = [], {}, deque()
        self.log_dropped = 0
        # Counts new latches (a retune release does not count: it only widens permission).
        self.latch_generation = 0
        # Set only on a detached copy: its owner, the owner's generation then, and the new stops.
        self._source, self.base_generation, self._added = None, None, []

    @property
    def stopped(self):
        return bool(self._latched)

    def detached_copy(self):
        """Copy for one background job thread: same database and latches, no aborts.

        The ArtemisDB is never modified after load, so the copy shares it. A stop
        the copy finds latches only there; adopt() on the owner thread then runs
        the abort callbacks and journals it. Confine the copy to one thread.
        """
        if self._source is not None:
            _refuse("DETACHED_COPY")
        detached = ScopeLatch(self._db, clock=self._clock)
        detached._latched = list(self._latched)
        detached._source, detached.base_generation = self, self.latch_generation
        return detached

    def adopt(self, detached):
        """Owner thread only: latch here every stop the detached copy found.

        True when nothing was latched here since the copy was made, so a result
        computed against the copy is still current. Every adopted stop runs the
        abort callbacks and journals one line, as a stop found here does; a failed
        callback still raises ABORT_CALLBACK_FAILED after all stops are latched.
        A second adopt() of the same copy adds nothing.
        """
        if not isinstance(detached, ScopeLatch) or detached._source is not self:
            _refuse("DETACHED_COPY_INVALID")
        unchanged = self.latch_generation == detached.base_generation
        added, detached._added = detached._added, []
        failure = None
        for low, high in added:
            try:
                self._latch(low, high)
            except ScopeRefused as error:
                failure = failure or error
        if failure is not None:
            raise failure
        return unchanged

    def register_abort(self, callback):
        """Return the token that unregister_abort() takes when the recording ends."""
        if self._source is not None:
            _refuse("DETACHED_COPY")
        if not callable(callback):
            _refuse("ABORT_CALLBACK_INVALID")
        if len(self._aborts) >= self.MAX_CALLBACKS:
            _refuse("ABORT_CALLBACK_LIMIT")
        token = object()
        self._aborts[token] = callback
        return token

    def unregister_abort(self, token):
        """A finished recording's callback never runs again; True if it was registered."""
        try:
            return self._aborts.pop(token, None) is not None
        except TypeError:  # an unhashable value was never a token
            return False

    def _journal(self, line):
        if len(self._log) >= self.MAX_LOG_LINES:
            self._log.popleft()
            self.log_dropped += 1
        self._log.append(line)

    def _blocked(self, low, high):
        return any(_hits(low, high, (latched,)) for latched in self._latched)

    def _latch(self, low, high):
        if any(a <= low and high <= b for a, b in self._latched):
            return
        self._latched.append((low, high))
        if len(self._latched) > self.MAX_LATCHES:  # fail closed: one hull covering all
            self._latched = [(min(a for a, _ in self._latched), max(b for _, b in self._latched))]
        self.latch_generation += 1
        if self._source is not None:
            self._added.append((low, high))  # aborts and journal run at adopt() on the owner
            return
        failed = False
        for callback in list(self._aborts.values()):  # aborts first: a bad clock must not skip them
            try:
                callback()
            except Exception:
                failed = True
        try:
            self._journal(stop_log_line(self._clock()))
        except Exception:
            if not failed:
                _refuse("STOP_LOG_TIME_UNAVAILABLE")
        if failed:
            _refuse("ABORT_CALLBACK_FAILED")

    def observe(self, span_lo_hz, span_hi_hz):
        """scope_check for the selected span; a stop latches it."""
        low, high = _span(span_lo_hz, span_hi_hz)
        decision = scope_check(low, high, self._db)
        if decision["stop"]:
            self._latch(low, high)
        elif self._blocked(low, high):
            return {"stop": True, "reason": "LATCHED", "reasons": [], "identify": "WITHHELD",
                    "display": OUT_OF_SCOPE}
        return decision

    def stop(self, span_lo_hz, span_hi_hz):
        """Operator or external identification stop; only ever adds a latch."""
        self._latch(*_span(span_lo_hz, span_hi_hz))

    def retune(self, span_lo_hz, span_hi_hz):
        """New receiver span: latches it no longer touches are released, then it is checked."""
        low, high = _span(span_lo_hz, span_hi_hz)
        self._latched = [latched for latched in self._latched if _hits(low, high, (latched,))]
        return self.observe(low, high)

    def permits(self, op, span):
        if type(op) is not str or op not in self.OPERATIONS:
            return False
        try:
            low, high = _span(*span)
        except (ScopeRefused, TypeError, ValueError):
            return False
        if self._blocked(low, high):
            return False
        if scope_check(low, high, self._db)["stop"]:
            self._latch(low, high)
            return False
        return True

    def drain_log(self):
        """Pending journal lines (UTC + "out of scope"), oldest first.

        After an overflow the first line ends "(N earlier lines dropped)"; still
        no frequency, position or entry text.
        """
        lines = list(self._log)
        if lines and self.log_dropped:
            lines[0] += " (%d earlier lines dropped)" % self.log_dropped
        self._log.clear()
        self.log_dropped = 0
        return lines
