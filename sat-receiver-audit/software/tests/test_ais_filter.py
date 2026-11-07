"""srrx.ais_filter (W2 SW-AIS): the AIS privacy rule of STACK.md:599/:621/:2182 and its lease wiring.

Synthetic JSON records in the AIS-catcher v0.70 JSON_FULL shape (Source/JSON/JSONAIS.cpp) and
temporary directories only: no AIS-catcher, no receiver, no unit is started. The real engine's key
names are checked by deployment/recipes/ais-catcher/runtime_check.py in sr-rx-packages (CI model).
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import stat
import sys
import tempfile
import unittest
from unittest import mock

from srrx import ais_filter, engine_leases
from srrx.ais_filter import VesselFilter

PROJECT = Path(__file__).resolve().parents[2]
UNIT = PROJECT / "software/systemd/srrx-lease-aiscatcher@.service"
RUNTIME_CHECK = PROJECT / "deployment/recipes/ais-catcher/runtime_check.py"
POLICY = PROJECT / "deployment/receive-only-policy.json"


def engine_line(**fields):
    """One line as AIS-catcher -o 5 / MSGFORMAT JSON_FULL prints it (envelope keys of JSONAIS::ProcessMsg)."""
    record = {"class": "AIS", "device": "AIS-catcher", "version": 70, "driver": 1, "hardware": "AIRSPY HF+",
              "scaled": True, "channel": "A", "nmea": ["!AIVDM,1,1,,A,synthetic,0*00"], "repeat": 0}
    record.update(fields)
    return json.dumps(record)


def static5(mmsi, shiptype, name="SRRX TEST", callsign="SRRX1"):
    return engine_line(type=5, mmsi=mmsi, ais_version=0, imo=0, callsign=callsign, shipname=name, shiptype=shiptype,
                       shiptype_text="synthetic", to_bow=10)


def position1(mmsi, lat=52.5, lon=4.25, speed=12.3, course=181.5, heading=180, status=0):
    return engine_line(type=1, mmsi=mmsi, status=status, status_text="synthetic", turn=-128, speed=speed, accuracy=False,
                       lon=lon, lat=lat, course=course, heading=heading, second=10)


def feed(filt, *lines, now=0.0):
    changed = [filt.feed(ais_filter.parse_line(line), now) for line in lines]
    return changed


class FakeReader:
    """read(timeout) for ais_filter.run: chunks, then None (timeouts) until stop()."""

    def __init__(self, chunks):
        self.chunks = list(chunks)

    def __call__(self, timeout_s):
        return self.chunks.pop(0) if self.chunks else None


class RuleTests(unittest.TestCase):
    def test_no_vessel_and_no_state_before_a_static_report(self):
        filt = VesselFilter()
        self.assertEqual(feed(filt, position1(244000101), engine_line(type=18, mmsi=244000101, lat=1.0, lon=2.0),
                              engine_line(type=24, partno=0, mmsi=244000101, shipname="ONLY PART A")), [False, False, False])
        self.assertEqual((filt.vessels, filt.suppressed), ({}, {}))  # rule 1: nothing kept, positions not buffered
        self.assertEqual(feed(filt, static5(244000101, 70), now=5.0), [True])
        vessel = filt.vessels[244000101]
        self.assertEqual((vessel["shiptype"], vessel["shipname"], vessel["callsign"]), (70, "SRRX TEST", "SRRX1"))
        self.assertNotIn("lat", vessel)  # the dropped position report is not replayed
        self.assertEqual(feed(filt, position1(244000101), now=6.0), [True])
        self.assertEqual({k: filt.vessels[244000101][k] for k in ("lat", "lon", "speed", "course", "heading", "status")},
                         {"lat": 52.5, "lon": 4.25, "speed": 12.3, "course": 181.5, "heading": 180, "status": 0})

    def test_every_static_kind_publishes_a_known_civil_ship_type(self):
        filt = VesselFilter()
        feed(filt, engine_line(type=19, mmsi=244000404, shiptype=30, shipname="SRRX FISH", lat=60.125, lon=24.875,
                               speed=5.0, course=90.0, heading=90),
             engine_line(type=24, partno=1, mmsi=244000303, shiptype=37, callsign="SRRX3"),
             engine_line(type=24, partno=0, mmsi=244000303, shipname="SRRX SAIL"))
        self.assertEqual(sorted(filt.vessels), [244000303, 244000404])
        self.assertEqual((filt.vessels[244000404]["lat"], filt.vessels[244000404]["shiptype"]), (60.125, 30))
        self.assertEqual((filt.vessels[244000303]["shipname"], filt.vessels[244000303]["callsign"]), ("SRRX SAIL", "SRRX3"))

    def test_unknown_or_military_ship_type_is_never_published(self):
        filt = VesselFilter()
        for index, shiptype in enumerate((0, 35, 100, 255, -1, None, "70", 70.0, True)):
            mmsi = 244001000 + index
            feed(filt, static5(mmsi, shiptype), position1(mmsi))
            feed(filt, engine_line(type=19, mmsi=mmsi + 100, shiptype=shiptype, lat=1.0, lon=1.0))
            feed(filt, engine_line(type=24, partno=1, mmsi=mmsi + 200, shiptype=shiptype))
        self.assertEqual(filt.vessels, {})
        # Part A of type 24 carries no ship type; part numbers other than 1 are never static.
        feed(filt, engine_line(type=24, partno=0, mmsi=244002000, shiptype=70),
             engine_line(type=24, partno=2, mmsi=244002001, shiptype=70))
        self.assertEqual(filt.vessels, {})
        self.assertTrue(ais_filter.is_published_shiptype(1) and ais_filter.is_published_shiptype(99))

    def test_late_type_35_deletes_the_vessel_and_keeps_it_suppressed(self):
        for late in (static5(244000101, 35), engine_line(type=19, mmsi=244000101, shiptype=35, lat=1.0, lon=1.0),
                     engine_line(type=24, partno=1, mmsi=244000101, shiptype=35)):
            with self.subTest(late=json.loads(late)["type"]):
                filt = VesselFilter()
                feed(filt, static5(244000101, 70), position1(244000101), static5(244000202, 80))
                self.assertIn(244000101, filt.vessels)
                self.assertEqual(feed(filt, late, now=10.0), [True])
                self.assertNotIn(244000101, filt.vessels)
                self.assertIn(244000202, filt.vessels)  # another vessel stays
                # Later reports of that MMSI are dropped, also a static report with a civil type.
                self.assertEqual(feed(filt, position1(244000101), static5(244000101, 70), now=11.0), [False, False])
                self.assertNotIn(244000101, filt.vessels)
                self.assertEqual(list(filt.suppressed), [244000101])

    def test_only_vessel_messages_count(self):
        filt = VesselFilter()
        lines = [engine_line(type=kind, mmsi=244000500 + kind, shiptype=70) for kind in (4, 6, 8, 9, 11, 14, 21, 22, 23, 25, 26)]
        lines += [engine_line(type=5, shiptype=70), engine_line(type=5, mmsi=0, shiptype=70),
                  engine_line(type=5, mmsi=1_000_000_000, shiptype=70), engine_line(type="5", mmsi=244000600, shiptype=70),
                  json.dumps({"class": "GPS", "type": 5, "mmsi": 244000601, "shiptype": 70})]
        self.assertFalse(any(feed(filt, *lines)))
        self.assertEqual((filt.vessels, filt.suppressed), ({}, {}))

    def test_malformed_oversized_and_out_of_range_input_is_dropped(self):
        for line in ("", "not json", "[]", "{\"class\": \"AIS\"", b"\xff\xfe", "x" * (ais_filter.MAX_LINE + 1),
                     b"{" + b" " * ais_filter.MAX_LINE + b"}"):
            self.assertIsNone(ais_filter.parse_line(line))
        filt = VesselFilter()
        feed(filt, static5(244000101, 70), position1(244000101, lat=91.0, lon=181.0, speed=102.3, course=360.0, heading=511, status=16),
             engine_line(type=1, mmsi=244000101, lat=float("nan"), lon=1.0))
        self.assertEqual(set(filt.vessels[244000101]), {"mmsi", "shiptype", "shipname", "callsign", "last_seen"})
        feed(filt, static5(244000102, 70, name="<script>" + "A" * 40, callsign="AB\"CD;EF"))
        self.assertEqual((filt.vessels[244000102]["shipname"], filt.vessels[244000102]["callsign"]), ("scriptAAAAAAAAAAAAAA", "ABCDEF"))

    def test_bounded_memory_and_expiry(self):
        filt = VesselFilter(max_vessels=3, ttl_s=60)
        for index in range(5):
            feed(filt, static5(244000100 + index, 70), now=float(index))
        self.assertEqual(list(filt.vessels), [244000102, 244000103, 244000104])  # least recently heard evicted
        self.assertTrue(filt.expire(63.5))
        self.assertEqual(list(filt.vessels), [244000104])
        for index in range(ais_filter.MAX_SUPPRESSED + 10):
            filt.feed({"class": "AIS", "type": 5, "mmsi": 200000000 + index, "shiptype": 35}, 70.0)
        self.assertEqual(len(filt.suppressed), ais_filter.MAX_SUPPRESSED)


class OutputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="srrx-ais-filter-")
        self.addCleanup(temporary.cleanup)
        self.out = Path(temporary.name)

    def run_filter(self, chunks, polls=3):
        written, real = [], ais_filter.write_snapshot
        ticks = iter(i / 10.0 for i in range(1000))  # 0.1 s per clock read: changes wait for WRITE_INTERVAL_S
        calls = []

        def capture(directory, document):
            written.append(json.loads(json.dumps(document)))
            real(directory, document)
        stdout, stderr = io.StringIO(), io.StringIO()
        reader = FakeReader(chunks)
        stop = lambda: calls.append(1) or len(calls) > len(chunks) + polls  # noqa: E731
        with mock.patch.object(ais_filter, "write_snapshot", capture), contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            ais_filter.run(reader, "hfplus", self.out, clock=lambda: next(ticks), wall=lambda: 1_800_000_000.0, stop=stop)
        return written, stdout.getvalue() + stderr.getvalue()

    def test_snapshots_are_atomic_empty_at_start_and_a_deletion_is_written_at_once(self):
        stream = (static5(244000101, 70) + "\n" + position1(244000101) + "\n").encode()
        late = (static5(244000101, 35) + "\n").encode()
        # A line split across two reads is joined; a newline-less tail waits for the rest.
        written, logged = self.run_filter([stream[:37], stream[37:]] + [None] * 12 + [late, b"{\"class\":\"AIS\",\"type\":5"])
        self.assertEqual(logged, "")  # rule 4: nothing on stdout or stderr
        self.assertEqual(written[0]["vessels"], [])  # a new lease never shows old vessels
        published = [d for d in written if d["vessels"]]
        self.assertTrue(published)
        self.assertEqual(published[-1]["vessels"][0]["mmsi"], 244000101)
        after = written[written.index(published[-1]) + 1]
        self.assertEqual(after["vessels"], [])  # the type-35 report is written in the same step
        self.assertEqual((written[-1]["active"], written[-1]["vessels"]), (False, []))
        document = json.loads((self.out / ais_filter.OUTPUT_FILE).read_text(encoding="utf-8"))
        self.assertEqual((document["kind"], document["engine"], document["receiver"], document["vessels"]),
                         ("srrx_ais_vessels", "aiscatcher", "hfplus", []))
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), [ais_filter.OUTPUT_FILE])  # no temp file left
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE((self.out / ais_filter.OUTPUT_FILE).stat().st_mode), 0o640)

    def test_unpublished_vessels_leave_no_trace_in_the_products_file(self):
        written, logged = self.run_filter([(position1(244000999) + "\n" + static5(244000998, 35) + "\n" + static5(244000997, 0) + "\n").encode()])
        self.assertEqual(logged, "")
        text = (self.out / ais_filter.OUTPUT_FILE).read_text(encoding="utf-8")
        for mmsi in ("244000999", "244000998", "244000997"):
            self.assertNotIn(mmsi, text)
            self.assertFalse(any(mmsi in json.dumps(d) for d in written))

    def test_unwritable_products_directory_is_a_stable_code(self):
        with self.assertRaisesRegex(ais_filter.FilterError, "^AIS_FILTER_OUTPUT_UNAVAILABLE$"):
            ais_filter.write_snapshot(self.out / "missing", {"vessels": []})


class LeaseWiringTests(unittest.TestCase):
    DEVICES = {"usb": {"rtl_a": {"serial": "LABRXA"}, "rtl_b": {"serial": "LABRXB"},
                       "hfplus": {"serial": "AIRSPYHF SN:0123456789abcdef"}}}

    def test_receivers_and_products_match_the_lease_module(self):
        self.assertEqual(ais_filter.RECEIVERS, engine_leases.RECEIVERS)
        self.assertEqual(ais_filter.DEVICE_KEYS, engine_leases.DEVICE_KEYS)
        self.assertIn(ais_filter.ENGINE, engine_leases.ENGINES)
        for receiver in ais_filter.RECEIVERS:
            self.assertEqual(engine_leases.products_dir(ais_filter.ENGINE, receiver),
                             ais_filter.PRODUCTS_ROOT + "/" + ais_filter.ENGINE + "-" + receiver)

    def test_device_args_select_exactly_the_leased_receiver(self):
        self.assertEqual(ais_filter.device_args("rtla", self.DEVICES), ["-d", "LABRXA", "-s", "1536000"])
        self.assertEqual(ais_filter.device_args("rtlb", self.DEVICES), ["-d", "LABRXB", "-s", "1536000"])
        self.assertEqual(ais_filter.device_args("hfplus", self.DEVICES), ["-d", "0123456789ABCDEF", "-s", "192000"])
        bad = [("hfp", self.DEVICES), ("rtla", {}), ("rtla", {"usb": {"rtl_a": {"serial": None}}}),
               ("rtla", {"usb": {"rtl_a": {"serial": "LABRXA -X"}}}), ("rtlb", {"usb": {"rtl_b": {"serial": "00000001"}}}),
               ("hfplus", {"usb": {"hfplus": {"serial": "0123456789ABCDEF"}}}),
               ("hfplus", {"usb": {"hfplus": {"serial": "AIRSPYHF SN:0123456789ABCDEF -N 8100"}}}), ("rtla", [])]
        for receiver, devices in bad:
            with self.subTest(receiver=receiver), self.assertRaises(ais_filter.FilterError) as caught:
                ais_filter.device_args(receiver, devices)
            self.assertIn(str(caught.exception), ais_filter.ERRORS)  # a code, never the serial

    @unittest.skipUnless(hasattr(os, "mkfifo") and hasattr(os, "geteuid"), "FIFOs and owners are POSIX")
    def test_prepare_writes_the_response_file_and_the_fifo(self):
        with tempfile.TemporaryDirectory(prefix="srrx-ais-prepare-") as temporary:
            runtime, devices = Path(temporary) / "run", Path(temporary) / "devices.json"
            runtime.mkdir(mode=0o700)
            os.chmod(runtime, 0o700)
            devices.write_text(json.dumps(self.DEVICES), encoding="utf-8")
            self.assertEqual(ais_filter.main(["prepare", "--receiver", "hfplus", "--devices", str(devices), "--runtime", str(runtime)]), 0)
            self.assertEqual((runtime / ais_filter.ARGS_FILE).read_text(encoding="ascii"), "-d\n0123456789ABCDEF\n-s\n192000\n")
            self.assertEqual(stat.S_IMODE((runtime / ais_filter.ARGS_FILE).stat().st_mode), 0o600)
            info = (runtime / ais_filter.FIFO_FILE).lstat()
            self.assertTrue(stat.S_ISFIFO(info.st_mode))
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
            # A second start never reuses a file (RuntimeDirectory is new for every lease).
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(ais_filter.main(["prepare", "--receiver", "hfplus", "--devices", str(devices), "--runtime", str(runtime)]), 2)
            self.assertEqual(err.getvalue().strip(), "AIS_FILTER_RUNTIME_UNAVAILABLE")
            os.chmod(runtime, 0o755)
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(ais_filter.main(["prepare", "--receiver", "rtla", "--devices", str(devices), "--runtime", str(runtime)]), 2)
            self.assertEqual(err.getvalue().strip(), "AIS_FILTER_RUNTIME_UNAVAILABLE")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are POSIX")
    def test_fifo_opened_read_write_never_blocks_and_feeds_the_filter(self):
        with tempfile.TemporaryDirectory(prefix="srrx-ais-fifo-") as temporary:
            fifo, out = Path(temporary) / ais_filter.FIFO_FILE, Path(temporary) / "out"
            os.mkfifo(fifo, 0o600)
            out.mkdir()
            fd = os.open(fifo, os.O_RDWR)  # as serve opens it (fifo(7)): no writer needed yet
            try:
                read = ais_filter.fifo_reader(fd)
                self.assertIsNone(read(0.01))  # nothing written: a timeout, never an end of stream
                os.write(fd, (position1(244000102) + "\n" + static5(244000101, 70) + "\n").encode())
                calls = []
                ais_filter.run(read, "rtla", out, stop=lambda: calls.append(1) or len(calls) > 2)
            finally:
                os.close(fd)
            document = json.loads((out / ais_filter.OUTPUT_FILE).read_text(encoding="utf-8"))
            self.assertEqual(([v["mmsi"] for v in document["vessels"]], document["active"]), ([244000101], False))

    def test_serve_writes_only_the_receivers_products_directory_and_reads_only_a_fifo(self):
        with tempfile.TemporaryDirectory(prefix="srrx-ais-serve-") as temporary:
            plain = Path(temporary) / "plain"
            plain.write_text("x", encoding="utf-8")
            for receiver, fifo, output in (("hfplus", plain, "/data/products/aiscatcher-rtla"), ("hfp", plain, "/data/products/aiscatcher-hfp"),
                                           ("hfplus", plain, "/data/products/readsb-hfplus"), ("hfplus", plain, "/data")):
                with self.assertRaisesRegex(ais_filter.FilterError, "^AIS_FILTER_BAD_REQUEST$"):
                    ais_filter.serve(receiver, fifo, output)
            with self.assertRaisesRegex(ais_filter.FilterError, "^AIS_FILTER_INPUT_UNAVAILABLE$"):
                ais_filter.serve("hfplus", plain, Path(temporary) / "aiscatcher-hfplus", products_root=temporary)

    def test_lease_unit_starts_the_engine_only_through_the_filter(self):
        service = {}
        for line in UNIT.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not line.startswith("#"):
                service.setdefault(key, []).append(value)
        pre, start, post = (shlex.split(service[k][0]) for k in ("ExecStartPre", "ExecStart", "ExecStartPost"))
        self.assertEqual([len(service[k]) for k in ("ExecStartPre", "ExecStart", "ExecStartPost")], [1, 1, 1])
        runtime = "%t/srrx-lease-aiscatcher-%i"
        self.assertEqual(start, ["/usr/bin/env", "AIS-catcher", "@" + runtime + "/" + ais_filter.ARGS_FILE, "-o", "0",
                                 "-f", runtime + "/" + ais_filter.FIFO_FILE, "MSGFORMAT", "JSON_FULL"])
        self.assertEqual(pre, ["/usr/bin/python3", "-P", "-s", "-B", "-m", "srrx.ais_filter", "prepare", "--receiver", "%i",
                               "--devices", "/etc/srrx/devices.json", "--runtime", runtime])
        self.assertEqual(post, ["/usr/bin/python3", "-P", "-s", "-B", "-m", "srrx.ais_filter", "serve", "--receiver", "%i",
                                "--fifo", runtime + "/" + ais_filter.FIFO_FILE, "--output", "/data/products/aiscatcher-%i", "--detach"])
        self.assertIn("PYTHONPATH=/opt/srrx/software", " ".join(service["Environment"]))
        # The policy of selftest RX-12-ais names exactly these command lines.
        component = json.loads(POLICY.read_text(encoding="utf-8"))["components"]["ais-catcher"]
        self.assertEqual((component["exec_start_pre"], component["exec_start"], component["exec_start_post"]),
                         (service["ExecStartPre"], service["ExecStart"][0], service["ExecStartPost"]))
        for token in component["deny_tokens"]:
            self.assertNotIn(token, start)


class EngineContractTests(unittest.TestCase):
    """The runtime check of the recipe replays its own AIVDM sentences through the built AIS-catcher;
    here its encoder is decoded at the bit offsets the pinned v0.70 reads (Source/JSON/JSONAIS.cpp)."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("ais_runtime_check", RUNTIME_CHECK)
        cls.check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.check)

    @staticmethod
    def payload(sentences):
        bits, fill = "", 0
        for sentence in sentences:
            body, _, checksum = sentence[1:].partition("*")
            value = 0
            for ch in body:
                value ^= ord(ch)
            assert "%02X" % value == checksum, sentence
            fields = body.split(",")
            for ch in fields[5]:
                code = ord(ch) - 48
                bits += format(code - 8 if code > 40 else code, "06b")
            fill = int(fields[6])
        return bits[:len(bits) - fill]

    @staticmethod
    def uint(bits, start, length):
        return int(bits[start:start + length], 2)

    def sint(self, bits, start, length):
        value = self.uint(bits, start, length)
        return value - (1 << length) if value >> (length - 1) else value

    @staticmethod
    def text(bits, start, length):
        out = ""
        for i in range(start, start + length, 6):
            code = int(bits[i:i + 6], 2)
            out += chr(code + 64 if code < 32 else code)
        return out.rstrip("@ ")

    def test_fields_agree_with_the_filter(self):
        self.assertEqual(self.check.FIELDS, ais_filter.FIELDS)
        self.assertEqual(self.check.BINARY, "/usr/bin/AIS-catcher")

    def test_synthetic_sentences_carry_the_values_at_the_engine_offsets(self):
        minimum = {1: 149, 5: 418, 18: 168, 19: 312, 24: 160}  # Source/Marine/Message.cpp:401 (validate)
        offsets = {"shiptype": {5: 232, 19: 263, 24: 40}, "shipname": {5: 112, 19: 143, 24: 40}, "callsign": {5: 70, 24: 90},
                   "lon": {1: 61, 18: 57, 19: 57}, "lat": {1: 89, 18: 85, 19: 85}, "speed": {1: 50, 18: 46},
                   "course": {1: 116, 18: 112}, "heading": {1: 128, 18: 124}, "status": {1: 38}}
        for sequence, (payload_bits, expected) in enumerate(self.check.MESSAGES):
            with self.subTest(type=expected["type"], mmsi=expected["mmsi"]):
                bits = self.payload(self.check.sentences(payload_bits, sequence))
                kind = expected["type"]
                self.assertEqual((self.uint(bits, 0, 6), self.uint(bits, 8, 30)), (kind, expected["mmsi"]))
                self.assertGreaterEqual(len(bits), minimum[kind])
                if kind == 24:
                    self.assertEqual(self.uint(bits, 38, 2), expected["partno"])
                for key, value in expected.items():
                    where = offsets.get(key, {}).get(kind)
                    if where is None or (kind == 24 and key == "shiptype" and expected["partno"] == 0):
                        continue
                    if key in ("lat", "lon"):
                        got = self.sint(bits, where, 27 if key == "lat" else 28) / 600000.0
                    elif key in ("speed", "course"):
                        got = self.uint(bits, where, 10 if key == "speed" else 12) / 10.0
                    elif key in ("shipname", "callsign"):
                        got = self.text(bits, where, 120 if key == "shipname" else 42)
                    else:
                        got = self.uint(bits, where, {"shiptype": 8, "heading": 9, "status": 4}[key])
                    self.assertAlmostEqual(got, value, places=4) if type(value) is float else self.assertEqual(got, value)

    def test_the_synthetic_traffic_through_the_filter(self):
        """The decoded values of the runtime-check messages, as JSON_FULL records, through the rule."""
        filt = VesselFilter()
        for _, expected in self.check.MESSAGES:
            filt.feed(dict(expected, **{"class": "AIS"}), 1.0)
        self.assertEqual(sorted(filt.vessels), [244000101, 244000303, 244000404])  # 244000202 is type 35
        self.assertNotIn("lat", filt.vessels[244000101])  # its position came before the static report
        # Its part A (name) came before part B (the ship type), so only part B's call sign is kept.
        self.assertEqual((filt.vessels[244000303].get("shipname"), filt.vessels[244000303]["callsign"]), (None, "SRRX3"))


if __name__ == "__main__":
    unittest.main()
