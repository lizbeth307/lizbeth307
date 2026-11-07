#!/usr/bin/env python3
"""Runtime check of the ais-catcher +lab package (check_repo.py runtime-check; CI model, no RF).

Runs as uid 1000 in a fresh offline chroot from the pinned snapshot with the package installed.
1. `AIS-catcher -L`: the build configuration is exactly the recipe's (SDR support RTLSDR, AIRSPYHF+
   and the always-built network inputs RTLTCP and SPYSERVER; other support only ZLIB, SYSLOG and
   RTLSDR-TUNERBW; no SSL, SOXR, libsamplerate, SQLite, PostgreSQL, NMEA2000, ZMQ, bias-tee).
2. Synthetic AIVDM sentences written here (types 1, 5, 18, 19, 24A, 24B; ship types 70, 30, 37
   and 35; no recorded traffic) are replayed with `-r TXT <file>` three ways: JSON on stdout
   (`-o 5`), JSON through a FIFO exactly as the lease unit runs it (`-o 0 -f <fifo> MSGFORMAT
   JSON_FULL`, nothing on stdout), and with the options from an @response file as
   srrx.ais_filter prepare writes it. Every message must come back with the JSON_FULL keys
   srrx.ais_filter reads (FIELDS) and the values encoded; stderr must not name an MMSI.
Last stdout line: {"ok": true, "findings": [], ...} (the hook contract of build_recipe.run_hook).
"""
import json
import os
import subprocess
import sys
import tempfile
import threading

BINARY = "/usr/bin/AIS-catcher"
# srrx.ais_filter.FIELDS (software/tests/test_ais_filter.py checks that both lists agree).
FIELDS = ("class", "type", "mmsi", "shiptype", "partno", "lat", "lon", "speed", "course", "heading", "status",
          "shipname", "callsign")
SDR_SUPPORT = {"RTLSDR", "AIRSPYHF+", "RTLTCP", "SPYSERVER"}
OTHER_REQUIRED, OTHER_ALLOWED = {"ZLIB"}, {"ZLIB", "SYSLOG", "RTLSDR-TUNERBW"}
TIMEOUT_S = 60


def bits(value, width):
    return format(value & ((1 << width) - 1), "0%db" % width)


def text6(value, chars):
    out = ""
    for ch in value.upper().ljust(chars, "@")[:chars]:
        code = ord(ch)
        out += bits(code - 64 if 64 <= code < 96 else code, 6)  # ITU-R M.1371 6-bit ASCII
    return out


def sentences(payload_bits, sequence):
    """!AIVDM sentences of one message: 6-bit armour, at most 60 characters per fragment."""
    fill = (-len(payload_bits)) % 6
    payload_bits += "0" * fill
    armoured = "".join(chr(v + 48 if v < 40 else v + 56) for v in
                       (int(payload_bits[i:i + 6], 2) for i in range(0, len(payload_bits), 6)))
    parts = [armoured[i:i + 60] for i in range(0, len(armoured), 60)]
    out = []
    for index, part in enumerate(parts):
        body = "AIVDM,%d,%d,%s,A,%s,%d" % (len(parts), index + 1, str(sequence) if len(parts) > 1 else "", part,
                                           fill if index == len(parts) - 1 else 0)
        checksum = 0
        for ch in body:
            checksum ^= ord(ch)
        out.append("!%s*%02X" % (body, checksum))
    return out


def position(kind, mmsi, lat, lon, speed, course, heading):
    head = bits(kind, 6) + bits(0, 2) + bits(mmsi, 30)
    fix = bits(round(lon * 600000), 28) + bits(round(lat * 600000), 27)
    if kind == 1:
        return (head + bits(0, 4) + bits(-128, 8) + bits(round(speed * 10), 10) + bits(0, 1) + fix
                + bits(round(course * 10), 12) + bits(heading, 9) + bits(10, 6) + bits(0, 2) + bits(0, 3) + bits(0, 1) + bits(0, 19))
    return (head + bits(0, 8) + bits(round(speed * 10), 10) + bits(0, 1) + fix + bits(round(course * 10), 12)
            + bits(heading, 9) + bits(10, 6) + bits(0, 2) + bits(1, 1) + "0" * 6 + bits(0, 20))  # type 18


def static5(mmsi, callsign, name, shiptype):
    return (bits(5, 6) + bits(0, 2) + bits(mmsi, 30) + bits(0, 2) + bits(0, 30) + text6(callsign, 7) + text6(name, 20)
            + bits(shiptype, 8) + bits(10, 9) + bits(20, 9) + bits(3, 6) + bits(3, 6) + bits(1, 4) + bits(0, 4) + bits(0, 5)
            + bits(24, 5) + bits(60, 6) + bits(0, 8) + text6("", 20) + bits(1, 1) + bits(0, 1))


def static19(mmsi, lat, lon, name, shiptype):
    return (bits(19, 6) + bits(0, 2) + bits(mmsi, 30) + bits(0, 8) + bits(50, 10) + bits(0, 1)
            + bits(round(lon * 600000), 28) + bits(round(lat * 600000), 27) + bits(900, 12) + bits(90, 9) + bits(10, 6)
            + bits(0, 4) + text6(name, 20) + bits(shiptype, 8) + bits(5, 9) + bits(5, 9) + bits(2, 6) + bits(2, 6)
            + bits(1, 4) + bits(0, 1) + bits(1, 1) + bits(0, 1) + bits(0, 4))


def static24(mmsi, part, name="", shiptype=0, callsign=""):
    head = bits(24, 6) + bits(0, 2) + bits(mmsi, 30) + bits(part, 2)
    if part == 0:
        return head + text6(name, 20)
    return (head + bits(shiptype, 8) + text6("SRX", 3) + bits(1, 4) + bits(1, 20) + text6(callsign, 7)
            + bits(4, 9) + bits(4, 9) + bits(1, 6) + bits(1, 6) + bits(0, 6))


# (bits, expected JSON_FULL values). MMSIs 2xx with an unallocated MID-like prefix: synthetic only.
MESSAGES = (
    (position(1, 244000101, 52.5, 4.25, 12.3, 181.5, 180), {"type": 1, "mmsi": 244000101, "lat": 52.5, "lon": 4.25,
                                                             "speed": 12.3, "course": 181.5, "heading": 180, "status": 0}),
    (static5(244000101, "SRRX1", "SRRX TEST CARGO", 70), {"type": 5, "mmsi": 244000101, "shiptype": 70,
                                                          "shipname": "SRRX TEST CARGO", "callsign": "SRRX1"}),
    (static5(244000202, "SRRX2", "SRRX TEST MIL", 35), {"type": 5, "mmsi": 244000202, "shiptype": 35}),
    (position(18, 244000303, -33.75, -70.5, 4.0, 10.0, 11), {"type": 18, "mmsi": 244000303, "lat": -33.75, "lon": -70.5,
                                                              "speed": 4.0, "course": 10.0, "heading": 11}),
    (static24(244000303, 0, name="SRRX TEST SAIL"), {"type": 24, "mmsi": 244000303, "partno": 0, "shipname": "SRRX TEST SAIL"}),
    (static24(244000303, 1, shiptype=37, callsign="SRRX3"), {"type": 24, "mmsi": 244000303, "partno": 1, "shiptype": 37,
                                                            "callsign": "SRRX3"}),
    (static19(244000404, 60.125, 24.875, "SRRX TEST FISH", 30), {"type": 19, "mmsi": 244000404, "shiptype": 30,
                                                                 "shipname": "SRRX TEST FISH", "lat": 60.125, "lon": 24.875}),
)


def nmea_text():
    lines = []
    for sequence, (payload, _) in enumerate(MESSAGES):
        lines += sentences(payload, sequence % 10)
    return "".join(line + "\n" for line in lines)


def run(argv, timeout=TIMEOUT_S):
    """One bounded AIS-catcher run; a timeout comes back as exit code None with empty output."""
    try:
        return subprocess.run([BINARY] + argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess([BINARY] + argv, None, "", "")


def json_lines(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if type(value) is dict and value.get("class") == "AIS":
                out.append(value)
    return out


def compare(label, records, findings):
    for _, expected in MESSAGES:
        match = [r for r in records if r.get("type") == expected["type"] and r.get("mmsi") == expected["mmsi"]
                 and ("partno" not in expected or r.get("partno") == expected["partno"])]
        if len(match) != 1:
            findings.append("%s: message type %d of a synthetic MMSI came back %d times" % (label, expected["type"], len(match)))
            continue
        for key, value in expected.items():
            got = match[0].get(key)
            if type(value) is float:
                ok = type(got) in (int, float) and abs(got - value) < 1e-3
            elif type(value) is str:
                ok = type(got) is str and got.rstrip("@ ") == value
            else:
                ok = got == value
            if not ok:
                findings.append("%s: key %s of message type %d differs from the encoded value" % (label, key, expected["type"]))
    seen = {key for record in records for key in record}
    missing = [key for key in FIELDS if key not in seen]
    if missing:
        findings.append(label + ": JSON_FULL keys missing: " + ",".join(missing))


def mmsi_in(text):
    return any(str(expected["mmsi"]) in text for _, expected in MESSAGES)


def main():
    findings, report = [], {"binary": BINARY}
    if not (os.path.isfile(BINARY) and os.access(BINARY, os.X_OK)):
        print(json.dumps({"ok": False, "findings": ["AIS-catcher binary missing"]}))
        return 1
    listing = run(["-L"])
    support = {}
    for line in (listing.stdout + listing.stderr).splitlines():
        name, sep, rest = line.partition(":")
        if sep and name.strip() in ("SDR support", "Other support"):
            support[name.strip()] = set(rest.split())
    report["build_configuration"] = {k: sorted(v) for k, v in support.items()}
    if support.get("SDR support") != SDR_SUPPORT:
        findings.append("SDR support differs from the recipe: " + " ".join(sorted(support.get("SDR support", []))))
    other = support.get("Other support")
    if other is None or not OTHER_REQUIRED <= other or not other <= OTHER_ALLOWED:
        findings.append("other support differs from the recipe: " + " ".join(sorted(other or [])))
    with tempfile.TemporaryDirectory(prefix="srrx-ais-runtime-") as temporary:
        source = os.path.join(temporary, "synthetic.nmea")
        with open(source, "w", encoding="ascii", newline="\n") as stream:
            stream.write(nmea_text())
        screen = run(["-r", "TXT", source, "-o", "5"])
        records = json_lines(screen.stdout)
        report["stdout_json_records"] = len(records)
        report["stdout_json_sample"] = records[:2]
        compare("stdout -o 5", records, findings)
        if mmsi_in(screen.stderr):
            findings.append("stdout run: stderr names a synthetic MMSI")
        fifo = os.path.join(temporary, "ais.fifo")
        os.mkfifo(fifo, 0o600)
        chunks = []

        def reader():
            with open(fifo, "rb") as stream:  # blocks until AIS-catcher opens the FIFO, ends at its close
                chunks.append(stream.read())
        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        piped = run(["-r", "TXT", source, "-o", "0", "-f", fifo, "MSGFORMAT", "JSON_FULL"])
        thread.join(TIMEOUT_S)
        if thread.is_alive():
            findings.append("FIFO run: the reader did not see the end of the stream")
            os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
        records = json_lines(b"".join(chunks).decode("utf-8", "replace"))
        report["fifo_json_records"] = len(records)
        compare("FIFO -f MSGFORMAT JSON_FULL", records, findings)
        if piped.stdout.strip():
            findings.append("FIFO run: -o 0 still printed on stdout")
        if mmsi_in(piped.stderr):
            findings.append("FIFO run: stderr names a synthetic MMSI")
        response = os.path.join(temporary, "receiver.args")
        with open(response, "w", encoding="ascii", newline="\n") as stream:
            stream.write("-o\n5\n")
        expanded = run(["-r", "TXT", source, "@" + response])
        records = json_lines(expanded.stdout)
        report["response_file_json_records"] = len(records)
        compare("@response file", records, findings)
    report["exit_codes"] = {"list": listing.returncode, "stdout": screen.returncode, "fifo": piped.returncode,
                            "response_file": expanded.returncode}
    report.update(ok=not findings, findings=findings, hardware_ready=False,
                  scope="CI model: synthetic AIVDM replay through the built AIS-catcher; no SDR, no RF")
    print(json.dumps(report, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
