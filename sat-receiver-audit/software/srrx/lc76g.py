"""LC76G proprietary sentences: the fixed build/07 allowlist, read-back parsing, jamming flag.

Standard library only; nothing here opens a device or sends a byte. srrx.gnss_config is
the only sender, and it can send only ALLOWLIST members, byte for byte (build/07 §18,
build/07-pz-vstanovlennia.md:485-498). $PAIR007, $PAIR752, $PAIR753, standby and any
firmware update are refused by name (build/07:500). Every checksum below is recomputed
by the tests. Reply layouts and field positions follow the Quectel LC26G/LC76G/LC86G
GNSS Protocol Specification v1.5 as transcribed in build/07; they are confirmed only on
a real receiver (BUILDER replay of a captured log, Q6A GNSS-01), never claimed here.
"""
import re

MAX_SENTENCE = 256
_FRAME = re.compile(rb"\$([A-Z][A-Z0-9]{1,19})(,[\x20-\x23\x25-\x29\x2b-\x7e]*)?\*([0-9A-Fa-f]{2})")
_VERSION = re.compile(r"[A-Za-z0-9_.+-]{1,48}")


def checksum(body):
    """XOR of the bytes between '$' and '*'."""
    value = 0
    for byte in body.encode("ascii"):
        value ^= byte
    return value


def sentence(body):
    """'$body*HH' text without line ending."""
    return "$%s*%02X" % (body, checksum(body))


def parse(line):
    """(name, fields) of one checksum-valid printable sentence without CR/LF, else None."""
    if type(line) not in (bytes, bytearray) or not 6 <= len(line) <= MAX_SENTENCE:
        return None
    match = _FRAME.fullmatch(bytes(line))
    if match is None:
        return None
    body = line[1:line.rindex(b"*")].decode("ascii")
    if checksum(body) != int(match.group(3), 16):
        return None
    name, comma, rest = body.partition(",")
    return name, (rest.split(",") if comma else [])


class Command:
    """One allowlisted sentence and the reply that completes it.

    reply: the reply sentence name; expect: the exact reply fields (None captures
    them, e.g. the version text); ack: the PAIR command id answered by
    $PAIR001,<id>,<result> (0 success, 1 still processing, other values refused).
    """
    def __init__(self, key, text, reply, expect=None, ack=None):
        self.key, self.text, self.wire = key, text, text.encode("ascii") + b"\r\n"
        self.reply, self.expect, self.ack = reply, expect, ack

    def match(self, parsed):
        """None for an unrelated line, ("ok", fields) when complete, ("error", code) on refusal."""
        if parsed is None:
            return None
        name, fields = parsed
        if self.ack is not None and name == "PAIR001":
            if len(fields) < 2 or fields[0] != str(self.ack):
                return None  # another command's acknowledgement
            if fields[1] == "0":
                return ("ok", fields) if self.reply == "PAIR001" else None
            if fields[1] == "1":
                return None  # still processing: the final result follows
            return ("error", "LC76G_PAIR_RESULT_" + (fields[1] if fields[1].isdigit() and len(fields[1]) <= 2 else "INVALID"))
        if name != self.reply:
            return None
        if fields[:1] == ["ERROR"]:
            return ("error", "LC76G_REPLY_ERROR")
        if self.expect is not None and fields != list(self.expect):
            return ("error", "LC76G_REPLY_MISMATCH")
        return ("ok", fields)


# Build/07:485-498, in its order. PPS mode 3: PPS only with a 3D fix, 100 ms pulse.
PPS_FIELDS = ("1", "1", "100", "3", "0", "0")
VERSION = Command("version", "$PQTMVERNO*58", "PQTMVERNO")
PPS_WRITE = Command("pps_write", "$PQTMCFGPPS,W,1,1,100,3,0,0*70", "PQTMCFGPPS", ("OK",))
SAVE_PQTM = Command("save_pqtm", "$PQTMSAVEPAR*5A", "PQTMSAVEPAR", ("OK",))
PPS_READ = Command("pps_read", "$PQTMCFGPPS,R,1*6A", "PQTMCFGPPS")
JAMMING_DETECT = Command("jamming_detect", "$PAIR391,1*2C", "PAIR001", ack=391)
SBAS_ENABLE = Command("sbas_enable", "$PAIR410,1*22", "PAIR001", ack=410)
DGPS_SBAS = Command("dgps_sbas", "$PAIR400,2*20", "PAIR001", ack=400)
SAVE_PAIR = Command("save_pair", "$PAIR513*3D", "PAIR001", ack=513)
DGPS_READ = Command("dgps_read", "$PAIR401*3F", "PAIR401", ack=401)
SBAS_READ = Command("sbas_read", "$PAIR411*3E", "PAIR411", ack=411)
JAMMING_RATE = Command("jamming_rate", "$PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11", "PQTMCFGMSGRATE", ("OK",))
ALLOWLIST = (VERSION, PPS_WRITE, SAVE_PQTM, PPS_READ, JAMMING_DETECT, SBAS_ENABLE, DGPS_SBAS,
             SAVE_PAIR, DGPS_READ, SBAS_READ, JAMMING_RATE)
ALLOWED_WIRE = frozenset(command.wire for command in ALLOWLIST)
WRITES = (PPS_WRITE, SAVE_PQTM, JAMMING_DETECT, SBAS_ENABLE, DGPS_SBAS, SAVE_PAIR)
READBACK = (PPS_READ, DGPS_READ, SBAS_READ)
# Expected read-back: PPS as written, DGPS source SBAS (2), SBAS enabled (1).
EXPECTED = {"pps_read": ["OK", *PPS_FIELDS], "dgps_read": ["2"], "sbas_read": ["1"]}
# Documented elsewhere in build/07:484 and checksum-verified, but never sent by gnss_config:
# a cold restart goes through labd's bounded RESET pulse instead.
DOCUMENTED_NOT_SENT = ("$PAIR006*3C",)
# build/07:500 names these three; stationary mode and field firmware updates are refused
# because nothing outside ALLOWLIST can be sent at all (no names are guessed for them).
FORBIDDEN = ("PAIR007", "PAIR752", "PAIR753")


def forbidden(wire):
    """True for a sentence named in FORBIDDEN, with or without arguments."""
    head = bytes(wire).strip().lstrip(b"$").split(b",", 1)[0].split(b"*", 1)[0]
    return head.decode("ascii", "replace") in FORBIDDEN


def version_text(fields):
    """The firmware version field of a $PQTMVERNO reply, or None if it is not plain text."""
    return fields[0] if fields and _VERSION.fullmatch(fields[0]) else None


JAMMING_HOLD_MS = 60000


class JammingMonitor:
    """Jamming flag from $PAIRSPF,<status> and $PQTMJAMMINGSTATUS,1,<status> (build/07:484).

    Status >= 2 is jamming. A well-formed sentence whose status is not a small
    integer (or a PQTMJAMMINGSTATUS message version other than 1) counts as jamming
    too: fail closed. The flag holds JAMMING_HOLD_MS after the last such report and a
    backwards clock keeps it active. Sentences with a bad checksum are never a verdict.
    Positions never pass through here; only the status number is kept.
    """
    def __init__(self):
        self._buffer = bytearray()
        self._discard = False
        self.reports = 0
        self.status_value = self.source = self.error = None
        self.flag_ms = self.report_ms = None

    def feed(self, data, now_ms):
        """Streaming bytes (any chunking); complete sentences go to line()."""
        for byte in bytes(data):
            if byte == 10:
                if self._buffer and not self._discard:
                    self.line(bytes(self._buffer).rstrip(b"\r"), now_ms)
                self._buffer.clear()
                self._discard = False
            elif byte == 36:
                self._buffer = bytearray(b"$")
                self._discard = False
            elif not self._discard:
                if len(self._buffer) >= MAX_SENTENCE:
                    self._buffer.clear()
                    self._discard = True
                else:
                    self._buffer.append(byte)

    def line(self, line, now_ms):
        parsed = parse(line)
        if parsed is None:
            return False
        name, fields = parsed
        if name == "PAIRSPF":
            value = fields[0] if fields else None
        elif name == "PQTMJAMMINGSTATUS":
            value = fields[1] if len(fields) >= 2 and fields[0] == "1" else None
        else:
            return False
        self.reports += 1
        self.source, self.report_ms = name, now_ms
        if value is not None and value.isdigit() and len(value) <= 2:
            self.status_value, self.error = int(value), None
            flagged = self.status_value >= 2
        else:
            self.status_value, self.error, flagged = None, "JAMMING_STATUS_MALFORMED", True
        if flagged:
            self.flag_ms = now_ms
        return True

    def active(self, now_ms):
        # A backwards clock cannot age a report out: still active.
        return self.flag_ms is not None and (now_ms < self.flag_ms or now_ms - self.flag_ms < JAMMING_HOLD_MS)

    def status(self, now_ms):
        return {"active": self.active(now_ms), "status": self.status_value, "source": self.source,
                "error": self.error, "reports": self.reports,
                "age_ms": None if self.report_ms is None else max(0, now_ms - self.report_ms)}
