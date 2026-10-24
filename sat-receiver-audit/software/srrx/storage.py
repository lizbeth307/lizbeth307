"""Opt-in Linux removable-storage binding; no formatting, mounting or power API.

StorageGuard(root, device) requires an existing *exact* mountpoint and explicit
block-device path (prefer /dev/disk/by-uuid/<operator-verified-UUID>). It pins
that directory, checks /proc/self/mountinfo + fdinfo mnt_id + st_dev and block
identity at every operation, and revokes permanently on loss/replacement/error.
No output parent directory is created. Paths are relative to root or absolute
below it; all existing parents must be real directories on the same mount.

Writes use O_NOFOLLOW and dirfd-relative staging/replace. JSONL append to an
existing file writes only the new line to the same checked inode (O(line), not
a whole-file copy) and truncates back to the previous complete lines on a write
or fsync error; a power loss mid-append can leave one torn final line, which a
later append refuses. A new JSONL file is created by staging+replace.
One writer owns a guard; advisory locking does not protect against privileged
mount manipulation or an unrelated program ignoring the lock. Mount/output
directories must be writable only by the trusted capture writer; malicious
concurrent directory writers can replace staging names. This is a
filesystem guard, not a raw-IQ policy, USB qualification or power-loss guarantee.

Primary interfaces:
https://www.kernel.org/doc/html/latest/filesystems/proc.html
https://docs.python.org/3/library/os.html
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import stat


MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_MOUNTINFO_BYTES = 2 * 1024 * 1024
MAX_MOUNTS = 8192


class StorageRevoked(OSError):
    def __init__(self, reason):
        super().__init__(errno.ENODEV, "Storage guard revoked: " + reason)


def _unescape(value):
    return re.sub(r"\\(040|011|012|134)", lambda match: chr(int(match.group(1), 8)), value)


def _parse_mountinfo(raw):
    if len(raw.encode("utf-8")) > MAX_MOUNTINFO_BYTES:
        raise OSError(errno.EOVERFLOW, "Mount inventory exceeds bound")
    lines = raw.splitlines()
    if len(lines) > MAX_MOUNTS:
        raise OSError(errno.EOVERFLOW, "Too many mount entries")
    mounts = []
    for line in lines:
        left, separator, right = line.partition(" - ")
        fields, tail = left.split(), right.split()
        if not separator or len(fields) < 6 or len(tail) < 3:
            raise OSError(errno.EINVAL, "Malformed mount inventory")
        try:
            major, minor = map(int, fields[2].split(":"))
            mount_id = int(fields[0])
        except (ValueError, IndexError) as error:
            raise OSError(errno.EINVAL, "Malformed mount identity") from error
        if mount_id < 1 or major < 0 or minor < 0:
            raise OSError(errno.EINVAL, "Invalid mount identity")
        mounts.append({"mount_id": mount_id, "major": major, "minor": minor,
                       "mount_root": _unescape(fields[3]), "mountpoint": _unescape(fields[4]),
                       "options": fields[5], "filesystem": tail[0], "source": _unescape(tail[1])})
    return mounts


def _read_mountinfo():
    with open("/proc/self/mountinfo", "rb") as source:
        raw = source.read(MAX_MOUNTINFO_BYTES + 1)
    if len(raw) > MAX_MOUNTINFO_BYTES:
        raise OSError(errno.EOVERFLOW, "Mount inventory exceeds bound")
    return _parse_mountinfo(raw.decode("utf-8", "strict"))


def _fd_mount_id(fd):
    with open("/proc/self/fdinfo/" + str(fd), "rb") as source:
        raw = source.read(4097)
    if len(raw) > 4096:
        raise OSError(errno.EOVERFLOW, "fdinfo exceeds bound")
    for line in raw.decode("ascii", "strict").splitlines():
        if line.startswith("mnt_id:"):
            value = int(line.split(":", 1)[1].strip())
            if value > 0:
                return value
    raise OSError(errno.ENOTSUP, "Linux fdinfo mount identity unavailable")


def _block_identity(device):
    path = Path(device)
    if not path.is_absolute() or not str(path).startswith("/dev/"):
        raise OSError(errno.EINVAL, "Explicit /dev block-device binding required")
    value = path.stat()  # The operator's by-UUID symlink is intentional here.
    if not stat.S_ISBLK(value.st_mode):
        raise OSError(errno.ENOTBLK, "Storage binding is not a block device")
    return (os.major(value.st_rdev), os.minor(value.st_rdev), str(path.resolve(strict=True)))


def _directory_flags():
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise OSError(errno.ENOTSUP, "Linux NOFOLLOW directory descriptors required")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _open_absolute_directory(path):
    fd = os.open("/", _directory_flags())
    try:
        for component in Path(path).parts[1:]:
            following = os.open(component, _directory_flags(), dir_fd=fd)
            os.close(fd)
            fd = following
        return fd
    except BaseException:
        os.close(fd)
        raise


def _inode(value):
    return value.st_dev, value.st_ino


def _write_all(fd, encoded):
    remaining = memoryview(encoded)
    while remaining:
        count = os.write(fd, remaining[:65536])
        if count <= 0:
            raise OSError(errno.EIO, "Storage write made no progress")
        remaining = remaining[count:]


class StorageGuard:
    def __init__(self, root, device):
        root = Path(root)
        if ".." in root.parts:
            raise ValueError("Storage root cannot contain parent traversal")
        self.root = Path(os.path.abspath(root))
        if self.root == Path("/"):
            raise ValueError("Root filesystem cannot be the removable-storage root")
        self.device = str(device)
        self.revoked, self.reason, self._closed = False, None, False
        self._root_fd = None
        try:
            self._device = _block_identity(self.device)
            self._root_fd = _open_absolute_directory(self.root)
            self._root_stat = os.fstat(self._root_fd)
            mount_id = _fd_mount_id(self._root_fd)
            matches = [m for m in _read_mountinfo() if m["mount_id"] == mount_id
                       and m["mountpoint"] == str(self.root)]
            if len(matches) != 1:
                raise StorageRevoked("Configured root is not the exact current mountpoint")
            self._mount = matches[0]
            self._validate_mount(self._mount)
            self.check()
        except BaseException:
            self.close()
            raise

    def _validate_mount(self, mount):
        expected = self._device[:2]
        if (mount["major"], mount["minor"]) != expected:
            raise StorageRevoked("Mounted device differs from explicit binding")
        if (os.major(self._root_stat.st_dev), os.minor(self._root_stat.st_dev)) != expected:
            raise StorageRevoked("Directory st_dev differs from mounted block device")
        if "rw" not in mount["options"].split(","):
            raise StorageRevoked("Bound mount is not writable")
        if _block_identity(mount["source"])[:2] != expected:
            raise StorageRevoked("Mount source is not the bound block device")

    @property
    def identity(self):
        return {"root": str(self.root), "device": self.device,
                "resolved_device": self._device[2], **self._mount,
                "root_inode": self._root_stat.st_ino, "physical_verified": False}

    def revoke(self, reason):
        if not self.revoked:
            self.revoked, self.reason = True, str(reason)[:240]

    def check(self):
        if self.revoked or self._closed:
            raise StorageRevoked(self.reason or "Guard closed")
        current_fd = None
        try:
            if _block_identity(self.device) != self._device:
                raise StorageRevoked("Configured block-device identity changed")
            mounts = [m for m in _read_mountinfo() if m["mount_id"] == self._mount["mount_id"]]
            if len(mounts) != 1 or mounts[0] != self._mount:
                raise StorageRevoked("Bound mount was lost, moved or replaced")
            self._validate_mount(mounts[0])
            current_fd = _open_absolute_directory(self.root)
            if (_fd_mount_id(current_fd) != self._mount["mount_id"]
                    or _inode(os.fstat(current_fd)) != _inode(self._root_stat)
                    or _fd_mount_id(self._root_fd) != self._mount["mount_id"]):
                raise StorageRevoked("Storage path no longer names the pinned mount root")
            return self.identity
        except (OSError, ValueError, UnicodeError) as error:
            self.revoke(error)
            raise StorageRevoked(self.reason) from error
        finally:
            if current_fd is not None:
                os.close(current_fd)

    def _parts(self, path):
        path = Path(path)
        if ".." in path.parts:
            raise ValueError("Storage output cannot contain parent traversal")
        if path.is_absolute():
            try:
                path = path.relative_to(self.root)
            except ValueError as error:
                raise ValueError("Output must remain under the bound storage root") from error
        parts = path.parts
        if not parts or len(str(path)) > 4096 or any(len(p.encode()) > 255 for p in parts):
            raise ValueError("Bounded storage file path required")
        return parts

    def _parent(self, parts):
        fd = os.dup(self._root_fd)
        try:
            for component in parts[:-1]:
                following = os.open(component, _directory_flags(), dir_fd=fd)
                os.close(fd)
                fd = following
                if (_fd_mount_id(fd) != self._mount["mount_id"]
                        or os.fstat(fd).st_dev != self._root_stat.st_dev):
                    raise StorageRevoked("Output crosses a nested or foreign mount")
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _existing(self, parent, name):
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=parent)
        except FileNotFoundError:
            return None, None
        try:
            value = os.fstat(fd)
            if (not stat.S_ISREG(value.st_mode) or value.st_nlink != 1
                    or value.st_size > MAX_FILE_BYTES
                    or _fd_mount_id(fd) != self._mount["mount_id"]
                    or value.st_dev != self._root_stat.st_dev):
                raise StorageRevoked("Output is not a bounded regular single-link file on the bound mount")
            return fd, value
        except BaseException:
            os.close(fd)
            raise

    def _commit(self, path, encoded, append):
        parts = self._parts(path)
        if len(encoded) > MAX_FILE_BYTES:
            raise ValueError("Storage JSON exceeds bounded write size")
        self.check()
        parent, existing, temporary_fd, temporary_name = None, None, None, None
        locked = False
        try:
            fcntl.flock(self._root_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            parent = self._parent(parts)
            existing, previous = self._existing(parent, parts[-1])
            if append and previous is not None and previous.st_size + len(encoded) > MAX_FILE_BYTES:
                raise OSError(errno.EFBIG, "Bounded survey size reached; choose a new file explicitly")
            if append and existing is not None:
                self._append(parent, parts, existing, previous, encoded)
                return
            for _ in range(5):
                temporary_name = ".srrx-" + secrets.token_hex(12)
                try:
                    temporary_fd = os.open(temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                           0o600, dir_fd=parent)
                    break
                except FileExistsError:
                    temporary_name = None
            if temporary_fd is None:
                raise OSError(errno.EEXIST, "Cannot create unique storage staging file")
            _write_all(temporary_fd, encoded)
            os.fsync(temporary_fd)
            self._verify(parent, parts, previous)
            os.replace(temporary_name, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
            temporary_name = None
            os.fsync(parent)
            self.check()
        except OSError as error:
            self.revoke(error)
            raise
        finally:
            for fd in (temporary_fd, existing):
                if fd is not None:
                    os.close(fd)
            if temporary_name is not None and parent is not None:
                try:
                    os.unlink(temporary_name, dir_fd=parent)
                except OSError:
                    pass
            if parent is not None:
                os.close(parent)
            if locked:
                fcntl.flock(self._root_fd, fcntl.LOCK_UN)

    def _verify(self, parent, parts, previous):
        self.check()
        # Reopen from the pinned root: reject a renamed/symlinked parent.
        verified = self._parent(parts)
        try:
            if _inode(os.fstat(verified)) != _inode(os.fstat(parent)):
                raise StorageRevoked("Output parent changed during write")
        finally:
            os.close(verified)
        current, value = self._existing(parent, parts[-1])
        if current is not None:
            os.close(current)
        key = lambda item: None if item is None else (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        if key(value) != key(previous):
            raise StorageRevoked("Output changed during atomic write")

    def _append(self, parent, parts, existing, previous, encoded):
        """O(line) append to the verified inode; a failed write is truncated back."""
        if previous.st_size and os.pread(existing, 1, previous.st_size - 1) != b"\n":
            raise OSError(errno.EILSEQ, "Survey does not end with a complete line; choose a new file explicitly")
        self._verify(parent, parts, previous)
        # Reopen the exact checked inode via its descriptor, never by name again.
        fd = os.open("/proc/self/fd/" + str(existing), os.O_WRONLY | os.O_APPEND | getattr(os, "O_CLOEXEC", 0))
        try:
            if _inode(os.fstat(fd)) != _inode(previous):
                raise StorageRevoked("Output changed during append")
            try:
                _write_all(fd, encoded)
                os.fsync(fd)
            except BaseException:
                os.ftruncate(fd, previous.st_size)  # keep exactly the previous complete lines
                os.fsync(fd)
                raise
            if os.fstat(fd).st_size != previous.st_size + len(encoded):
                raise StorageRevoked("Output changed during append")
        finally:
            os.close(fd)
        self.check()

    def open_directory(self, path):
        """O_NOFOLLOW descriptor of an existing directory below the root, on the bound mount
        (srrx.baseband: dirfd-relative raw writes). The caller closes it."""
        parts = self._parts(path)
        self.check()
        return self._parent(tuple(parts) + ("",))  # _parent opens every component but the last

    def atomic_json(self, path, value):
        encoded = (json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        self._commit(path, encoded, False)

    def append_jsonl(self, path, value):
        encoded = (json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        self._commit(path, encoded, True)

    def close(self):
        if self._root_fd is not None:
            os.close(self._root_fd)
            self._root_fd = None
        self._closed = True

    def __enter__(self):
        self.check()
        return self

    def __exit__(self, *_):
        self.close()
