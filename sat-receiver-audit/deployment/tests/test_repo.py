"""deploy.verify_repo with a throwaway key generated inside each test, never a release key.

The repository is synthetic (hand-written Release/Packages, opaque .deb bytes): verify_repo
checks signatures, indexes, hashes and bindings, not package contents. A missing gpg skips
these tests, except with SRRX_RELEASE_BUILDER=1, where it fails like deployment/test.sh.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy  # noqa: E402

GPG = shutil.which("gpg") and shutil.which("gpgv") and os.name == "posix"
if not GPG and os.environ.get("SRRX_RELEASE_BUILDER") == "1":
    raise RuntimeError("BLOCKED: release builder lacks gpg/gpgv for the signed repository tests")
LOCK = deploy.load(HERE / "sources.lock.json")
RTL = next(c for c in LOCK["components"] if c["id"] == "rtlsdr")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Keys:
    """Ephemeral GnuPG home (short path: the agent socket must fit in sun_path)."""

    def __init__(self):
        self.home = tempfile.mkdtemp(prefix="srrx-gpg-", dir="/tmp" if os.path.isdir("/tmp") else None)
        os.chmod(self.home, 0o700)
        self.env = dict(os.environ, GNUPGHOME=self.home)

    def gpg(self, *args, data=None):
        return subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", ""] + list(args),
                              env=self.env, input=data, capture_output=True, check=True, timeout=120)

    def new_key(self, uid):
        self.gpg("--quick-gen-key", uid, "ed25519", "sign", "1d")
        colons = self.gpg("--with-colons", "--list-keys", uid).stdout.decode()
        return next(line.split(":")[9] for line in colons.splitlines() if line.startswith("fpr:"))

    def export(self, fingerprint, path):
        Path(path).write_bytes(self.gpg("--export", fingerprint).stdout)

    def clearsign(self, fingerprint, text):
        return self.gpg("--local-user", fingerprint, "--digest-algo", "SHA512", "--clearsign", data=text.encode()).stdout

    def close(self):
        subprocess.run(["gpgconf", "--kill", "gpg-agent"], env=self.env, capture_output=True)
        shutil.rmtree(self.home, ignore_errors=True)


@unittest.skipUnless(GPG, "gpg/gpgv not available (SRRX_RELEASE_BUILDER=1 makes this a failure)")
class SignedRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = Keys()
        cls.fpr = cls.keys.new_key("SR-RX unit test key - not for release")
        cls.other = cls.keys.new_key("SR-RX unit test other key")

    @classmethod
    def tearDownClass(cls):
        cls.keys.close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-repo-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.keyring = self.root / "srrx-lab.gpg"
        self.keys.export(self.fpr, self.keyring)
        self.wrong = self.root / "other.gpg"
        self.keys.export(self.other, self.wrong)
        self.sources = HERE / "repo/srrx-lab.sources"
        self.packages = [("librtlsdr2", RTL["version"], b"synthetic librtlsdr2 deb bytes"),
                         ("librtlsdr-dev", RTL["version"], b"synthetic librtlsdr-dev deb bytes")]

    def publish(self, packages=None, origin="srrx-lab", signer=None, extra_release=""):
        repo = self.root / "repo"
        if repo.exists():
            shutil.rmtree(repo)
        dist = repo / "dists/noble-lab"
        index = dist / "main/binary-arm64"
        index.mkdir(parents=True)
        stanzas = []
        for name, version, data in packages or self.packages:
            filename = "pool/main/l/%s/%s_%s_arm64.deb" % (name, name, version)
            (repo / filename).parent.mkdir(parents=True, exist_ok=True)
            (repo / filename).write_bytes(data)
            stanzas.append("Package: %s\nVersion: %s\nArchitecture: arm64\nFilename: %s\nSize: %d\nSHA256: %s\n"
                           % (name, version, filename, len(data), sha(data)))
        text = "\n".join(stanzas).encode()
        (index / "Packages").write_bytes(text)
        (index / "Packages.gz").write_bytes(gzip.compress(text, mtime=0))
        (index / "Release").write_bytes(b"Archive: noble-lab\nComponent: main\nArchitecture: arm64\n")
        listed = "".join(" %s %d %s\n" % (sha((dist / p).read_bytes()), (dist / p).stat().st_size, p)
                         for p in ("main/binary-arm64/Packages", "main/binary-arm64/Packages.gz", "main/binary-arm64/Release"))
        release = ("Origin: %s\nLabel: SR-RX lab +labN builds\nSuite: noble-lab\nCodename: noble-lab\nDate: Sat, 24 Oct 2026 00:00:00 UTC\n"
                   "Architectures: arm64\nComponents: main\n%sSHA256:\n%s" % (origin, extra_release, listed))
        (dist / "InRelease").write_bytes(self.keys.clearsign(signer or self.fpr, release))
        return repo

    def record(self, packages=None, **overrides):
        entries = []
        for name, version, data in packages or self.packages:
            entries.append({"package": name, "version": version, "architecture": "arm64", "filename": "%s_%s_arm64.deb" % (name, version),
                            "sha256": sha(data), "size": len(data), "build_manifest_sha256": "0" * 64})
        record = {"schema_version": 1, "kind": "srrx_lab_build_record", "status": "CI_BUILT_UNREVIEWED", "component": "rtlsdr",
                  "version": RTL["version"], "recipe_sha256": deploy.sha(HERE / "recipes/rtlsdr/recipe.json"),
                  "source_archive_sha256": RTL["source_archive_sha256"], "apt_snapshot": LOCK["apt_snapshot"]["timestamp"],
                  "build_environment": {}, "packages": entries, "checks": [], "hardware_ready": False}
        record.update(overrides)
        path = self.root / ("record-%d.json" % len(list(self.root.glob("record-*.json"))))
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def verify(self, repo, records, **kwargs):
        arguments = dict(repo=repo, keyring=self.keyring, fingerprint=self.fpr, build_records=records, sources_entry=self.sources)
        arguments.update(kwargs)
        return deploy.verify_repo(**arguments)

    def refused(self, needle, repo, records, **kwargs):
        with self.assertRaisesRegex(deploy.DeploymentError, needle):
            self.verify(repo, records, **kwargs)

    def test_signed_repository_matching_its_build_records_passes(self):
        repo, record = self.publish(), self.record()
        result = self.verify(repo, [record], inrelease_sha256=deploy.sha(repo / "dists/noble-lab/InRelease"))
        self.assertEqual((result["status"], result["packages"], result["hardware_ready"]), ("SIGNED_REPOSITORY_MATCHES_BUILD_RECORDS", 2, False))
        self.assertEqual(result["build_records"], [{"path": str(record), "sha256": deploy.sha(record)}])
        self.assertEqual(result["signing_fingerprint"], self.fpr)

    def test_tampered_index_pool_and_signature_are_refused(self):
        record = self.record()
        repo = self.publish()
        index = repo / "dists/noble-lab/main/binary-arm64/Packages"
        index.write_bytes(index.read_bytes() + b"\n")
        self.refused("index differs from the signed Release", repo, [record])
        repo = self.publish()
        (repo / "pool/main/l/extra").mkdir(parents=True)
        (repo / "pool/main/l/extra/extra_1.0+lab1_arm64.deb").write_bytes(b"unlisted")
        self.refused("pool holds a file", repo, [record])
        repo = self.publish()
        deb = next(repo.rglob("librtlsdr2_*.deb"))
        deb.write_bytes(b"X" * deb.stat().st_size)
        self.refused("pool .deb differs", repo, [record])
        repo = self.publish()
        self.refused("not a good signature", repo, [record], keyring=self.wrong)
        self.refused("not a good signature", self.publish(signer=self.other), [record])
        repo = self.publish()
        (repo / "dists/noble-lab/stray").write_bytes(b"not in Release")
        self.refused("not covered by the signed Release", repo, [record])
        repo = self.publish()
        inrelease = repo / "dists/noble-lab/InRelease"
        inrelease.write_bytes(inrelease.read_bytes().replace(b"Codename: noble-lab", b"Codename: noble-lob"))
        self.refused("not a good signature", repo, [record])

    def test_old_or_foreign_publications_are_refused(self):
        record = self.record()
        repo = self.publish()
        self.refused("InRelease differs from the reviewed release record", repo, [record], inrelease_sha256="0" * 64)
        self.refused("foreign or unexpected repository origin", self.publish(origin="Ubuntu"), [record])

    def test_every_package_needs_a_record_bound_to_the_locked_source(self):
        repo = self.publish()
        self.refused("not one of the build records", repo, [])
        self.refused("not one of the build records", repo, [self.record(packages=self.packages[:1])])
        self.refused("not bound to the locked component source", repo, [self.record(source_archive_sha256="1" * 64)])
        self.refused("not bound to the locked component source", repo, [self.record(version="2.0.1-2build1")])
        self.refused("not bound to the locked component source", repo, [self.record(apt_snapshot="20240101T000000Z")])
        self.refused("not bound to the locked component source", repo, [self.record(component="made-up")])

    def test_kernel_firmware_policy_and_non_lab_packages_are_refused(self):
        for name, needle in (("linux-image-6.18.2-4-qcom", "kernel, bootloader"), ("edk2-qcs6490", "kernel, bootloader"),
                             ("radxa-firmware-qcs6490", "kernel, bootloader"), ("wsjtx", "receive-only policy forbids")):
            packages = [(name, RTL["version"], b"synthetic " + name.encode())]
            self.refused(needle, self.publish(packages=packages), [self.record(packages=packages)])
        # The record must carry the locked +labN version, so the version rule is shown on its own.
        with patch.object(deploy, "LAB_BUILD", re.compile(r"(?!)")):
            self.refused("not a \\+labN build", self.publish(), [self.record()])

    def test_held_package_change_and_apt_entry_without_signed_by_are_refused(self):
        repo, record = self.publish(), self.record()
        status = self.root / "status"
        status.write_text("Package: librtlsdr2\nStatus: hold ok installed\nVersion: 2.0.3-0+lab0\n\n"
                          "Package: chrony\nStatus: install ok installed\nVersion: 1\n", encoding="utf-8")
        self.refused("held package", repo, [record], target_status=status)
        status.write_text("Package: librtlsdr2\nStatus: hold ok installed\nVersion: " + RTL["version"] + "\n", encoding="utf-8")
        self.assertEqual(self.verify(repo, [record], target_status=status)["packages"], 2)
        entry = self.root / "no-signed-by.sources"
        entry.write_text("Types: deb\nURIs: file:/srv/srrx-repo/lab\nSuites: noble-lab\nComponents: main\n", encoding="utf-8")
        self.refused("Signed-By", repo, [record], sources_entry=entry)
        entry.write_text(self.sources.read_text(encoding="utf-8").replace("/usr/share/keyrings/srrx-lab.gpg", "/tmp/other.gpg"), encoding="utf-8")
        self.refused("Signed-By", repo, [record], sources_entry=entry)

    def test_unpinned_fingerprint_is_refused(self):
        repo, record = self.publish(), self.record()
        self.refused("40-hex fingerprint", repo, [record], fingerprint="SR-RX")
        self.refused("not a good signature", repo, [record], fingerprint=self.other)


class ReleaseGuardRepositoryTests(unittest.TestCase):
    """release_guard verifies the signed repository instead of hashing one snapshot file."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-guard-repo-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def guard(self, snapshot):
        devices, manifest, record_file = self.root / "devices.json", self.root / "build-manifest.json", self.root / "record.json"
        devices.write_text("{}", encoding="utf-8")
        manifest.write_text("{}", encoding="utf-8")
        record_file.write_text('{"kind": "record"}', encoding="utf-8")
        release = {"schema_version": 1, "status": "REVIEWED", "hardware_unit_id": "SRRX-UNIT-TEST", "device_bindings_sha256": deploy.sha(devices),
                   "build_manifest_sha256": deploy.sha(manifest), "source_lock_sha256": deploy.sha(HERE / "sources.lock.json"),
                   "profile": "controller", "base_image_sha256": LOCK["target"]["base_image_sha256"], "offline_snapshot": snapshot(record_file)}
        (self.root / "release.json").write_text(json.dumps(release), encoding="utf-8")
        sys.path.insert(0, str(deploy.PROJECT / "software"))
        import srrx.commissioning as commissioning
        calls = []
        with patch.object(deploy, "validate_devices", return_value={}), patch.object(deploy, "doctor", return_value={"issues": []}), \
                patch.object(commissioning, "load_acceptance", return_value={"hardware_unit_id": "SRRX-UNIT-TEST"}), \
                patch.object(deploy, "verify_repo", side_effect=lambda *a: calls.append(a)), \
                patch.object(deploy, "verify_cache"), patch.object(deploy, "verify_build"):
            result = deploy.release_guard(devices, self.root / "acceptance.json", self.root / "release.json", manifest, self.root / "cache")
        return result, calls

    def test_guard_calls_verify_repo_with_the_pinned_record(self):
        snapshot = lambda record: {"status": "REVIEWED", "repo": "/srv/srrx-repo/lab", "keyring": "/usr/share/keyrings/srrx-lab.gpg",
                                   "signing_fingerprint": "A" * 40, "inrelease_sha256": "b" * 64,
                                   "sources_entry": "/etc/apt/sources.list.d/srrx-lab.sources",
                                   "build_records": [{"path": str(record), "sha256": deploy.sha(record)}]}
        result, calls = self.guard(snapshot)
        self.assertEqual(result["status"], "RELEASE_GUARDS_MATCH")
        repo, keyring, fingerprint, records, sources, pinned, status = calls[0]
        self.assertEqual((repo, fingerprint, pinned, status), ("/srv/srrx-repo/lab", "A" * 40, "b" * 64, Path("/var/lib/dpkg/status")))
        self.assertEqual(len(records), 1)

    def test_hash_only_snapshot_and_changed_record_are_refused(self):
        with self.assertRaisesRegex(deploy.DeploymentError, "offline package snapshot"):
            self.guard(lambda record: {"status": "REVIEWED", "path": str(record), "sha256": deploy.sha(record)})
        changed = lambda record: {"status": "REVIEWED", "repo": "/r", "keyring": "/k", "signing_fingerprint": "A" * 40, "inrelease_sha256": None,
                                  "sources_entry": "/s", "build_records": [{"path": str(record), "sha256": "0" * 64}]}
        with self.assertRaisesRegex(deploy.DeploymentError, "build record differs"):
            self.guard(changed)
        empty = lambda record: dict(changed(record), build_records=[])
        with self.assertRaisesRegex(deploy.DeploymentError, "not bound"):
            self.guard(empty)

    def test_template_is_open_and_names_the_installed_paths(self):
        template = deploy.load(HERE / "release.template.json")["offline_snapshot"]
        self.assertEqual(template["status"], "OPEN")
        policy = deploy.load(deploy.REPO_POLICY)
        self.assertEqual(template["keyring"], policy["keyring_path"])
        entry = deploy.deb822((HERE / "repo/srrx-lab.sources").read_text(encoding="utf-8"), "sources")[0]
        self.assertEqual((entry["signed-by"], entry["suites"], entry["components"]), (policy["keyring_path"], policy["codename"], policy["component"]))
        self.assertTrue(template["sources_entry"].endswith("/" + "srrx-lab.sources"))


class RepositoryLayoutTests(unittest.TestCase):
    def test_lab_pref_is_the_structure_selftest_rx16_accepts(self):
        stanzas = deploy.deb822((HERE / "repo/lab.pref").read_text(encoding="utf-8"), "lab.pref")
        self.assertEqual([int(s["pin-priority"]) for s in stanzas], deploy.load(HERE / "receive-only-policy.json")["apt"]["pref_priorities"])
        self.assertEqual([s["pin"] for s in stanzas], ["release o=" + deploy.load(deploy.REPO_POLICY)["origin"], "release o=srrx-mirror", "origin *"])
        self.assertNotIn("<", (HERE / "repo/lab.pref").read_text(encoding="utf-8"))  # no placeholder (RX-16 apt_pin_origin_placeholder)

    def test_policy_keeps_kernel_bootloader_and_firmware_out_of_the_lab_repository(self):
        policy = deploy.load(deploy.REPO_POLICY)
        import fnmatch
        for name in ("linux-image-6.18.2-4-qcom", "linux-headers-radxa-dragon-q6a", "embloader", "systemd-boot-efi", "edk2-radxa-dragon-q6a",
                     "radxa-firmware-qcs6490", "fastrpc", "libcdsprpc1", "linux-firmware-dragonwing", "u-boot-menu", "qcom-qnn-sdk-v68"):
            self.assertTrue(any(fnmatch.fnmatchcase(name, g) for g in policy["never_in_lab_repo_globs"]), name)
        for name in ("librtlsdr2", "liblimesuiteng", "limesuiteng-soapysdr", "satdump", "labwc", "sdrangel"):
            self.assertFalse(any(fnmatch.fnmatchcase(name, g) for g in policy["never_in_lab_repo_globs"]), name)

    def test_publish_script_signs_without_valid_until_and_takes_names_from_the_policy(self):
        script = (HERE / "repo/publish.sh").read_text(encoding="utf-8")
        for needle in ('-origin="$origin"', '-distribution="$codename"', "-gpg-key=", "repo-policy.json", "-skip-contents"):
            self.assertIn(needle, script)
        self.assertNotIn("valid-until", script.lower().replace("no valid-until", ""))
        self.assertNotIn("--export-secret", script)
        conf = json.loads((HERE / "repo/aptly.conf.template.json").read_text(encoding="utf-8"))
        self.assertEqual((conf["architectures"], conf["gpgDisableSign"], conf["downloadSourcePackages"]), (["arm64"], False, False))

    def test_deb822_reader_fails_closed(self):
        self.assertEqual(deploy.deb822("A: 1\n B\n\nC: 2\n", "t"), [{"a": "1\nB"}, {"c": "2"}])
        for bad in ("A: 1\nA: 2\n", " lead\n", "no colon\n"):
            with self.assertRaises(deploy.DeploymentError):
                deploy.deb822(bad, "t")
        with self.assertRaisesRegex(deploy.DeploymentError, "malformed SHA256"):
            deploy.release_files({"sha256": "\n" + "a" * 64 + " 1 ../escape"}, "t")


if __name__ == "__main__":
    unittest.main()
