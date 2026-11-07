"""deploy.verify_repo with a throwaway key generated inside each test, never a release key.

The repository is synthetic (hand-written Release/Packages, small .deb files built here in
Python): verify_repo checks signatures, indexes, hashes, bindings and the named receive-only
content rules of each package's data tree. A missing gpg skips the signed tests, except with
SRRX_RELEASE_BUILDER=1, where it fails like deployment/test.sh; the .deb reader and content rules
are tested without gpg.
"""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
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
LIB = "usr/lib/aarch64-linux-gnu/"
# What build_recipe.package_manifest writes: verify_build refuses it as OPEN/unreviewed.
OPEN_MANIFEST = {"schema_version": 1, "status": "OPEN", "files": {}, "allowed_modules": [],
                 "source_audit": {"status": "OPEN", "report": {"path": None, "sha256": None}},
                 "tx_negative_tests": {"status": "OPEN", "report": {"path": None, "sha256": None}}}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_deb(files, links=None, compression="xz"):
    """A .deb (ar: debian-binary, control.tar.xz, data.tar.<compression>) like dpkg-deb writes:
    files {path: bytes}, links {path: target}, parent directories as ./ entries."""
    def tar(entries, mode):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode=mode) as archive:
            for name, data, target in entries:
                info = tarfile.TarInfo(name)
                if target is not None:
                    info.type, info.linkname = tarfile.SYMTYPE, target
                elif data is None:
                    info.type, info.mode = tarfile.DIRTYPE, 0o755
                else:
                    info.size, info.mode = len(data), 0o644
                archive.addfile(info, io.BytesIO(data) if data is not None and target is None else None)
        return buffer.getvalue()
    links = links or {}
    directories = sorted({"/".join(p.split("/")[:i]) for p in list(files) + list(links) for i in range(1, p.count("/") + 1)})
    entries = [("./", None, None)] + [("./" + d + "/", None, None) for d in directories]
    entries += [("./" + p, d, None) for p, d in sorted(files.items())] + [("./" + p, None, t) for p, t in sorted(links.items())]
    members = [("debian-binary", b"2.0\n"), ("control.tar.xz", tar([("./", None, None), ("./control", b"Package: x\n", None)], "w:xz")),
               ("data.tar." + compression, tar(entries, "w:" + compression))]
    out = b"!<arch>\n"
    for name, payload in members:
        out += (name.ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) + "100644".ljust(8) + str(len(payload)).ljust(10) + "`\n").encode()
        out += payload + (b"\n" if len(payload) % 2 else b"")
    return out


def rtl_deb(name):
    """Synthetic package data trees shaped like the real lab packages."""
    if name == "librtlsdr2":
        return make_deb({LIB + "librtlsdr.so.2.0.3": b"\x7fELF synthetic librtlsdr"}, {LIB + "librtlsdr.so.2": "librtlsdr.so.2.0.3"})
    return make_deb({"usr/include/rtl-sdr.h": b"/* synthetic header */\n"}, {LIB + "librtlsdr.so": "librtlsdr.so.2"})


class DebContentTests(unittest.TestCase):
    """The .deb reader and the receive-only content rules, without gpg."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-deb-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def deb(self, data, name="x.deb"):
        (self.root / name).write_bytes(data)
        return self.root / name

    def test_data_tree_is_read_and_extracted_in_python(self):
        deb = self.deb(rtl_deb("librtlsdr2"))
        tree = deploy.deb_data_tree(deb)
        self.assertEqual(tree, {"usr": "dir", "usr/lib": "dir", "usr/lib/aarch64-linux-gnu": "dir",
                                LIB + "librtlsdr.so.2.0.3": "file", LIB + "librtlsdr.so.2": "link"})
        if os.name == "posix":  # Windows without symlink rights makes tarfile copy the link target (a backwards seek)
            deploy.deb_data_tree(deb, self.root / "out")
            self.assertEqual((self.root / "out" / LIB / "librtlsdr.so.2.0.3").read_bytes(), b"\x7fELF synthetic librtlsdr")
            self.assertEqual(os.readlink(self.root / "out" / LIB / "librtlsdr.so.2"), "librtlsdr.so.2.0.3")
        self.assertEqual(deploy.deb_data_tree(self.deb(make_deb({"a/b": b"1"}, compression="gz"), "gz.deb")), {"a": "dir", "a/b": "file"})

    def test_unreadable_or_unsafe_debs_fail_closed(self):
        with self.assertRaisesRegex(deploy.DeploymentError, "not a .deb"):
            deploy.deb_data_tree(self.deb(b"synthetic opaque bytes"))
        with self.assertRaisesRegex(deploy.DeploymentError, "no data.tar"):
            deploy.deb_data_tree(self.deb(make_deb({"a": b"1"})[:80]))
        with self.assertRaisesRegex(deploy.DeploymentError, "unsafe"):
            deploy.deb_data_tree(self.deb(make_deb({"../escape": b"x"})))

    def test_lime_soapy_and_tx_tools_are_named_findings(self):
        self.assertEqual(deploy.lab_package_issues(deploy.deb_data_tree(self.deb(rtl_deb("librtlsdr2")))), [])
        self.assertEqual(deploy.lab_package_issues({LIB + "SoapySDR/modules0.8/librtlsdrSupport.so": "file"}), [])
        cases = {
            LIB + "liblimesuiteng.so.0.3-1": "RX-08 Lime runtime library",
            LIB + "liblimesuiteng.so": "RX-08 Lime runtime library",
            LIB + "SoapySDR/modules0.8/liblimesuitengSupport.so": "RX-06 Lime Soapy module",
            LIB + "SoapySDR/modules0.8/libhackrfSupport.so": "RX-06 Soapy module outside the allowlist",
            LIB + "SoapySDR/modules0.8/libremoteSupport.so": "RX-06 Soapy module outside the allowlist",
            LIB + "SoapySDR/modules0.9-0/librtlsdrSupport.so": "RX-06 SoapySDR 0.9",
            "usr/bin/rtl_tcp": "TX/control executable",
            "usr/bin/rigctld": "TX/control executable",
            "usr/lib/sdrangel/plugins/channeltx/libmodam.so": "TX/control executable or plugin",
        }
        for path, rule in cases.items():
            with self.subTest(path):
                issues = deploy.lab_package_issues({path: "file"})
                self.assertTrue(issues and issues[0].startswith(rule) and issues[0].endswith(path), issues)


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
        self.packages = [("librtlsdr2", RTL["version"], rtl_deb("librtlsdr2")),
                         ("librtlsdr-dev", RTL["version"], rtl_deb("librtlsdr-dev"))]

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

    def record(self, packages=None, manifests=None, **overrides):
        """A build record in a new directory, with a build manifest file per package (manifests
        {package: manifest}; default an OPEN placeholder) next to it, as lab_build.py writes them."""
        directory = self.root / ("records-%d" % len(list(self.root.glob("records-*"))))
        directory.mkdir()
        entries = []
        for name, version, data in packages or self.packages:
            manifest = directory / (name + ".build-manifest.json")
            manifest.write_text(json.dumps((manifests or {}).get(name, OPEN_MANIFEST)), encoding="utf-8")
            entries.append({"package": name, "version": version, "architecture": "arm64", "filename": "%s_%s_arm64.deb" % (name, version),
                            "sha256": sha(data), "size": len(data), "build_manifest_sha256": deploy.sha(manifest)})
        patch_sha = deploy.sha(HERE / "patches/rtlsdr-rx-only.patch")
        record = {"schema_version": 1, "kind": "srrx_lab_build_record", "status": "CI_BUILT_UNREVIEWED", "component": "rtlsdr",
                  "version": RTL["version"], "recipe_sha256": deploy.sha(HERE / "recipes/rtlsdr/recipe.json"),
                  "source_archive_sha256": RTL["source_archive_sha256"], "apt_snapshot": LOCK["apt_snapshot"]["timestamp"],
                  "build_environment": {"patch_receipt": {"component": "rtlsdr", "patch_sha256": patch_sha}},
                  "packages": entries, "checks": [], "hardware_ready": False}
        record.update(overrides)
        path = directory / "rtlsdr.build-record.json"
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
            packages = [(name, RTL["version"], make_deb({"usr/share/doc/%s/README" % name: b"synthetic"}))]
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

    def test_package_contents_follow_the_receive_only_rules_whatever_the_name(self):
        # The real liblimesuiteng/limesuiteng-soapysdr trees (CI run 40114793589), and a renamed copy.
        for name, files in (("liblimesuiteng", {LIB + "liblimesuiteng.so.0.3-1": b"\x7fELF lime"}),
                            ("limesuiteng-soapysdr", {LIB + "SoapySDR/modules0.8/liblimesuitengSupport.so": b"\x7fELF module"}),
                            ("librtlsdr-extras", {LIB + "liblimesuiteng.so.0.3-1": b"\x7fELF lime"}),
                            ("soapysdr-module-x", {LIB + "SoapySDR/modules0.8/libremoteSupport.so": b"\x7fELF remote"}),
                            ("librtlsdr-tools", {"usr/bin/rtl_tcp": b"\x7fELF tcp"})):
            packages = [(name, RTL["version"], make_deb(files))]
            with self.subTest(name):
                self.refused("receive-only policy refuses the contents of " + name, self.publish(packages=packages), [self.record(packages=packages)])
        self.refused("not a .deb", self.publish(packages=[("librtlsdr2", RTL["version"], b"opaque")]),
                     [self.record(packages=[("librtlsdr2", RTL["version"], b"opaque")])])

    def test_record_needs_the_reviewed_recipe_and_patch_of_this_tree(self):
        repo = self.publish()
        self.refused("another recipe", repo, [self.record(recipe_sha256="0" * 64)])
        self.refused("patch differs", repo, [self.record(build_environment={"patch_receipt": {"patch_sha256": "0" * 64}})])
        self.refused("patch differs", repo, [self.record(build_environment={})])

    def reviewed_manifest(self, files, links):
        """The REVIEWED verify_build manifest a reviewer would write for this package tree."""
        with tempfile.TemporaryDirectory(prefix="srrx-manifest-") as temporary:
            (Path(temporary) / "p.deb").write_bytes(make_deb(files, links))
            deploy.deb_data_tree(Path(temporary) / "p.deb", Path(temporary) / "root")
            root = Path(temporary) / "root"
            listed = {p.relative_to(root).as_posix(): deploy.sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
        doc = "usr/share/doc/librtlsdr2/"
        evidence = {name: {"status": "PASS", "report": {"path": doc + name + ".json", "sha256": listed.get(doc + name + ".json")}}
                    for name in ("source_audit", "tx_negative_tests")}
        return {"schema_version": 1, "status": "REVIEWED", "files": listed, "allowed_modules": sorted(f for f in listed if ".so" in f),
                **evidence}

    def test_release_path_needs_reviewed_records_and_verify_build_per_package(self):
        doc = "usr/share/doc/librtlsdr2/"
        files = {LIB + "librtlsdr.so.2.0.3": b"\x7fELF synthetic librtlsdr", doc + "source_audit.json": b'{"report": "synthetic source audit of the test"}\n',
                 doc + "tx_negative_tests.json": b'{"report": "synthetic TX negative tests of the test"}\n'}
        links = {LIB + "librtlsdr.so.2": "librtlsdr.so.2.0.3"}
        packages = [("librtlsdr2", RTL["version"], make_deb(files, links))]
        repo = self.publish(packages=packages)
        manifest = self.reviewed_manifest(files, links)
        record = self.record(packages=packages, manifests={"librtlsdr2": manifest}, status="REVIEWED")
        result = self.verify(repo, [record], release=True)
        self.assertEqual((result["status"], result["release_path"], result["packages"]), ("SIGNED_REPOSITORY_MATCHES_BUILD_RECORDS", True, 1))
        self.assertFalse(self.verify(repo, [self.record(packages=packages)])["release_path"])  # CI path: CI records are enough
        self.refused("REVIEWED build record", repo, [self.record(packages=packages, manifests={"librtlsdr2": manifest})], release=True)
        self.refused("OPEN/unreviewed", repo, [self.record(packages=packages, status="REVIEWED")], release=True)
        changed = self.record(packages=packages, manifests={"librtlsdr2": manifest}, status="REVIEWED")
        (changed.parent / "librtlsdr2.build-manifest.json").write_text(json.dumps(dict(manifest, files={})), encoding="utf-8")
        self.refused("build manifest differs from the build record", repo, [changed], release=True)
        other = dict(manifest, files=dict(manifest["files"], **{LIB + "librtlsdr.so.2.0.3": "0" * 64}))
        self.refused("staged file hashes", repo, [self.record(packages=packages, manifests={"librtlsdr2": other}, status="REVIEWED")], release=True)
        # A -dev package links into the runtime package: it cannot pass verify_build on its own.
        dev = [("librtlsdr-dev", RTL["version"], rtl_deb("librtlsdr-dev"))]
        self.refused("not self-contained", self.publish(packages=dev),
                     [self.record(packages=dev, manifests={"librtlsdr-dev": self.reviewed_manifest({"usr/include/rtl-sdr.h": b"/* synthetic header */\n"}, {})},
                                  status="REVIEWED")], release=True)


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
                patch.object(deploy, "verify_repo", side_effect=lambda *a, **k: calls.append((a, k))), \
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
        (repo, keyring, fingerprint, records, sources, pinned, status), options = calls[0]
        self.assertEqual((repo, fingerprint, pinned, status), ("/srv/srrx-repo/lab", "A" * 40, "b" * 64, Path("/var/lib/dpkg/status")))
        self.assertEqual(len(records), 1)
        self.assertEqual(options, {"release": True})  # REVIEWED records and verify_build per package on this path

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


# --- W2 SW-BUILDER: the record binding of schema-2 recipes (listed patches, source member, recipe
# files) and the optional record_digests field. Synthetic deployment trees in temporary directories.
import copy  # noqa: E402
import importlib.util  # noqa: E402

FIXTURE = "srrx-fixture"
MEMBER = {"path": "superbuild-1.0/src/inner.tgz", "sha256": "c" * 64}


def v2_deployment(root, hook_out=True):
    """deployment/ stand-in: recipes/srrx-fixture/ with a recipe naming three listed patches, a
    source member, both hooks (the package hook writing {hook_out} unless hook_out is False) and a
    files/ copy, its check_recipe.py and files/. Returns the record a builder would write for it."""
    directory = root / "recipes" / FIXTURE
    (directory / "patches").mkdir(parents=True)
    (directory / "files").mkdir()
    (directory / "check_recipe.py").write_text("# synthetic hook\n", encoding="utf-8")
    (directory / "files/srrx-fixture.conf").write_text("# synthetic recipe file\n", encoding="utf-8")
    listed = []
    for index in range(1, 4):
        file = "patches/%04d-synthetic.patch" % index
        (directory / file).write_text("--- a/f%d\n+++ b/f%d\n@@ -1 +1 @@\n-a\n+b\n" % (index, index), encoding="utf-8")
        listed.append({"file": file, "sha256": deploy.sha(directory / file), "strip": 1, "targets": {"f%d" % index: "0" * 40},
                       "kind": "lab", "summary": "synthetic"})
    hooks = {"source_check": ["python3", "-I", "{recipe}/check_recipe.py", "verify-source", "--source", "{src}"],
             "package": ["python3", "-I", "{recipe}/check_recipe.py", "package", "--root", "{destdir}"]
             + (["--manifest", "{hook_out}"] if hook_out else [])}
    install = {"cmake_install": False, "make_install": True, "copy": [{"from": "{recipe}/files/srrx-fixture.conf", "to": "etc/srrx-fixture"}]}
    (directory / "recipe.json").write_text(json.dumps({"schema_version": 2, "component": FIXTURE,
                                                       "source": {"patch": None, "patches": listed, "member": MEMBER},
                                                       "install": install, "hooks": hooks}), encoding="utf-8")
    receipts = [dict(entry, after={t: "1" * 40 for t in entry["targets"]}) for entry in listed]
    for receipt in receipts:
        del receipt["kind"], receipt["summary"]
    script = deploy.sha(directory / "check_recipe.py")
    ran = [{"hook": name, "argv": list(argv), "script_sha256": script, "status": "CI_PASS", "report": {"findings": [], "ok": True}}
           for name, argv in hooks.items()]
    if hook_out:
        ran[1].update(output=FIXTURE + ".package-hook.json", output_sha256="d" * 64)
    return {"component": FIXTURE, "recipe_sha256": deploy.sha(directory / "recipe.json"),
            "build_environment": {"patch_receipt": {"component": FIXTURE, "patch": None}, "patch_receipts": receipts,
                                  "source_member": dict(MEMBER), "hooks": ran,
                                  "recipe_files": {"check_recipe.py": script,
                                                   "files/srrx-fixture.conf": deploy.sha(directory / "files/srrx-fixture.conf")}}}


class ListedPatchBindingTests(unittest.TestCase):
    """deploy._record_binding: one receipt per listed patch, the source member and recipe files."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-binding-v2-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        self.good = v2_deployment(self.root)
        for name, value in (("HERE", self.root), ("PROJECT", self.root.parent)):
            mocked = patch.object(deploy, name, value)
            mocked.start()
            self.addCleanup(mocked.stop)

    def refused(self, needle, change):
        record = copy.deepcopy(self.good)
        change(record["build_environment"])
        with self.assertRaisesRegex(deploy.DeploymentError, needle):
            deploy._record_binding(record, "fixture")

    def test_a_three_patch_record_binds_with_three_receipts(self):
        self.assertEqual(len(self.good["build_environment"]["patch_receipts"]), 3)
        deploy._record_binding(self.good, "fixture")

    def test_a_patch_list_mismatch_is_refused(self):
        receipts = lambda change: (lambda environment: change(environment["patch_receipts"]))  # noqa: E731
        for label, change in {"one receipt missing": receipts(lambda r: r.pop()),
                              "one receipt more": receipts(lambda r: r.append(copy.deepcopy(r[0]))),
                              "receipts reordered": receipts(lambda r: r.reverse()),
                              "other patch bytes": receipts(lambda r: r[1].update(sha256="0" * 64)),
                              "other strip level": receipts(lambda r: r[2].update(strip=0)),
                              "other file": receipts(lambda r: r[0].update(file="patches/0009-other.patch")),
                              "no receipt list": lambda e: e.pop("patch_receipts"),
                              "receipts not a list": lambda e: e.update(patch_receipts={"file": "x"}),
                              "receipt not an object": receipts(lambda r: r.__setitem__(0, "patches/0001-synthetic.patch"))}.items():
            with self.subTest(label):
                self.refused("patch list differs", change)
        (self.root / "recipes" / FIXTURE / "patches/0002-synthetic.patch").write_text("changed after the build\n", encoding="utf-8")
        with self.assertRaisesRegex(deploy.DeploymentError, r"patch list differs .*\(3 listed, 3 recorded\)"):
            deploy._record_binding(self.good, "fixture")

    def test_member_and_recipe_files_are_bound(self):
        self.refused("source member differs", lambda e: e.pop("source_member"))
        self.refused("source member differs", lambda e: e.update(source_member=dict(MEMBER, sha256="0" * 64)))
        self.refused("source member differs", lambda e: e.update(source_member=dict(MEMBER, path="other/inner.tgz")))
        self.refused("recipe files differ", lambda e: e["recipe_files"].update({"check_recipe.py": "0" * 64}))
        self.refused("recipe files differ", lambda e: e["recipe_files"].update({"files/absent.conf": "0" * 64}))
        self.refused("recipe files differ", lambda e: e["recipe_files"].update({"../recipes/x": "0" * 64}))
        self.refused("recipe files differ", lambda e: e.update(recipe_files=[]))
        (self.root / "recipes" / FIXTURE / "files/srrx-fixture.conf").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(deploy.DeploymentError, "recipe files differ"):
            deploy._record_binding(self.good, "fixture")

    def test_recipe_files_and_hooks_come_from_the_recipe(self):
        # The expected recipe files and hooks are the recipe's (hook script, files/ matches, hooks in
        # builder order), not whatever the record lists; build records are not signed.
        directory = self.root / "recipes" / FIXTURE
        files = lambda change: (lambda e: change(e["recipe_files"]))  # noqa: E731
        hooks = lambda change: (lambda e: change(e["hooks"]))  # noqa: E731
        for label, change in {"recipe file dropped": files(lambda f: f.pop("files/srrx-fixture.conf")),
                              "hook script dropped": files(lambda f: f.pop("check_recipe.py")),
                              "recipe_files missing for a hooked recipe": lambda e: e.pop("recipe_files"),
                              "recipe_files empty": lambda e: e.update(recipe_files={})}.items():
            with self.subTest(label):
                self.refused("recipe files differ", change)
        for label, change in {"hook list missing": lambda e: e.pop("hooks"),
                              "hook list empty": lambda e: e.update(hooks=[]),
                              "hook list not a list": lambda e: e.update(hooks={"package": {}}),
                              "one hook missing": hooks(lambda h: h.pop(0)),
                              "hooks reordered": hooks(lambda h: h.reverse()),
                              "hook entry not an object": hooks(lambda h: h.__setitem__(0, "source_check")),
                              "other hook argv": hooks(lambda h: h[0].update(argv=h[0]["argv"] + ["--strict"])),
                              "other hook script": hooks(lambda h: h[1].update(script_sha256="0" * 64)),
                              "package output missing": hooks(lambda h: h[1].pop("output")),
                              "package output named otherwise": hooks(lambda h: h[1].update(output="other.package-hook.json")),
                              "package output without its sha": hooks(lambda h: h[1].update(output_sha256=None)),
                              "source_check with an output": hooks(lambda h: h[0].update(output=FIXTURE + ".package-hook.json",
                                                                                          output_sha256="d" * 64))}.items():
            with self.subTest(label):
                self.refused("hooks differ", change)
        (directory / "check_recipe.py").write_text("# rewritten after the build\n", encoding="utf-8")
        record = copy.deepcopy(self.good)
        record["build_environment"]["recipe_files"].pop("check_recipe.py")  # and its entry left out of the record
        for each in (record, self.good):
            with self.subTest(recipe_files=sorted(each["build_environment"]["recipe_files"])), \
                    self.assertRaisesRegex(deploy.DeploymentError, "recipe files differ"):
                deploy._record_binding(each, "fixture")

    def test_recipe_file_globs_bind_every_match(self):
        directory = self.root / "recipes" / FIXTURE
        recipe = json.loads((directory / "recipe.json").read_text(encoding="utf-8"))
        recipe["install"]["copy"] = [{"from": "{recipe}/files/*.conf", "to": "etc/srrx-fixture"}]
        (directory / "recipe.json").write_text(json.dumps(recipe), encoding="utf-8")
        record = copy.deepcopy(self.good)
        record["recipe_sha256"] = deploy.sha(directory / "recipe.json")
        deploy._record_binding(record, "fixture")
        added = directory / "files/added-after-the-build.conf"
        added.write_text("# not in the build\n", encoding="utf-8")
        with self.assertRaisesRegex(deploy.DeploymentError, "recipe files differ"):
            deploy._record_binding(record, "fixture")
        record["build_environment"]["recipe_files"]["files/added-after-the-build.conf"] = deploy.sha(added)
        deploy._record_binding(record, "fixture")

    def test_schema_1_records_bind_as_before(self):
        with patch.object(deploy, "HERE", HERE), patch.object(deploy, "PROJECT", HERE.parent):
            record = {"component": "rtlsdr", "recipe_sha256": deploy.sha(HERE / "recipes/rtlsdr/recipe.json"),
                      "build_environment": {"patch_receipt": {"component": "rtlsdr", "patch_sha256": deploy.sha(HERE / "patches/rtlsdr-rx-only.patch")}}}
            deploy._record_binding(record, "rtlsdr")  # a record written before schema 2: no new fields
            current = copy.deepcopy(record)
            current["build_environment"].update(patch_receipts=[], source_member=None, recipe_files={})
            deploy._record_binding(current, "rtlsdr")  # the fields this builder now writes for a schema-1 recipe
            current["build_environment"]["patch_receipts"].append({"file": "patches/0001-x.patch", "sha256": "0" * 64, "strip": 1})
            with self.assertRaisesRegex(deploy.DeploymentError, r"patch list differs .*\(0 listed, 1 recorded\)"):
                deploy._record_binding(current, "rtlsdr")


class PackageHookOutputTests(unittest.TestCase):
    """check_repo.record_binding: the package hook output next to the record and its record_digests."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-hook-output-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        self.record = v2_deployment(self.root)
        for name, value in (("HERE", self.root), ("PROJECT", self.root.parent)):
            mocked = patch.object(deploy, name, value)
            mocked.start()
            self.addCleanup(mocked.stop)
        spec = importlib.util.spec_from_file_location("srrx_check_repo_hooks", HERE / "repo/check_repo.py")
        self.check_repo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.check_repo)
        self.out = Path(self.temp.name) / "out" / FIXTURE
        self.out.mkdir(parents=True)
        self.output = self.out / (FIXTURE + ".package-hook.json")
        self.output.write_text(json.dumps({"files": {}, "record_digests": {"sha256": "a" * 64}}), encoding="utf-8")
        self.record["build_environment"]["hooks"][1].update(output=self.output.name, output_sha256=deploy.sha(self.output))
        self.record["record_digests"] = {"sha256": "a" * 64}
        self.path = self.out / (FIXTURE + ".build-record.json")

    def test_output_and_digests_match_the_record(self):
        self.assertEqual(self.check_repo.record_binding(self.path, self.record),
                         {"component": FIXTURE, "patch_receipts": 3, "source_member": MEMBER["path"], "record_digests": True})
        for label, change, needle in (
                ("digests differ", lambda r: r.update(record_digests={"sha256": "b" * 64}), "record_digests differ"),
                ("digests without output", lambda r: [r["build_environment"]["hooks"][1].pop(k) for k in ("output", "output_sha256")], "hooks differ"),
                ("no hook list", lambda r: r["build_environment"].pop("hooks"), "hooks differ"),
                ("output elsewhere", lambda r: r["build_environment"]["hooks"][1].update(output="../" + self.output.name), "hooks differ"),
                ("output bytes", lambda r: r["build_environment"]["hooks"][1].update(output_sha256="0" * 64), "hook output differs"),
                ("patch list", lambda r: r["build_environment"]["patch_receipts"].pop(), "patch list differs")):
            record = copy.deepcopy(self.record)
            change(record)
            with self.subTest(label), self.assertRaisesRegex(self.check_repo.CheckError, needle):
                self.check_repo.record_binding(self.path, record)

    def test_record_digests_need_a_package_hook_output(self):
        # A package hook without {hook_out} names no output, so record_digests would have no source.
        root = Path(self.temp.name) / "no-hook-out" / "deployment"
        record = v2_deployment(root, hook_out=False)
        with patch.object(deploy, "HERE", root), patch.object(deploy, "PROJECT", root.parent):
            self.assertFalse(self.check_repo.record_binding(self.path, record)["record_digests"])
            record["record_digests"] = {"sha256": "a" * 64}
            with self.assertRaisesRegex(self.check_repo.CheckError, "without a package hook output"):
                self.check_repo.record_binding(self.path, record)
            record["build_environment"]["hooks"][1].update(output=self.output.name, output_sha256=deploy.sha(self.output))
            with self.assertRaisesRegex(self.check_repo.CheckError, "hooks differ"):
                self.check_repo.record_binding(self.path, record)


@unittest.skipUnless(GPG, "gpg/gpgv not available (SRRX_RELEASE_BUILDER=1 makes this a failure)")
class SchemaV2SignedRecordTests(unittest.TestCase):
    """deploy.verify_repo with the schema-2 record fields: record_digests is the one optional key, and
    the listed-patch, member and recipe-file bindings refuse a record that differs from the recipe."""
    # The fixtures of SignedRepositoryTests, without inheriting (and re-running) its tests.
    setUpClass = classmethod(SignedRepositoryTests.setUpClass.__func__)
    tearDownClass = classmethod(SignedRepositoryTests.tearDownClass.__func__)
    setUp = SignedRepositoryTests.setUp
    publish = SignedRepositoryTests.publish
    record = SignedRepositoryTests.record
    verify = SignedRepositoryTests.verify
    refused = SignedRepositoryTests.refused

    def environment(self, **fields):
        return dict({"patch_receipt": {"component": "rtlsdr", "patch_sha256": deploy.sha(HERE / "patches/rtlsdr-rx-only.patch")},
                     "patch_receipts": [], "source_member": None, "recipe_files": {}}, **fields)

    def test_record_digests_is_the_one_optional_record_field(self):
        repo = self.publish()
        self.assertEqual(self.verify(repo, [self.record(build_environment=self.environment(), record_digests={"sha256": "a" * 64})])["packages"], 2)
        self.refused("record_digests must be an object", repo, [self.record(record_digests=["a" * 64])])
        self.refused("missing or unknown fields", repo, [self.record(digests={"sha256": "a" * 64})])

    def test_records_differing_from_the_recipe_patches_member_or_files_are_refused(self):
        repo = self.publish()
        receipt = {"file": "patches/0001-x.patch", "sha256": "0" * 64, "strip": 1}
        self.refused("patch list differs", repo, [self.record(build_environment=self.environment(patch_receipts=[receipt]))])
        self.refused("source member differs", repo, [self.record(build_environment=self.environment(source_member=dict(MEMBER)))])
        self.refused("recipe files differ", repo, [self.record(build_environment=self.environment(recipe_files={"check_recipe.py": "0" * 64}))])


if __name__ == "__main__":
    unittest.main()
