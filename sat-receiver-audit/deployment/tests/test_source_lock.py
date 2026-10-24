"""sources.lock.json pins and deployment/fetch_sources.py, offline (file:// fixtures only)."""
import copy
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy  # noqa: E402
import fetch_sources  # noqa: E402
from test_repo import GPG, Keys  # noqa: E402

LOCK = deploy.load(HERE / "sources.lock.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class LockShapeTests(unittest.TestCase):
    def test_only_the_licensed_qairt_archive_is_unresolved(self):
        unresolved = {c["id"] for c in LOCK["components"] if c["source_archive_sha256"] is None}
        self.assertEqual(unresolved, {"qairt"})
        for component in LOCK["components"]:
            if component["source_archive_sha256"] is None:
                continue
            self.assertTrue(component["ref_verified"], component["id"])
            if component.get("debian_source"):
                self.assertIsNone(component["commit"])
                continue
            self.assertRegex(component["commit"], "^[0-9a-f]{40}$")
            self.assertTrue(component["source_archive_url"].startswith("https://"), component["id"])
            self.assertGreater(component["source_archive_size"], 0)
            if component["source_archive_url"].startswith("https://github.com/"):
                self.assertRegex(component.get("git_tree_sha1", ""), "^[0-9a-f]{40}$", component["id"])
                self.assertIn(component["commit"], component["source_archive_url"])

    def test_ubuntu_pins_come_from_one_signed_snapshot(self):
        snapshot = LOCK["apt_snapshot"]
        self.assertRegex(snapshot["timestamp"], r"^\d{8}T\d{6}Z$")
        self.assertEqual(snapshot["archive"], "https://snapshot.ubuntu.com/ubuntu")
        # The same archive key the ARM64 lab lock was verified against.
        guest = json.loads((HERE / "linux_lab/guest-packages.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(set(snapshot["signing_fingerprints"]), {f for r in guest["signed_releases"] for f in r["signing_fingerprints"]})
        noble = next(r for r in snapshot["releases"] if r["suite"] == "noble")
        self.assertEqual(noble["inrelease_sha256"], next(r for r in guest["signed_releases"] if r["suite"] == "noble")["sha256"])
        for cid in ("gnuradio", "volk", "gpsd", "chrony"):
            component = next(c for c in LOCK["components"] if c["id"] == cid)
            debian = component["debian_source"]
            self.assertIn(debian["suite"], snapshot["suites"])
            self.assertTrue(any(i["suite"] == debian["suite"] and i["path"] == debian["area"] + "/source/Sources.xz" for i in snapshot["indices"]))
            self.assertTrue(component["binary_debs"])
            for deb in component["binary_debs"]:
                # Same source pool directory, possibly another area (gpsd-clients is universe, gpsd main).
                self.assertEqual(deb["filename"].split("/")[2:4], debian["directory"].split("/")[2:4], deb["filename"])
                self.assertIn(deb["architecture"], ("arm64", "all"))
        for cid, version in (("gpsd", "3.25-3ubuntu3.2"), ("chrony", "4.5-1ubuntu4.2"), ("gnuradio", "3.10.9.2-1.1ubuntu2"), ("volk", "3.1.2-1.1build1")):
            self.assertEqual(next(c for c in LOCK["components"] if c["id"] == cid)["version"], version)  # STACK pins, unchanged

    def test_lime_kernel_modules_share_the_locked_lime_archive(self):
        lime = next(c for c in LOCK["components"] if c["id"] == "limesuiteng")
        for cid in ("la9310-limesdr", "la9310-uart"):
            module = next(c for c in LOCK["components"] if c["id"] == cid)
            self.assertEqual((module["commit"], module["source_archive_sha256"], module["source_cache_path"]),
                             (lime["commit"], lime["source_archive_sha256"], lime["source_cache_path"]))
            self.assertEqual(module["source_subdir"], "drivers/linux/la9310_limesdr")
        entries = deploy.cache_entries(LOCK, ["limesuiteng", "la9310-limesdr", "la9310-uart"], include_core=False)
        self.assertEqual([e["path"] for e in entries], [lime["source_cache_path"]])  # one archive, listed once

    def test_source_cache_record_is_bound_to_this_lock(self):
        record = deploy.load(HERE / "source-cache-verification.json")
        resolved = [c["id"] for c in LOCK["components"] if c["source_archive_sha256"] is not None]
        self.assertEqual(record["components"], resolved)
        self.assertEqual(record["entries"], len(deploy.cache_entries(LOCK, resolved, include_core=False)))
        self.assertEqual(record["source_lock_sha256"], deploy.sha(HERE / "sources.lock.json"))
        self.assertEqual((record["status"], record["includes_core"], record["hardware_ready"]), ("CACHE_BYTES_VERIFIED", False, False))
        pins = deploy.load(HERE / "extra-pins.json")
        for ref in pins["refs"]:
            self.assertRegex(ref["sha"] or "", "^[0-9a-f]{40}$", ref["repo"])

    def test_documented_release_digests_stay_outside_the_core_cache(self):
        documented = LOCK["documented_artifacts"]
        core = {e["path"] for e in deploy.cache_entries(LOCK, [], include_core=True)}
        self.assertEqual({a["name"] for a in documented} & {Path(p).name for p in core}, set())
        for item in documented:
            self.assertTrue(item["digest_source"].startswith("https://api.github.com/repos/radxa-pkg/"), item["name"])
            self.assertTrue(item["url"].endswith("/" + item["name"]) and item["cache_path"] == "debs/documented/" + item["name"])
            self.assertIn("release asset digest", item["verification"])
        self.assertIsNone(LOCK["phase0"]["selection"])  # candidates only: the Phase 0 matrix still decides
        self.assertEqual({a["name"].split("_")[1] for a in documented if a["name"].startswith("radxa-firmware-qcs6490")},
                         {c.split()[-1] for c in LOCK["phase0"]["firmware_candidates"]})

    def test_deploy_check_counts_one_unresolved_archive(self):
        with patch("vendor_patch.check_fixtures", return_value=[]):
            self.assertEqual(deploy.check()["unresolved_source_archives"], 1)


class CacheEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-cache-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def debian_lock(self):
        lock = copy.deepcopy(LOCK)
        component = next(c for c in lock["components"] if c["id"] == "chrony")
        files = {"chrony_9-1.dsc": b"dsc", "chrony_9.orig.tar.gz": b"orig", "chrony_9-1.debian.tar.xz": b"debian"}
        component["debian_source"]["files"] = [{"name": n, "sha256": sha(d), "size": len(d)} for n, d in files.items()]
        component["source_archive_sha256"] = sha(b"dsc")
        component["source_cache_path"] = "sources/chrony/chrony_9-1.dsc"
        component["binary_debs"] = [{"package": "chrony", "version": "9-1", "architecture": "arm64", "filename": "pool/main/c/chrony/chrony_9-1_arm64.deb",
                                     "sha256": sha(b"deb"), "size": 3}]
        for name, data in files.items():
            (self.root / "sources/chrony").mkdir(parents=True, exist_ok=True)
            (self.root / "sources/chrony" / name).write_bytes(data)
        (self.root / "debs/chrony").mkdir(parents=True)
        (self.root / "debs/chrony/chrony_9-1_arm64.deb").write_bytes(b"deb")
        return lock, component

    def test_debian_pin_needs_dsc_tarballs_and_debs(self):
        lock, component = self.debian_lock()
        entries = deploy.cache_entries(lock, ["chrony"], include_core=False)
        self.assertEqual(sorted(e["path"] for e in entries), ["debs/chrony/chrony_9-1_arm64.deb", "sources/chrony/chrony_9-1.debian.tar.xz",
                                                              "sources/chrony/chrony_9-1.dsc", "sources/chrony/chrony_9.orig.tar.gz"])
        base = lock["apt_snapshot"]["archive"] + "/" + lock["apt_snapshot"]["timestamp"] + "/"
        self.assertIn(base + "pool/main/c/chrony/chrony_9-1_arm64.deb", [e["url"] for e in entries])
        with patch.object(deploy, "load", return_value=lock):
            self.assertEqual(deploy.verify_cache(self.root, ["chrony"], include_core=False)["entries"], 4)
            (self.root / "debs/chrony/chrony_9-1_arm64.deb").write_bytes(b"DEB")
            with self.assertRaisesRegex(deploy.DeploymentError, "digest/size differs"):
                deploy.verify_cache(self.root, ["chrony"], include_core=False)
        component["source_archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(deploy.DeploymentError, "inconsistent"):
            deploy.cache_entries(lock, ["chrony"], include_core=False)

    def test_unresolved_and_conflicting_pins_fail_closed(self):
        lock = copy.deepcopy(LOCK)
        qairt = next(c for c in lock["components"] if c["id"] == "qairt")
        with self.assertRaisesRegex(deploy.DeploymentError, "unresolved"):
            deploy.cache_entries(lock, ["qairt"], include_core=False)
        qairt.update(commit="a" * 40, ref_verified=True)
        with patch.object(deploy, "load", return_value=lock), self.assertRaisesRegex(deploy.DeploymentError, "SHA256 unresolved"):
            deploy.verify_cache(self.root, ["qairt"], include_core=False)
        uart = next(c for c in lock["components"] if c["id"] == "la9310-uart")
        uart["source_archive_size"] += 1
        with self.assertRaisesRegex(deploy.DeploymentError, "two locked hashes"):
            deploy.cache_entries(lock, ["limesuiteng", "la9310-uart"], include_core=False)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-fetch-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "upstream.bin"
        self.data = os.urandom(3 * fetch_sources.CHUNK + 17)  # several streamed chunks
        self.source.write_bytes(self.data)
        self.url = self.source.as_uri()

    def test_locked_bytes_stream_into_place_and_are_reused(self):
        target = self.root / "cache/sources/x.tar.gz"
        first = fetch_sources.download(self.url, target, sha(self.data), len(self.data))
        self.assertEqual((first["sha256"], first["size"], first["cached"]), (sha(self.data), len(self.data), False))
        self.assertTrue(fetch_sources.download(self.url, target, sha(self.data), len(self.data))["cached"])
        self.assertEqual(target.read_bytes(), self.data)

    def test_wrong_or_oversized_bytes_never_reach_the_cache(self):
        target = self.root / "cache/x"
        with self.assertRaisesRegex(fetch_sources.FetchError, "differ from the lock"):
            fetch_sources.download(self.url, target, "0" * 64, len(self.data))
        with self.assertRaisesRegex(fetch_sources.FetchError, "exceeds the locked size"):
            fetch_sources.download(self.url, target, sha(self.data), len(self.data) - 1)
        with self.assertRaisesRegex(fetch_sources.FetchError, "max-bytes"):
            fetch_sources.download(self.url, target, max_bytes=10)
        self.assertEqual(list((self.root / "cache").iterdir()), [])  # no partial or temporary file left
        measured = fetch_sources.download(self.url, self.root / "acquired", max_bytes=len(self.data))
        self.assertEqual((measured["sha256"], measured["md5"]), (sha(self.data), hashlib.md5(self.data).hexdigest()))

    def test_fetch_uses_the_shared_entry_list(self):
        lock = copy.deepcopy(LOCK)
        rtl = next(c for c in lock["components"] if c["id"] == "rtlsdr")
        rtl.update(source_archive_url=self.url, source_archive_sha256=sha(self.data), source_archive_size=len(self.data))
        lock["documented_artifacts"] = [dict(lock["documented_artifacts"][0], url=self.url, sha256=sha(self.data), size=len(self.data))]
        result = fetch_sources.fetch(self.root / "cache", ["rtlsdr"], include_core=False, lock=lock)
        self.assertEqual((result["entries"], result["downloaded"], result["unresolved_in_lock"]), (1, 1, ["qairt"]))
        with_documented = fetch_sources.fetch(self.root / "cache", ["rtlsdr"], include_core=False, lock=lock, documented=True)
        self.assertEqual((with_documented["entries"], with_documented["downloaded"]), (2, 1))
        with patch.object(deploy, "load", return_value=lock):
            self.assertEqual(deploy.verify_cache(self.root / "cache", ["rtlsdr"], include_core=False)["status"], "CACHE_BYTES_VERIFIED")
        with self.assertRaisesRegex(fetch_sources.FetchError, "unresolved"):
            fetch_sources.fetch(self.root / "cache", ["qairt"], include_core=False, lock=lock)
        rtl["source_cache_path"] = "../escape.tar.gz"
        with self.assertRaisesRegex(fetch_sources.FetchError, "unsafe cache path"):
            fetch_sources.fetch(self.root / "cache", ["rtlsdr"], include_core=False, lock=lock)


@unittest.skipUnless(shutil.which("git"), "git not available")
class GitTreeTests(unittest.TestCase):
    def test_archive_tree_equals_git_tree_with_modes_symlinks_and_gitlinks(self):
        with tempfile.TemporaryDirectory(prefix="srrx-tree-test-") as temporary:
            repo = Path(temporary) / "repo"
            (repo / "src/sub").mkdir(parents=True)
            (repo / "README").write_text("readme\n", encoding="utf-8")
            (repo / "src/tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (repo / "src/sub/b.c").write_text("int b;\n", encoding="utf-8")
            (repo / "src.c").write_text("int a;\n", encoding="utf-8")  # sorts between "src" files and the "src/" tree
            env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@invalid",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@invalid")
            def git(*args, data=None):
                return subprocess.run(["git", "-C", str(repo)] + list(args), env=env, input=data, capture_output=True, text=True,
                                      check=True).stdout.strip()
            git("init", "-q")
            git("config", "core.autocrlf", "false")
            git("add", ".")
            git("update-index", "--chmod=+x", "src/tool.sh")
            # A symlink and a submodule entered straight into the index, independent of the filesystem.
            git("update-index", "--add", "--cacheinfo", "120000," + git("hash-object", "-w", "--stdin", data="README") + ",link")
            git("update-index", "--add", "--cacheinfo", "160000," + "1" * 40 + ",vendor/lib")
            git("commit", "-q", "-m", "fixture")
            tree = git("rev-parse", "HEAD^{tree}")
            archive = Path(temporary) / "a.tar.gz"
            subprocess.run(["git", "-C", str(repo), "archive", "--format=tar.gz", "--prefix=root/", "-o", str(archive), "HEAD"], env=env, check=True)
            self.assertEqual(fetch_sources.git_tree_sha1(archive, {"vendor/lib": "1" * 40}), tree)
            with self.assertRaisesRegex(fetch_sources.FetchError, "without a locked gitlink"):
                fetch_sources.git_tree_sha1(archive)
            self.assertNotEqual(fetch_sources.git_tree_sha1(archive, {"vendor/lib": "2" * 40}), tree)


@unittest.skipUnless(GPG, "gpg/gpgv not available (SRRX_RELEASE_BUILDER=1 makes this a failure)")
class SignedSnapshotTests(unittest.TestCase):
    """resolve-debian/verify-debian against a file:// snapshot signed by a throwaway key."""

    @classmethod
    def setUpClass(cls):
        cls.keys = Keys()
        cls.fpr = cls.keys.new_key("SR-RX snapshot test key")

    @classmethod
    def tearDownClass(cls):
        cls.keys.close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-snapshot-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.keyring = self.root / "archive.gpg"
        self.keys.export(self.fpr, self.keyring)

    def snapshot(self, version="4.5-1ubuntu4.2"):
        base = self.root / "snapshot/20990101T000000Z"
        pool = base / "pool/main/c/chrony"
        pool.mkdir(parents=True)
        files = {"chrony_%s.dsc" % version: b"dsc bytes", "chrony_4.5.orig.tar.gz": b"orig bytes", "chrony_%s.debian.tar.xz" % version: b"deb src"}
        for name, data in files.items():
            (pool / name).write_bytes(data)
        deb = b"chrony binary"
        (pool / ("chrony_%s_arm64.deb" % version)).write_bytes(deb)
        sources = ("Package: chrony\nVersion: %s\nDirectory: pool/main/c/chrony\nChecksums-Sha256:\n" % version
                   + "".join(" %s %d %s\n" % (sha(d), len(d), n) for n, d in files.items()))
        packages = ("Package: chrony\nVersion: %s\nArchitecture: arm64\nFilename: pool/main/c/chrony/chrony_%s_arm64.deb\nSize: %d\nSHA256: %s\n\n"
                    "Package: other\nSource: other\nVersion: 1\nArchitecture: arm64\nFilename: pool/main/o/other_1_arm64.deb\nSize: 1\nSHA256: %s\n"
                    % (version, version, len(deb), sha(deb), "0" * 64))
        for suite in LOCK["apt_snapshot"]["suites"]:
            dist = base / "dists" / suite
            indices = {}
            for area in LOCK["apt_snapshot"]["areas"]:
                text_s = sources if (suite, area) == ("noble-updates", "main") else ""
                text_p = packages if (suite, area) == ("noble-updates", "main") else ""
                for relative, text in ((area + "/source/Sources.xz", text_s), (area + "/binary-arm64/Packages.xz", text_p)):
                    (dist / relative).parent.mkdir(parents=True, exist_ok=True)
                    (dist / relative).write_bytes(lzma.compress(text.encode()))
                    indices[relative] = (dist / relative).read_bytes()
            release = "Origin: Ubuntu\nSuite: %s\nCodename: noble\nSHA256:\n%s" % (suite, "".join(" %s %d %s\n" % (sha(d), len(d), r) for r, d in indices.items()))
            (dist / "InRelease").write_bytes(self.keys.clearsign(self.fpr, release))
        lock = copy.deepcopy(LOCK)
        lock["apt_snapshot"].update(archive=(self.root / "snapshot").as_uri(), timestamp="20990101T000000Z", signing_fingerprints=[self.fpr])
        return lock

    def test_resolution_follows_the_signed_chain_and_verify_compares_with_the_lock(self):
        lock = self.snapshot()
        derived = fetch_sources.resolve_debian(lock, "chrony", self.keyring, self.root / "work")
        self.assertEqual((derived["debian_source"]["suite"], [d["package"] for d in derived["binary_debs"]]), ("noble-updates", ["chrony"]))
        self.assertEqual(derived["source_cache_path"], "sources/chrony/chrony_4.5-1ubuntu4.2.dsc")
        chrony = next(c for c in lock["components"] if c["id"] == "chrony")
        for key in ("debian_source", "binary_debs", "source_archive_sha256", "source_cache_path"):
            chrony[key] = derived[key]
        lock["apt_snapshot"]["releases"], lock["apt_snapshot"]["indices"] = derived["releases"], derived["indices"]
        self.assertEqual(fetch_sources.verify_debian(lock, self.keyring, self.root / "work2", ["chrony"])["status"], "DEBIAN_PINS_MATCH_SIGNED_SNAPSHOT")
        chrony["binary_debs"][0]["sha256"] = "1" * 64
        with self.assertRaisesRegex(fetch_sources.FetchError, "differs from the lock"):
            fetch_sources.verify_debian(lock, self.keyring, self.root / "work3", ["chrony"])

    def test_unsigned_or_tampered_index_is_refused(self):
        lock = self.snapshot()
        other = self.root / "other.gpg"
        other_keys = Keys()
        try:
            other_keys.export(other_keys.new_key("other"), other)
        finally:
            other_keys.close()
        with self.assertRaisesRegex(deploy.DeploymentError, "not a good signature"):
            fetch_sources.resolve_debian(lock, "chrony", other, self.root / "w1")
        index = self.root / "snapshot/20990101T000000Z/dists/noble-updates/main/source/Sources.xz"
        index.write_bytes(index.read_bytes() + b"x")
        with self.assertRaisesRegex(fetch_sources.FetchError, "exceeds the locked size|differ from the lock"):
            fetch_sources.resolve_debian(lock, "chrony", self.keyring, self.root / "w2")
        with self.assertRaisesRegex(fetch_sources.FetchError, "not in the pinned snapshot"):
            fetch_sources.resolve_debian(self.snapshot_without_version(), "chrony", self.keyring, self.root / "w3")

    def snapshot_without_version(self):
        shutil.rmtree(self.root / "snapshot")
        return self.snapshot(version="4.5-1ubuntu9")


if __name__ == "__main__":
    unittest.main()
