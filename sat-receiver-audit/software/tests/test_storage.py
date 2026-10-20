"""Real dirfd/filesystem IO with injected mount/block inventory, no physical disk."""
import contextlib
import errno
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from srrx import storage
from srrx.storage import StorageGuard, StorageRevoked


class BoundFixture:
    """Only Linux mount-table/block identity are injected; IO uses real syscalls."""
    def __init__(self, root):
        self.root = Path(root)
        self.device = "/dev/srrx-unit-fixture"
        descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            self.mount_id = storage._fd_mount_id(descriptor)
        finally:
            os.close(descriptor)
        self.dev = self.root.stat().st_dev
        self.identity = (os.major(self.dev), os.minor(self.dev), self.device)
        self.rows = [{"mount_id": self.mount_id, "major": self.identity[0], "minor": self.identity[1],
                      "mount_root": "/", "mountpoint": str(self.root), "options": "rw,relatime",
                      "filesystem": "fixture-only", "source": self.device}]
        self.table_patch = patch("srrx.storage._read_mountinfo", side_effect=lambda: [dict(x) for x in self.rows])
        self.block_patch = patch("srrx.storage._block_identity", side_effect=lambda _: self.identity)

    def __enter__(self):
        self.table_patch.start()
        self.block_patch.start()
        self.guard = StorageGuard(self.root, self.device)
        return self

    def __exit__(self, *_):
        self.guard.close()
        self.block_patch.stop()
        self.table_patch.stop()


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="srrx-storage-test-")
        self.root = Path(self.temporary.name) / "mounted"
        self.root.mkdir()
        self.fixture = BoundFixture(self.root)
        self.fixture.__enter__()
        self.guard = self.fixture.guard

    def tearDown(self):
        self.fixture.__exit__()
        self.temporary.cleanup()

    def test_atomic_and_atomic_jsonl_use_existing_bound_directories(self):
        (self.root / "logs").mkdir()
        self.guard.atomic_json("logs/latest.json", {"source": "SIMULATION", "n": 1})
        self.guard.atomic_json(self.root / "logs/latest.json", {"n": 2})
        self.guard.append_jsonl("logs/survey.jsonl", {"n": 1})
        self.guard.append_jsonl("logs/survey.jsonl", {"n": 2})
        self.assertEqual(json.loads((self.root / "logs/latest.json").read_text()), {"n": 2})
        self.assertEqual([json.loads(x) for x in (self.root / "logs/survey.jsonl").read_text().splitlines()], [{"n": 1}, {"n": 2}])
        self.assertEqual((self.root / "logs/latest.json").stat().st_mode & 0o777, 0o600)
        self.assertFalse(list(self.root.rglob(".srrx-*")))
        self.assertFalse(self.guard.revoked)

    def test_missing_parent_never_created_and_permanently_revokes(self):
        with self.assertRaises(OSError):
            self.guard.atomic_json("missing/file.json", {"n": 1})
        self.assertFalse((self.root / "missing").exists())
        self.assertTrue(self.guard.revoked)
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("later.json", {})
        self.assertFalse((self.root / "later.json").exists())

    def test_mount_disappeared_never_creates_output_root(self):
        self.fixture.rows.clear()
        self.root.rmdir()
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("fallback/file.json", {})
        self.assertFalse(self.root.exists())
        self.assertTrue(self.guard.revoked)
        self.fixture.rows.append({})
        with self.assertRaises(StorageRevoked):
            self.guard.check()  # It cannot recover implicitly after revocation.

    def test_mount_id_replacement_same_st_dev_is_rejected(self):
        self.fixture.rows[0]["mount_id"] += 1
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("latest.json", {})
        self.assertFalse((self.root / "latest.json").exists())

    def test_replaced_root_inode_rejected_even_with_same_mount_table(self):
        moved = self.root.with_name("old-mounted")
        self.root.rename(moved)
        self.root.mkdir()
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("latest.json", {})
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(list(moved.iterdir()), [])

    def test_device_alias_change_is_rejected(self):
        major, minor, _ = self.fixture.identity
        self.fixture.identity = (major, minor, "/dev/replaced-device")
        with self.assertRaises(StorageRevoked):
            self.guard.check()

    def test_readonly_or_changed_source_revokes(self):
        self.fixture.rows[0]["options"] = "ro,relatime"
        with self.assertRaises(StorageRevoked):
            self.guard.check()

    def test_foreign_nested_mount_same_st_dev_rejected(self):
        nested = self.root / "foreign"
        nested.mkdir()
        real_mount_id = storage._fd_mount_id
        inode = nested.stat().st_ino
        def foreign(fd):
            return self.fixture.mount_id + 1 if os.fstat(fd).st_ino == inode else real_mount_id(fd)
        with patch("srrx.storage._fd_mount_id", side_effect=foreign):
            with self.assertRaises(StorageRevoked):
                self.guard.atomic_json("foreign/latest.json", {})
        self.assertFalse((nested / "latest.json").exists())

    def test_parent_symlink_cannot_write_outside_mount(self):
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            self.guard.atomic_json("link/latest.json", {})
        self.assertEqual(list(outside.iterdir()), [])

    def test_leaf_symlink_and_hardlink_rejected(self):
        outside = Path(self.temporary.name) / "outside.json"
        outside.write_text("keep")
        (self.root / "linked.json").symlink_to(outside)
        with self.assertRaises(OSError):
            self.guard.append_jsonl("linked.json", {})
        self.assertEqual(outside.read_text(), "keep")
        # A new explicit binding is required after revocation.
        self.guard.close()
        self.guard = self.fixture.guard = StorageGuard(self.root, self.fixture.device)
        (self.root / "linked.json").unlink()
        os.link(outside, self.root / "hard.json")
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("hard.json", {})
        self.assertEqual(outside.read_text(), "keep")

    def test_outside_and_parent_traversal_are_rejected_without_writes(self):
        for path in ("../escape.json", self.root.parent / "escape.json", "."):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.guard.atomic_json(path, {})
        self.assertFalse((self.root.parent / "escape.json").exists())

    def test_partial_enospc_preserves_previous_atomic_and_jsonl_files(self):
        for append in (False, True):
            with self.subTest(append=append):
                if self.guard.revoked:
                    self.guard.close()
                    self.guard = self.fixture.guard = StorageGuard(self.root, self.fixture.device)
                destination = self.root / "saved.json"
                destination.write_bytes(b'{"keep":1}\n')
                def partial(fd, value):
                    os.write(fd, bytes(value)[:3])
                    raise OSError(errno.ENOSPC, "injected disk full")
                operation = self.guard.append_jsonl if append else self.guard.atomic_json
                with patch("srrx.storage._write_all", side_effect=partial):
                    with self.assertRaises(OSError) as failure:
                        operation("saved.json", {"new": 2})
                self.assertEqual(failure.exception.errno, errno.ENOSPC)
                self.assertEqual(destination.read_bytes(), b'{"keep":1}\n')
                self.assertFalse(list(self.root.glob(".srrx-*")))
                self.assertTrue(self.guard.revoked)

    def test_mount_loss_after_staging_before_commit_preserves_previous_file(self):
        destination = self.root / "saved.json"
        destination.write_bytes(b'{"keep":1}\n')
        fsync = os.fsync
        def lose_mount(fd):
            fsync(fd)
            self.fixture.rows.clear()
        with patch("srrx.storage.os.fsync", side_effect=lose_mount):
            with self.assertRaises(StorageRevoked):
                self.guard.atomic_json("saved.json", {"new": 2})
        self.assertEqual(destination.read_bytes(), b'{"keep":1}\n')
        self.assertFalse(list(self.root.glob(".srrx-*")))

    def test_parent_symlink_swap_after_staging_is_rejected(self):
        parent = self.root / "logs"
        parent.mkdir()
        (parent / "saved.json").write_text("keep")
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        moved = self.root / "old-logs"
        fsync = os.fsync
        def swap(fd):
            fsync(fd)
            parent.rename(moved)
            parent.symlink_to(outside, target_is_directory=True)
        with patch("srrx.storage.os.fsync", side_effect=swap):
            with self.assertRaises(OSError):
                self.guard.atomic_json("logs/saved.json", {"new": 2})
        self.assertEqual((moved / "saved.json").read_text(), "keep")
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(list(moved.glob(".srrx-*")))

    def test_nan_and_size_bound_do_not_replace_file(self):
        self.guard.atomic_json("latest.json", {"keep": 1})
        original = (self.root / "latest.json").read_bytes()
        with self.assertRaises(ValueError):
            self.guard.atomic_json("latest.json", {"bad": float("nan")})
        with patch("srrx.storage.MAX_FILE_BYTES", 8):
            with self.assertRaises(ValueError):
                self.guard.atomic_json("latest.json", {"bad": "too long"})
        self.assertEqual((self.root / "latest.json").read_bytes(), original)

    def test_survey_masks_before_guarded_persistence(self):
        from srrx.spectrum import append_survey, validate_frame
        frame = {"v": 1, "kind": "spectrum", "center_hz": 300000000, "sample_rate_hz": 1024000,
                 "fft_size": 16, "power_dbfs": [-70.0] * 16, "valid": [True] * 16,
                 "relative_frequency_hz": [(i - 8) * 1024000 / 16 for i in range(16)],
                 "source": "SIMULATION", "sample_count": 16}
        safe = append_survey("survey.jsonl", frame, storage_guard=self.guard)
        saved = json.loads((self.root / "survey.jsonl").read_text())
        self.assertEqual(saved, validate_frame(safe))
        self.assertTrue(all(value is None for value in saved["power_dbfs"]))

    def test_capture_storage_loss_closes_source_and_requests_branch_off(self):
        import numpy as np
        from srrx.labrx import run_capture
        calls = []
        fixture = self.fixture
        class Source:
            closed = False
            def read(self, guard):
                fixture.rows.clear()
                return np.ones(64, dtype=np.complex64)
            def close(self):
                self.closed = True
        source = Source()
        def transport(request):
            calls.append(request)
            return {"ok": True, "data": {"mode": "HARDWARE", "hardware_qualified": True,
                    "live_identity_verified": True, "configured": True, "last_error": None, "session": 10,
                    "pico": {"state": "ACTIVE", "mcp_reset": False},
                    "policy": {"armed": True, "commissioned": True, "pico_active": True, "fault": None,
                               "outputs": {"EN_RTLA": True}}}}
        with self.assertRaises(StorageRevoked):
            run_capture(record={"backend": "rtl", "branch": "RTLA"}, transport=transport,
                        source_factory=lambda *args: source, fft_size=64, frames=1,
                        output="latest.json", storage_guard=self.guard)
        self.assertTrue(source.closed)
        self.assertEqual(calls[-1], {"op": "control", "name": "EN_RTLA", "value": False})
        self.assertFalse((self.root / "latest.json").exists())

    def test_closed_guard_cannot_be_reused(self):
        self.guard.close()
        with self.assertRaises(StorageRevoked):
            self.guard.atomic_json("later.json", {})


class NativeBindingTests(unittest.TestCase):
    def test_regular_file_is_not_a_block_device(self):
        with patch("srrx.storage.os.stat", return_value=Path(__file__).stat()):
            with self.assertRaises(OSError) as failure:
                storage._block_identity("/dev/not-a-block-device")
        self.assertEqual(failure.exception.errno, errno.ENOTBLK)

    def test_mountinfo_escapes_and_bounds(self):
        rows = storage._parse_mountinfo("24 1 8:17 / /media/T7\\040disk rw,nosuid - ext4 /dev/sdb1 rw\n")
        self.assertEqual(rows[0]["mountpoint"], "/media/T7 disk")
        for malformed in ("bad", "x 1 x:y / /tmp rw - ext4 /dev/no rw", "0 1 8:1 / /tmp rw - ext4 /dev/no rw"):
            with self.assertRaises(OSError):
                storage._parse_mountinfo(malformed)
        with patch("srrx.storage.MAX_MOUNTINFO_BYTES", 8), self.assertRaises(OSError):
            storage._parse_mountinfo("too much mount data")

    def test_foreign_initial_device_and_not_exact_mountpoint_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with BoundFixture(temporary) as bound:
                major, minor, device = bound.identity
                bound.identity = (major + 1, minor, device)
                with self.assertRaises(StorageRevoked):
                    StorageGuard(temporary, device)
                bound.identity = (major, minor, device)
                bound.rows[0]["mountpoint"] = str(Path(temporary).parent)
                with self.assertRaises(StorageRevoked):
                    StorageGuard(temporary, device)

    def test_cli_pair_and_regular_file_binding_fail_cleanly(self):
        from srrx.labrx import main
        for arguments in (["--simulate", "--storage-root", "/tmp/not-a-real-mount"],
                          ["--simulate", "--storage-root", "/tmp", "--storage-device", "/dev/null"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(main(arguments), 2)
                self.assertIn("labrx:", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
