"""Harness regressions: lab host/guest trust boundaries and fixture contracts."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
BOOTSTRAP = HERE / "guest_bootstrap.sh"
QNN_SKIP = "Actual QNN HTP SDK library unavailable; no real manifest was generated"
LINUX = sys.platform == "linux"
IMAGE = "ubuntu-24.04-server-cloudimg-arm64.img"


def load(name):
    spec = importlib.util.spec_from_file_location("srrx_lab_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve string annotations here.
    spec.loader.exec_module(module)
    return module


host, rx, tools, kit = load("host"), load("rx_worker_smoke"), load("fetch_tools"), load("build_kit")


def bootstrap_block(marker):
    text = BOOTSTRAP.read_text()
    start = text.index("<<'PY'\n", text.index(marker)) + len("<<'PY'\n")
    return text[start:text.index("\nPY\n", start) + 1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


class HostBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_signed_sums_must_list_every_locked_asset(self):
        expected = {IMAGE: {"sha256": "a" * 64},
                    "ubuntu-24.04-server-cloudimg-arm64-vmlinuz-generic": {"sha256": "b" * 64},
                    "ubuntu-24.04-server-cloudimg-arm64-initrd-generic": {"sha256": "c" * 64}}
        def write(image="a" * 64, kernel="b" * 64):
            for folder, lines in (("ubuntu", ["%s *%s" % (image, IMAGE), "d" * 64 + " *other.img"]),
                                  ("unpacked", ["%s *ubuntu-24.04-server-cloudimg-arm64-vmlinuz-generic" % kernel,
                                                "c" * 64 + " *ubuntu-24.04-server-cloudimg-arm64-initrd-generic"])):
                (self.root / folder).mkdir(exist_ok=True)
                (self.root / folder / "SHA256SUMS").write_text("\n".join(lines) + "\n")
        write()
        host.check_signed_assets(self.root, expected)
        for changes in ({"image": "e" * 64}, {"kernel": "f" * 64}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "absent from signed"):
                write(**changes)
                host.check_signed_assets(self.root, expected)

    def test_payload_pins_come_only_from_the_project_lock(self):
        for name in ("wheelhouse-requirements.txt", "wheelhouse-manifest.json"):
            shutil.copyfile(HERE / name, self.root / name)
        locks = host.dependency_locks(self.root)
        self.assertEqual(locks["wheelhouse-requirements.txt"], (HERE / "wheelhouse-requirements.txt").read_bytes())
        with (self.root / "wheelhouse-requirements.txt").open("a") as stale:
            stale.write("evil==1.0 --hash=sha256:" + "0" * 64 + "\n")
        with self.assertRaisesRegex(ValueError, "differs from the project lock"):
            host.dependency_locks(self.root)

    def test_project_archive_never_carries_the_host_owner_into_the_guest(self):
        source = self.root / "file.py"
        source.write_text("x = 1\n")
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            archive.add(source, arcname="software/file.py", recursive=False, filter=host.root_owned)
        buffer.seek(0)
        with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
            member = archive.getmember("software/file.py")
        self.assertEqual((member.uid, member.gid, member.uname, member.gname), (0, 0, "root", "root"))

    def test_guest_symlinks_and_special_files_are_refused_before_host_reads(self):
        (self.root / "module-lab").mkdir()
        (self.root / "summary.json").write_text("{}\n")
        (self.root / "module-lab" / "report.json").write_text("{}\n")
        host.check_results(self.root)
        try:
            os.symlink(Path.home(), self.root / "module-lab" / "leak.txt")
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(ValueError, "symlink or special file: module-lab/leak.txt"):
            host.check_results(self.root)
        os.unlink(self.root / "module-lab" / "leak.txt")
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.root / "pipe.log")
            with self.assertRaisesRegex(ValueError, "pipe.log"):
                host.check_results(self.root)

    @unittest.skipUnless(os.name == "posix" and Path("/bin/sh").exists(), "POSIX shell fake qemu-img required")
    def test_base_overlay_requires_written_summary_exit0_and_locked_chain(self):
        run, image = self.root / "previous", self.root / IMAGE
        run.mkdir()
        base = run / "guest.qcow2"
        base.write_bytes(b"overlay")
        image.write_bytes(b"locked image")
        fake = self.root / "qemu-img"
        fake.write_text('#!/bin/sh\ntest "$1" = check && exit 0\ncat "$(dirname "$0")/chain.json"\n')
        fake.chmod(0o755)
        (self.root / "chain.json").write_text(json.dumps([{"filename": str(base), "format": "qcow2"},
                                                         {"filename": str(image), "format": "qcow2"}]))
        good = {"status": "FAIL", "environment": {"architecture": "aarch64"}, "physical_tests_performed": False,
                "host": {"qemu_exit_code": 0}}
        (run / "report.json").write_text(json.dumps(good))
        record = host.overlay_record(fake, base.resolve(), sha(b"locked image"))
        self.assertEqual([x["sha256"] for x in record["backing_chain"]], [sha(b"overlay"), sha(b"locked image")])
        self.assertEqual((record["previous_qemu_exit_code"], record["sha256"]), (0, sha(b"overlay")))
        self.assertNotIn("previous_clean_shutdown", record)
        with self.assertRaisesRegex(ValueError, "end at the locked Ubuntu image"):
            host.overlay_record(fake, base.resolve(), sha(b"other image"))
        for change in ({"status": "ABORTED"}, {"status": None}, {"host": {"qemu_exit_code": 1}},
                       {"host": {"qemu_exit_code": False}}, {"host": {}}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "exited QEMU with code 0"):
                (run / "report.json").write_text(json.dumps({**good, **change}))
                host.overlay_record(fake, base.resolve(), sha(b"locked image"))


@unittest.skipUnless(LINUX and Path("/proc/1/comm").exists() and Path("/etc/os-release").exists(),
                     "guest summary block reads Linux /proc and os-release")
class BootstrapSummaryTests(unittest.TestCase):
    def summary(self, code=0, skipped=({"test": "qnn", "reason": QNN_SKIP},), dependency=True):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            (results / "module-lab").mkdir()
            reports = {name: {"status": "PASS"} for name in ("system-smoke.json", "pty-smoke.json", "xcb-smoke.json",
                                                             "rx-worker-smoke.json", "storage-smoke.json")}
            reports["gui-smoke.json"] = {"status": "PASS_LINUX_OFFSCREEN_SIMULATION"}
            reports["module-lab/report.json"] = {"status": "EMULATION_PASS_WITH_GAPS"}
            reports["software-tests.json"] = {"host_regression_status": "PASS", "failures": [], "errors": [],
                                              "skipped": list(skipped)}
            if dependency:
                reports["dependency-verification.json"] = {"status": "PASS"}
            for name, value in reports.items():
                (results / name).write_text(json.dumps(value))
            subprocess.run([sys.executable, "-I", "-B", "-", str(results), str(code)], check=True, capture_output=True,
                           input=bootstrap_block('python3 - "$results" "$code"'), text=True, timeout=60)
            return json.loads((results / "summary.json").read_text())

    def test_only_documented_guest_gaps_may_skip(self):
        self.assertEqual(self.summary()["status"], "PASS")
        self.assertEqual(self.summary(skipped=())["status"], "PASS")
        pdf = {"test": "pdf", "reason": "PyMuPDF is not installed in this environment"}
        self.assertEqual(self.summary(skipped=[pdf, {"test": "qnn", "reason": QNN_SKIP}])["status"], "PASS")
        for skipped in ([{"test": "spectrum", "reason": "Optional NumPy dependency is not installed"}],
                        [{"test": "hmi", "reason": "optional PySide6 is not installed"}],
                        [{"test": "qnn", "reason": QNN_SKIP}] * 2, [pdf, pdf], ["not a record"]):
            with self.subTest(skipped=skipped):
                report = self.summary(skipped=skipped)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(report["suites"]["software-tests.json"], "PASS_WITH_UNEXPECTED_SKIPS")

    def test_missing_dependency_verification_or_failed_bootstrap_fails(self):
        report = self.summary(dependency=False)
        self.assertEqual((report["status"], report["suites"]["dependency-verification.json"]), ("FAIL", "MISSING_OR_INVALID"))
        self.assertEqual(self.summary(code=1)["status"], "FAIL")


@unittest.skipUnless(LINUX and Path("/bin/sh").exists(), "dependency block uses Linux dpkg-query semantics")
class DependencyVerificationTests(unittest.TestCase):
    """Cached-overlay runs must prove installed versions equal both locks."""
    def run_block(self, rows, requirements=None, payload_requirements=None):
        listed = subprocess.run([sys.executable, "-I", "-c", "from importlib.metadata import distributions as d\n"
                                 "for x in d(): print(x.metadata['Name'] + '==' + x.version)"],
                                capture_output=True, text=True, check=True).stdout
        if requirements is None:
            requirements = "".join(line + " --hash=sha256:" + "0" * 64 + "\n" for line in listed.splitlines())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ("lock", "payload", "bin"):
                (root / folder).mkdir()
            (root / "lock/wheelhouse-requirements.txt").write_text(requirements)
            (root / "payload/wheelhouse-requirements.txt").write_text(payload_requirements or requirements)
            (root / "lock/guest-packages.lock.json").write_text(json.dumps({"packages": [
                {"package": "libsrrx1", "architecture": "arm64", "version": "1:2.0-1"},
                {"package": "srrx-data", "architecture": "all", "version": "3"}]}))
            (root / "rows.txt").write_text(rows)
            fake = root / "bin/dpkg-query"
            fake.write_text('#!/bin/sh\ncat "$SRRX_FAKE_ROWS"\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(root / "bin") + os.pathsep + os.environ.get("PATH", ""),
                       SRRX_FAKE_ROWS=str(root / "rows.txt"))
            result = subprocess.run([sys.executable, "-I", "-B", "-", str(root / "lock"), str(root / "payload"),
                                     str(root / "out.json")], input=bootstrap_block("/opt/srrx/venv/bin/python3 -I -B -"),
                                    capture_output=True, text=True, env=env, timeout=60)
            out = json.loads((root / "out.json").read_text()) if (root / "out.json").exists() else None
            return result, out, requirements

    def test_exact_reinstalled_versions_pass_and_any_drift_fails(self):
        good = "libsrrx1\tarm64\t1:2.0-1\tii \nsrrx-data\tall\t3\tii \nother\tarm64\t1\tii \n"
        result, out, requirements = self.run_block(good)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((out["status"], out["debs"], out["cached_dependency_state_trusted"]), ("PASS", 2, False))
        for rows in (good.replace("1:2.0-1", "1:1.9-1"), good.replace("srrx-data\tall\t3\tii ", "srrx-data\tall\t3\tiU "),
                     good.replace("srrx-data\tall", "srrx-data\tarm64"), "libsrrx1\tarm64\t1:2.0-1\tii \n"):
            with self.subTest(rows=rows):
                result, out, _ = self.run_block(rows)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Installed guest packages differ from the lock", result.stderr)
                self.assertIsNone(out)
        result, out, _ = self.run_block(good, requirements="".join(requirements.splitlines(True)[1:]))
        self.assertIn("Venv distributions differ from the wheel lock", result.stderr)
        result, out, _ = self.run_block(good, payload_requirements=requirements + "x==1\n")
        self.assertIn("Payload wheel lock differs", result.stderr)
        self.assertIsNone(out)


class RxWorkerContractTests(unittest.TestCase):
    def test_only_clean_boundary_errors_pass_failure_fixtures(self):
        off = list(rx.BRANCH_OFF)
        for name, error in (("driver_error", OSError("RX worker failed")), ("crash_sigsegv", OSError("RX worker exited")),
                            ("invalid_odd_short_read", OSError("Invalid worker complex64 block")),
                            ("hang_ignoring_sigterm", TimeoutError("No fresh RX block within one second"))):
            with self.subTest(name=name):
                self.assertEqual(rx.failure_issues(name, error, off), [])
        for error in (TypeError("x"), KeyError("x"), AttributeError("x")):
            with self.subTest(error=error):
                self.assertIn("Unclean public error type escaped run_capture: " + type(error).__name__,
                              rx.failure_issues("crash_sigsegv", error, off))
        self.assertIn("Raw pipe EOF escaped the production clean-error boundary", rx.failure_issues("crash_sigsegv", EOFError(), off))
        for error in (None, AssertionError("unexpected spectrum")):
            self.assertIn("Expected bounded worker failure was not observed", rx.failure_issues("driver_error", error, off))
        self.assertTrue(rx.failure_issues("hang_ignoring_sigterm", OSError("RX worker exited"), off))
        self.assertIn("Capture cleanup did not request exactly branch OFF", rx.failure_issues("driver_error", OSError(), []))


class ToolRuntimeTests(unittest.TestCase):
    def test_wrappers_do_not_consult_the_host_loader_cache(self):
        texts = tools.wrapper_texts()
        self.assertEqual(set(texts), {"qemu-system-aarch64", "qemu-img", "genisoimage"})
        for text in texts.values():
            self.assertIn('ld-linux-x86-64.so.2" --inhibit-cache --library-path', text)
            self.assertIn('tools_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)', text)

    def test_any_library_resolved_outside_the_locked_root_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            listing = ("\tlinux-vdso.so.1 (0x00007ffd1)\n"
                       "\tlibz.so.1 => %s (0x00007f01)\n"
                       "\tlibpixman-1.so.0 => /usr/lib/x86_64-linux-gnu/libpixman-1.so.0 (0x00007f02)\n"
                       "\tlibmissing.so.2 => not found\n"
                       "\t/lib64/ld-linux-x86-64.so.2 => /lib64/ld-linux-x86-64.so.2 (0x00007f03)\n"
                       % (root / "usr/lib/x86_64-linux-gnu/libz.so.1"))
            self.assertEqual(tools.host_library_leaks(listing, root),
                             ["libpixman-1.so.0 => /usr/lib/x86_64-linux-gnu/libpixman-1.so.0", "libmissing.so.2 => not found"])

    @unittest.skipUnless(LINUX and shutil.which("dpkg-deb") and shutil.which("tar"), "dpkg-deb and GNU tar required")
    def test_kit_runtime_must_equal_a_fresh_unpack_of_the_locked_debs(self):
        with tempfile.TemporaryDirectory() as temporary:
            work, packages = Path(temporary), []
            out = work / "tools"
            for part in ("debs", "root", "bin"):
                (out / part).mkdir(parents=True)
            for name in ("srrx-tool", "srrx-lib"):
                package = work / name
                (package / "DEBIAN").mkdir(parents=True)
                (package / "DEBIAN").chmod(0o755)  # dpkg-deb rejects 0700 control directories.
                (package / "DEBIAN/control").write_text("Package: %s\nVersion: 1.0\nArchitecture: all\n"
                                                        "Maintainer: lab <lab@example.invalid>\nDescription: fixture\n" % name)
                if name == "srrx-tool":
                    (package / "usr/bin").mkdir(parents=True)
                    (package / "usr/bin/tool").write_text("#!/bin/sh\nexit 0\n")
                    (package / "usr/bin/tool").chmod(0o755)
                else:
                    (package / "usr/lib/x86_64-linux-gnu").mkdir(parents=True)
                    (package / "usr/lib/x86_64-linux-gnu/libx.so.1").write_bytes(b"\x7fELF fixture")
                    os.symlink("libx.so.1", package / "usr/lib/x86_64-linux-gnu/libx.so")
                deb = out / "debs" / (name + "_1.0_all.deb")
                subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(package), str(deb)],
                               check=True, capture_output=True)
                packages.append({"name": name, "filename": deb.name, "bytes": deb.stat().st_size, "sha256": sha(deb.read_bytes())})
            tools.unpack(out / "debs", packages, out / "root")
            tools.wrappers(out)
            tree = kit.check_runtime(out, packages)
            self.assertEqual(tree["usr/bin/tool"][0::3], ("file", True))
            self.assertEqual(tree["usr/lib/x86_64-linux-gnu/libx.so"], ("symlink", "libx.so.1"))
            library = out / "root/usr/lib/x86_64-linux-gnu/libx.so.1"
            for mutate, undo in ((lambda: library.write_bytes(b"\x7fELF swapped"), lambda: library.write_bytes(b"\x7fELF fixture")),
                                 (lambda: (out / "root/usr/bin/extra").write_text("x"), lambda: (out / "root/usr/bin/extra").unlink()),
                                 (lambda: (out / "root/usr/bin/tool").chmod(0o644), lambda: (out / "root/usr/bin/tool").chmod(0o755))):
                mutate()
                with self.assertRaisesRegex(ValueError, "tools/root differs from the locked host debs"):
                    kit.check_runtime(out, packages)
                undo()
            kit.check_runtime(out, packages)
            wrapper = out / "bin/qemu-img"
            wrapper.write_text(wrapper.read_text().replace(" --inhibit-cache", ""))
            with self.assertRaisesRegex(ValueError, "tools/bin differs"):
                kit.check_runtime(out, packages)
            tools.wrappers(out)
            with self.assertRaisesRegex(ValueError, "Locked file mismatch"):
                kit.check_runtime(out, [dict(packages[0], sha256="0" * 64), packages[1]])


@unittest.skipUnless(LINUX, "pty_smoke imports Linux pty/termios")
class PtyFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pty = load("pty_smoke")

    def test_hup_case_records_only_an_accepted_trip_cause(self):
        for cause, path in (("OSError: [Errno 5] Input/output error", "transport_error"),
                            ("BrokenPipeError: [Errno 32] Broken pipe", "transport_error"),
                            ("pico_status_timeout", "status_deadline"), ("host_policy_fault", None),
                            ("daemon_exit", None), ("RuntimeError: No fresh Pico session", None), (None, None)):
            with self.subTest(cause=cause):
                self.assertEqual(self.pty.hup_trip_path(cause), path)

    def test_peer_uses_the_shipped_firmware_status_and_hello_cadence(self):
        left, right = socket.socketpair()
        try:
            left.setblocking(False)
            peer = self.pty.Peer(types.SimpleNamespace(master=left.fileno()))
            frames, last = [], None
            for stamp in range(0, 5000, 10):
                peer.tick(stamp)
                if peer.last_frame is not last:
                    last = peer.last_frame
                    frames.append((stamp, last["t"], last["q"]))
        finally:
            left.close()
            right.close()
        self.assertEqual(peer.model.state, "SAFE")
        self.assertEqual([stamp for stamp, kind, _ in frames if kind == "HELLO"], [0, 1000, 2000, 3000, 4000])
        status = [stamp for stamp, kind, _ in frames if kind == "STATUS"]
        self.assertEqual(status[0], 10)  # State change after HELLO, as in main.py.
        gaps = [b - a for a, b in zip(status, status[1:])]
        self.assertTrue(gaps and all(200 <= gap <= 210 for gap in gaps), gaps)
        self.assertEqual([q for _, _, q in frames], list(range(len(frames))))


if __name__ == "__main__":
    unittest.main()
