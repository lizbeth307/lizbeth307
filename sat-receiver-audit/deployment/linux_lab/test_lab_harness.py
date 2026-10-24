"""Harness regressions: lab host/guest trust boundaries and fixture contracts."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from unittest import mock

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

    def test_unlistable_guest_directory_is_refused_not_skipped(self):
        (self.root / "module-lab").mkdir()
        (self.root / "summary.json").write_text("{}\n")
        real = os.scandir
        # debugfs re-applies guest modes (0311: traversable, not listable); injected so root also runs it.
        for blocked in (self.root / "module-lab", self.root):
            def scandir(path, blocked=blocked):
                if Path(path) == blocked:
                    raise PermissionError(13, "Permission denied", str(path))
                return real(path)
            with self.subTest(blocked=blocked.name), mock.patch.object(os, "scandir", scandir):
                with self.assertRaisesRegex(ValueError, "Unreadable guest results"):
                    host.check_results(self.root)
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


def satisfies(version, clauses):
    """Numeric PEP 440 subset used by software/pyproject.toml extras (>=, <=, ==, <, >)."""
    key = lambda text: tuple(int(x) for x in text.split("."))
    for clause in filter(None, (c.strip() for c in clauses.split(","))):
        op, bound = re.fullmatch(r"(>=|<=|==|<|>)\s*([0-9]+(?:\.[0-9]+)*)", clause).groups()
        a, b = key(version), key(bound)
        a, b = a + (0,) * (len(b) - len(a)), b + (0,) * (len(a) - len(b))
        if not {">=": a >= b, "<=": a <= b, "==": a == b, "<": a < b, ">": a > b}[op]:
            return False
    return True


class ProjectExtrasTests(unittest.TestCase):
    def test_guest_project_extras_are_defined_and_fully_locked(self):
        import tomllib
        line = next(l for l in BOOTSTRAP.read_text().splitlines() if "'/opt/srrx/software[" in l)
        extras = re.search(r"'/opt/srrx/software\[([a-z,]+)\]'", line).group(1).split(",")
        project = tomllib.loads((HERE.parents[1] / "software/pyproject.toml").read_text(encoding="utf-8"))["project"]
        optional = project["optional-dependencies"]
        self.assertIn("orbits", extras)  # srrx.passes (Skyfield/sgp4) is installed like the other extras
        self.assertLessEqual(set(extras), set(optional))
        manifest = json.loads((HERE / "wheelhouse-manifest.json").read_text())
        self.assertEqual(manifest["dependency_closure"]["extras"], extras)
        norm = lambda n: re.sub(r"[-_.]+", "-", n).lower()
        locked = {norm(w["name"]): w["version"] for w in manifest["wheels"]}
        closure = {(r["owner"], r["requirement"]): r["resolved_version"] for r in manifest["dependency_closure"]["requirements"]}
        for extra in extras:
            for requirement in optional[extra]:
                name = re.match(r"[A-Za-z0-9_.-]+", requirement).group(0)
                with self.subTest(extra=extra, requirement=requirement):
                    self.assertIn(norm(name), locked)  # --no-deps install: pip check needs every extra wheel locked
                    self.assertTrue(satisfies(locked[norm(name)], requirement[len(name):]), (requirement, locked[norm(name)]))
                    self.assertEqual(closure[(project["name"] + "[" + extra + "]", requirement)], locked[norm(name)])
        self.assertTrue(satisfies("2.3.5", ">=1.26,<3") and not satisfies("3.0", ">=1.26,<3") and not satisfies("1.25.9", ">=1.26"))


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

    def test_wrapper_loader_audit_is_opt_in_and_set_only_for_the_locked_loader(self):
        for text in tools.wrapper_texts().values():
            lines = text.splitlines()
            audit = [i for i, line in enumerate(lines) if "SRRX_LOADER_AUDIT" in line]
            root = next(i for i, line in enumerate(lines) if line.startswith("tools_root="))
            run = next(i for i, line in enumerate(lines) if line.startswith("exec "))
            self.assertEqual(len(audit), 1)
            self.assertTrue(root < audit[0] < run)  # after the host sh/dirname/subshell, before the locked ld.so
            self.assertEqual(lines[audit[0]], 'if [ -n "${SRRX_LOADER_AUDIT:-}" ]; then export LD_DEBUG=files,libs '
                                              'LD_DEBUG_OUTPUT="$SRRX_LOADER_AUDIT"; fi')
            self.assertEqual(sum("LD_DEBUG" in line for line in lines), 1)
            self.assertIn('export QEMU_MODULE_DIR="$tools_root/root/' + tools.MODULE_DIR + '"', lines)
            self.assertIn('ld-linux-x86-64.so.2" --inhibit-cache --library-path', lines[run])

    def test_every_unpacked_qemu_module_must_resolve_inside_the_locked_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            dest = Path(temporary)
            modules = dest / "root" / tools.MODULE_DIR
            modules.mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, "No QEMU modules unpacked"):
                tools.module_closure(dest)  # a layout change must not pass vacuously
            (modules / "hw-usb-host.so").write_bytes(b"\x7fELF fixture")
            (modules / "ui-curses.so").write_bytes(b"\x7fELF fixture")
            inside = "\tlibusb-1.0.so.0 => %s (0x1)\n\t/lib64/ld-linux-x86-64.so.2 => %s (0x2)\n" % (
                dest / "root/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0", dest / "root/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2")
            listings = {"hw-usb-host.so": inside, "ui-curses.so": "\tlinux-vdso.so.1 (0x3)\n"}
            with mock.patch.object(tools, "_ld_list", lambda d, target: listings[Path(target).name]):
                self.assertEqual(tools.module_closure(dest), {"hw-usb-host.so": ["/lib64/ld-linux-x86-64.so.2", "libusb-1.0.so.0"],
                                                              "ui-curses.so": []})
                for leak in ("\tlibusb-1.0.so.0 => /usr/lib/x86_64-linux-gnu/libusb-1.0.so.0 (0x1)\n", "\tlibusb-1.0.so.0 => not found\n"):
                    listings["hw-usb-host.so"] = leak
                    with self.subTest(leak=leak), self.assertRaisesRegex(RuntimeError, "QEMU module .*: hw-usb-host.so: libusb"):
                        tools.module_closure(dest)

    def test_module_upgrade_directory_uses_the_canonical_package_version(self):
        self.assertEqual(tools.module_upgrade_dir("QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1)"),
                         "/var/run/qemu/Debian_1_8.2.2+ds-0ubuntu1")
        self.assertEqual(tools.module_upgrade_dir("QEMU emulator version 9.0 (a b/c~d)"), "/var/run/qemu/a_b_c~d")
        with self.assertRaisesRegex(RuntimeError, "no package version"):
            tools.module_upgrade_dir("QEMU emulator version 8.2.2")

    def test_loader_log_parser_resolves_sonames_dlopens_and_fails_closed(self):
        # glibc logs POSIX paths; this fixture root never exists, so nothing resolves through a link.
        root = Path("/srrx-lab-fixture/tools/root")
        lib, program = (root / "usr/lib/x86_64-linux-gnu").as_posix(), (root / "usr/bin/qemu-system-aarch64").as_posix()
        log = "\n".join(["     71:\tfile=%s [0];  generating link map" % program,
                         "     71:\t  dynamic: 0x1  base: 0x0   size: 0x2",
                         "     71:\tfile=libglib-2.0.so.0 [0];  needed by %s [0]" % program,
                         "     71:\tfind library=libglib-2.0.so.0 [0]; searching",
                         "     71:\t search path=%s/glibc-hwcaps/x86-64-v3:%s\t\t(LD_LIBRARY_PATH)" % (lib, lib),
                         "     71:\t  trying file=%s/glibc-hwcaps/x86-64-v3/libglib-2.0.so.0" % lib,
                         "     71:\t  trying file=%s/libglib-2.0.so.0" % lib,
                         "     71:\t", "     71:\tfile=libglib-2.0.so.0 [0];  generating link map",
                         "     71:\tfile=%s/qemu/hw-usb-host.so [0];  dynamically loaded by %s/libgmodule-2.0.so.0 [0]" % (lib, lib),
                         "     71:\tfile=%s/qemu/hw-usb-host.so [0];  generating link map" % lib,
                         "     71:\tcalling init: %s/libgmodule-2.0.so.0" % lib, ""])
        audit = host.loader_audit([log], root, program)
        self.assertEqual((audit["status"], audit["objects"], audit["outside_tools_root"]), ("PASS", 4, []))
        self.assertEqual(audit["mapped_inside_tools_root"], sorted(["usr/bin/qemu-system-aarch64", "usr/lib/x86_64-linux-gnu/libglib-2.0.so.0",
                                                                    "usr/lib/x86_64-linux-gnu/qemu/hw-usb-host.so", "usr/lib/x86_64-linux-gnu/libgmodule-2.0.so.0"]))
        self.assertEqual(audit["dlopened"], [lib + "/qemu/hw-usb-host.so"])
        host_nss = log + "\n".join(["     72:\tfind library=libnss_files.so.2 [0]; searching",
                                    "     72:\t  trying file=/lib/x86_64-linux-gnu/libnss_files.so.2",
                                    "     72:\tfile=libnss_files.so.2 [0];  generating link map", ""])
        audit = host.loader_audit([host_nss], root, program)
        self.assertEqual((audit["status"], audit["outside_tools_root"]), ("FAIL", [str(Path("/lib/x86_64-linux-gnu/libnss_files.so.2").resolve())]))
        # A soname without its own search (stale 'trying' discarded) and a log without the program both fail.
        unresolved = "     73:\t  trying file=%s/libz.so.1\n     73:\tfind library=libx.so.1 [0]; searching\n     73:\tfile=libx.so.1 [0];  generating link map\n" % lib
        audit = host.loader_audit([log, unresolved], root, program)
        self.assertEqual(audit["outside_tools_root"], ["libx.so.1 (unresolved)"])
        audit = host.loader_audit([log.split("\n", 1)[1]], root, program)
        self.assertEqual((audit["status"], audit["program_mapped"]), ("FAIL", False))
        self.assertEqual(host.loader_audit([], root, program)["status"], "FAIL")

    @unittest.skipUnless(LINUX and any(Path(p).exists() for p in ("/lib64/ld-linux-x86-64.so.2", "/lib/ld-linux-aarch64.so.1")),
                         "Linux glibc loader required")
    def test_loader_log_parser_reads_the_real_glibc_format(self):
        # Format drift guard on the CI hosts and in the ARM64 guest (glibc 2.39, as the locked ld.so).
        ldso = next(p for p in ("/lib64/ld-linux-x86-64.so.2", "/lib/ld-linux-aarch64.so.1") if Path(p).exists())
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ, LD_DEBUG="files,libs", LD_DEBUG_OUTPUT=str(Path(temporary) / "x"))
            subprocess.run([ldso, "/bin/true"], env=env, check=True, capture_output=True, timeout=30)
            logs = [p.read_text(errors="replace") for p in sorted(Path(temporary).glob("x.*"))]
            self.assertTrue(logs)
            audit = host.loader_audit(logs, Path(temporary) / "empty-root", "/bin/true")
            mapped, _, unresolved = host.loader_objects(logs)
        self.assertTrue(audit["program_mapped"])
        self.assertEqual(unresolved, set())
        libc = {Path(p).resolve() for p in mapped if Path(p).name == "libc.so.6"}
        self.assertEqual(len(libc), 1)
        self.assertTrue(next(iter(libc)).is_file())
        self.assertIn(str(next(iter(libc))), audit["outside_tools_root"])  # the host libc is outside this root
        self.assertEqual(audit["status"], "FAIL")

    def test_prepare_accepts_only_the_locked_wrappers_and_no_module_upgrade_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            bin_dir = Path(temporary) / "qemu-tools/bin"
            bin_dir.mkdir(parents=True)
            for name, text in tools.wrapper_texts().items():
                (bin_dir / name).write_text(text, newline="\n")
            selected = [bin_dir / name for name in ("qemu-system-aarch64", "qemu-img", "genisoimage")]
            upgrade = Path(temporary) / "var-run-qemu"
            helper = types.SimpleNamespace(wrapper_texts=tools.wrapper_texts, module_closure=lambda dest: {"hw-usb-host.so": ["libusb-1.0.so.0"]},
                                           module_upgrade_dir=lambda version: str(upgrade))
            version = subprocess.CompletedProcess([], 0, "QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1)\n", "")
            with mock.patch.object(host, "fetch_tools", lambda: helper), mock.patch.object(host, "call", lambda *a, **k: version):
                record = host.qemu_runtime(*selected)
                self.assertEqual((record["module_count"], record["module_upgrade_dir_present"]), (1, False))
                self.assertEqual(record["tools_root"], str((Path(temporary) / "qemu-tools").resolve()))
                upgrade.mkdir()
                with self.assertRaisesRegex(ValueError, "module-upgrade directory"):
                    host.qemu_runtime(*selected)
                upgrade.rmdir()
                (bin_dir / "qemu-img").write_text("#!/bin/sh\nexec /usr/bin/qemu-img \"$@\"\n")
                with self.assertRaisesRegex(ValueError, "wrappers of one locked tools directory: qemu-img"):
                    host.qemu_runtime(*selected)
                (bin_dir / "qemu-img").write_text(tools.wrapper_texts()["qemu-img"], newline="\n")
                other = Path(temporary) / "other/bin"
                other.mkdir(parents=True)
                shutil.copyfile(bin_dir / "genisoimage", other / "genisoimage")
                with self.assertRaisesRegex(ValueError, "genisoimage"):
                    host.qemu_runtime(selected[0], selected[1], other / "genisoimage")
                helper.module_closure = lambda dest: (_ for _ in ()).throw(RuntimeError("QEMU module resolves a library outside"))
                with self.assertRaisesRegex(ValueError, "Locked QEMU runtime check failed"):
                    host.qemu_runtime(*selected)

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
