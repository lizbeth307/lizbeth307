"""tools/flash_mcu.py against a fake mpremote transport: no board is touched or flashed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("srrx_flash_mcu", PROJECT / "tools/flash_mcu.py")
flash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash)
spec = importlib.util.spec_from_file_location("srrx_test_calibration", PROJECT / "firmware/pico/calibration.py")
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)

SERIAL = "e660583883724a2f"


class FakeBoard:
    """mpremote-shaped transport over an in-memory MicroPython filesystem."""
    def __init__(self, role, files=None, release=None, machine=None, version="mpremote 1.26.0"):
        pin = flash.board(role)
        self.files, self.log, self.version_text = dict(files or {}), [], version
        self.release, self.machine = release or pin["micropython"], machine or pin["uname_machine"]

    def version(self):
        return self.version_text

    def exec(self, code):
        self.log.append(("exec", code.split("\n", 1)[0]))
        if code == flash.HASH_SCRIPT:
            return "SRRX-FS " + json.dumps({n: hashlib.sha256(d).hexdigest() for n, d in self.files.items()}) + "\n"
        if code == flash.UNAME_SCRIPT:
            return "SRRX-UNAME " + json.dumps({"release": self.release, "machine": self.machine}) + "\n"
        if code == flash.SERIAL_SCRIPT:
            return "SRRX-SERIAL " + SERIAL + "\n"
        raise AssertionError("unexpected device code")

    def cp(self, local, remote):
        self.log.append(("cp", remote))
        self.files[remote] = Path(local).read_bytes()

    def rm(self, remote):
        self.log.append(("rm", remote))
        del self.files[remote]

    def reset(self):
        self.log.append(("reset", None))


def uf2(blocks, family=flash.RP2040_FAMILY, address=0x10000000):
    out = b""
    for n in range(blocks):
        out += struct.pack("<8I", flash.UF2_MAGIC[0], flash.UF2_MAGIC[1], flash.UF2_FAMILY_FLAG, address + 256 * n, 256, n, blocks, family)
        out += b"\0" * 476 + struct.pack("<I", flash.UF2_MAGIC[2])
    return out


class FlashMcuTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-mcu-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def records(self):
        cal = calibration.from_two_points(SERIAL, 48000, 12000, 64000, 16000, 0, 0, "bench-fixture")
        comm = calibration.seal({"v": 1, "revision": calibration.REVISION, "serial": SERIAL, "calibration_crc32": cal["crc32"],
                                 "hardware_commissioned": True, "qualification_record": "a" * 64}, commissioning=True)
        directory = self.root / "records"
        directory.mkdir()
        (directory / "calibration.json").write_text(json.dumps(cal))
        (directory / "commissioning.json").write_text(json.dumps(comm))
        return directory

    def test_package_order_is_the_documented_one(self):
        pico = list(flash.package("pico"))
        self.assertEqual(pico[0], "boot.py")  # firmware/pico/README.md: boot.py first, main.py last
        self.assertEqual(pico[-1], "main.py")
        self.assertEqual(sorted(pico), sorted(json.loads((PROJECT / "firmware/dist/build-manifest.json").read_text())["packages"]["pico"]["source_files"]))
        imu = list(flash.package("imu"))
        self.assertEqual(imu[-1], "main.py")
        self.assertNotIn("__init__.py", imu)  # CPython test marker only

    def test_install_copies_in_order_verifies_and_resets(self):
        board = FakeBoard("pico")
        result = flash.install(board, "pico", staging=self.root)
        copied = [name for op, name in board.log if op == "cp"]
        self.assertEqual(copied, flash.board("pico")["copy_order"])
        self.assertEqual(board.log[-1], ("reset", None))
        self.assertEqual(result["status"], "DEVICE_FILES_MATCH_PACKAGE")
        self.assertFalse(result["hardware_qualified"])
        self.assertEqual(flash.verify(board, "pico")["files"], sorted(copied))

    def test_records_are_bound_to_the_connected_pico(self):
        board = FakeBoard("pico")
        result = flash.install(board, "pico", self.records(), staging=self.root)
        self.assertTrue(result["records_copied"])
        copied = [name for op, name in board.log if op == "cp"]
        self.assertEqual(copied[-2:], ["calibration.json", "commissioning.json"])
        other = self.root / "other"
        other.mkdir()
        cal = calibration.from_two_points("0123456789abcdef", 48000, 12000, 64000, 16000, 0, 0, "bench-fixture")
        (other / "calibration.json").write_text(json.dumps(cal))
        (other / "commissioning.json").write_text("{}")
        with self.assertRaises(flash.FlashError):
            flash.install(FakeBoard("pico"), "pico", other, staging=self.root)
        with self.assertRaisesRegex(flash.FlashError, "only the Pico"):
            flash.install(FakeBoard("imu"), "imu", other, staging=self.root)

    def test_wrong_runtime_board_or_tool_and_dirty_filesystems_are_refused(self):
        for board in (FakeBoard("pico", release="1.25.0"), FakeBoard("pico", machine="Raspberry Pi Pico W with RP2040"),
                      FakeBoard("pico", version="mpremote 1.27.0"), FakeBoard("imu", release="1.26.0"),
                      FakeBoard("pico", files={"main.py": b"old supervisor"})):
            with self.assertRaises(flash.FlashError):
                flash.install(board, "imu" if board.machine.startswith("Waveshare") else "pico", staging=self.root)
            self.assertFalse([entry for entry in board.log if entry[0] in ("cp", "rm", "reset")])
        board = FakeBoard("pico")
        flash.install(board, "pico", staging=self.root)
        board.files["extra.py"] = b"stray"
        with self.assertRaisesRegex(flash.FlashError, "extra"):
            flash.verify(board, "pico")

    def test_uf2_checks_size_digest_magic_and_family(self):
        image = self.root / "fixture.uf2"
        data = uf2(4)
        image.write_bytes(data)
        pin = {"file": "fixture.uf2", "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "blocks": 4}
        self.assertEqual(flash.check_uf2(image, pin)["blocks"], 4)
        for bad in (uf2(4, family=0xE48BFF59), uf2(4, address=0x20000000)):
            image.write_bytes(bad)
            with self.assertRaises(flash.FlashError):
                flash.check_uf2(image, dict(pin, sha256=hashlib.sha256(bad).hexdigest()))
        image.write_bytes(uf2(4, address=0x20000000))
        ram = dict(pin, sha256=hashlib.sha256(image.read_bytes()).hexdigest())
        self.assertEqual(flash.check_uf2(image, ram, ram_loader=True)["blocks"], 4)  # the nuke loader runs from RAM
        image.write_bytes(data[:-1] + b"\x01")
        with self.assertRaisesRegex(flash.FlashError, "differs"):
            flash.check_uf2(image, pin)

    def test_uf2_copy_needs_a_bootsel_drive_and_execute(self):
        image = self.root / "fixture.uf2"
        data = uf2(2)
        image.write_bytes(data)
        drive = self.root / "drive"
        drive.mkdir()
        (drive / "INFO_UF2.TXT").write_text("UF2 Bootloader v3.0\nModel: Raspberry Pi RP2\nBoard-ID: RPI-RP2\n")
        pin = {"file": "fixture.uf2", "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "blocks": 2}
        with patch.object(flash, "board", lambda role: {"uf2": pin}):
            self.assertEqual(flash.main(["uf2", "--role", "pico", "--file", str(image), "--drive", str(drive)]), 0)
            self.assertFalse((drive / "fixture.uf2").exists())  # dry run
            self.assertEqual(flash.main(["uf2", "--role", "pico", "--file", str(image), "--drive", str(drive), "--execute"]), 0)
        self.assertEqual((drive / "fixture.uf2").read_bytes(), data)
        (drive / "INFO_UF2.TXT").write_text("Board-ID: SOMETHING-ELSE\n")
        with self.assertRaises(flash.FlashError):
            flash.copy_uf2(image, drive)

    def test_lock_pins_documented_runtimes(self):
        lock = flash.lock()
        self.assertEqual(lock["boards"]["pico"]["micropython"], "1.26.0")  # firmware/pico/README.md API target
        self.assertTrue(lock["boards"]["pico"]["uf2"]["file"].startswith("RPI_PICO-") and lock["boards"]["pico"]["uf2"]["file"].endswith("-v1.26.0.uf2"))
        self.assertTrue(lock["boards"]["imu"]["uf2"]["file"].startswith("WAVESHARE_RP2040_ZERO-"))
        for pin in [b["uf2"] for b in lock["boards"].values()] + [lock["flash_erase"]]:
            self.assertRegex(pin["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(pin["size"], pin["blocks"] * 512)
            self.assertTrue(pin["url"].startswith("https://") and pin["url"].endswith(pin["file"]))
        requirements = [l for l in (PROJECT / "firmware/mpremote-requirements.txt").read_text().splitlines() if l and not l.startswith("#")]
        self.assertEqual(requirements[0].split()[0], "mpremote==" + lock["mpremote"]["version"])
        self.assertTrue(all("--hash=sha256:" in l for l in requirements))

    def test_dry_run_prints_the_plan_without_a_device(self):
        plan = flash.plan_install("pico", "/dev/ttyACM0", "/srv/records")
        self.assertIn("mpremote connect /dev/ttyACM0 fs cp <boot.py from firmware/dist/pico-micropython-files.zip> :boot.py", plan)
        self.assertTrue(plan[-1].endswith("reset"))
        self.assertTrue(any(":commissioning.json" in step for step in plan))


if __name__ == "__main__":
    unittest.main()
