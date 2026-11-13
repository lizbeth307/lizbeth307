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
        stanzas = [s for s in deploy.deb822((HERE / "repo/lab.pref").read_text(encoding="utf-8"), "lab.pref") if s["package"] == "*"]
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


class LabPrefMinusOnePinTests(unittest.TestCase):
    """W2 IMG-1: the -1 pattern pins of build/07 section 2 (STACK.md:892) appended to repo/lab.pref after
    the three wildcard stanzas, and the srrx-mirror sources entry the image installs next to srrx-lab's."""

    # build/07-pz-vstanovlennia.md section 2 table, by name (globs of the table are policy globs too)
    BUILD07 = ("wsjtx", "libhamlib4t64", "libhamlib-utils", "libhamlib-dev", "fldigi", "qsstv", "direwolf", "js8call", "python3-js8py",
               "soapysdr-module-all", "soapysdr0.8-module-all", "soapysdr0.8-module-remote", "soapysdr0.8-module-lms7",
               "soapysdr0.8-module-hackrf", "soapysdr0.8-module-bladerf", "soapysdr0.8-module-uhd", "soapysdr0.8-module-redpitaya",
               "libsoapysdr0.9-1", "limesuite", "limesuiteng-gui", "gr-limesuiteng", "limesuiteng-cli", "librtlsdr0", "rtl-433",
               "digiham-tools", "python3-digiham", "codecserver", "codecserver-driver-ambe3k", "acarsdec", "dumphfdl", "dumpvdl2",
               "libacars-tools", "libacars2", "dump1090-fa", "dump1090-fa-minimal", "dump978-fa", "skyaware978", "dxlaprs-tetra",
               "dxlaprs-lora", "python3-meshtastic", "python3-bleak", "m17-demod", "nrsc5", "hpsdrconnector", "multimon-ng", "lame",
               "python3-paho-mqtt", "gr-gsm", "gr-iridium", "kalibrate-rtl", "urh", "qcom-fastrpc1", "qairt-dsp-binaries", "libqnn1",
               "libqnn-dev", "libsnpe1", "qnn-tools", "snpe-tools", "qcom-adreno1", "dragonwing-defaults", "firmware-qcom-audioreach",
               "firmware-qcom-soc", "linux-firmware-qualcomm-misc", "hexagon-dsp-binaries-qcs6490", "firmware-qcom-dsp",
               "linux-image-7.0.11-7-qcom", "linux-headers-7.0.11-7-qcom")

    def setUp(self):
        import fnmatch
        self.match = fnmatch.fnmatchcase
        self.text = (HERE / "repo/lab.pref").read_text(encoding="utf-8")
        self.stanzas = deploy.deb822(self.text, "lab.pref")
        self.extra = [s for s in self.stanzas if s["package"] != "*"]
        self.policy = deploy.load(HERE / "receive-only-policy.json")

    def tokens(self, pin):
        return {t for s in self.extra if s["pin"] == pin for t in s["package"].split()}

    def test_wildcards_come_first_and_every_extra_stanza_only_lowers(self):
        self.assertEqual([s["package"] for s in self.stanzas[:3]], ["*"] * 3)
        self.assertNotIn("*", [s["package"] for s in self.stanzas[3:]])  # RX-16 accepts exactly three wildcard stanzas
        self.assertGreaterEqual(len(self.extra), 8)
        for stanza in self.extra:
            self.assertEqual(int(stanza["pin-priority"]), -1, stanza["package"])
            self.assertEqual(list(stanza)[0], "explanation", stanza["package"])  # apt_preferences(5): Explanation begins a record
        self.assertTrue(self.text.endswith("\n") and "\r" not in self.text and "<" not in self.text)

    def test_policy_packages_without_a_version_rule_are_pinned_from_every_origin(self):
        never = self.tokens("release *")
        for entry in self.policy["forbidden_packages"]:
            rule = entry.get("name") or entry["glob"]
            if "version_rule" not in entry:  # embloader has one; it is route A only (files/srrx-boot-route-a.pref)
                self.assertIn(rule, never, rule)
        for name in self.BUILD07:
            self.assertTrue(any(self.match(name, token) for token in never), name)

    def test_lab_build_only_packages_never_come_from_the_mirror(self):
        self.assertEqual(self.tokens("release o=srrx-mirror"), set(deploy.LAB_BUILD_ONLY_PACKAGES))
        self.assertNotIn("embloader", {t for s in self.extra for t in s["package"].split()})  # route B keeps embloader 0.4

    def test_version_pins_match_the_policy_thresholds_and_spare_the_held_versions(self):
        pins = {s["package"]: s["pin"][len("version "):] for s in self.extra if s["pin"].startswith("version ")}
        self.assertEqual(set(pins), {"linux-firmware-dragonwing", "*mesa*", "edk2-*"})
        self.assertTrue(apt_version_pin_matches(pins["linux-firmware-dragonwing"], "1.0.0+20260825"))  # apt semantics (below)
        self.assertFalse(apt_version_pin_matches(pins["linux-firmware-dragonwing"], "1.0.0+20251203"))  # held r2 version
        rules = {e["glob"]: e["version_rule"]["forbid_at_least"] for e in self.policy["forbidden_packages"]
                 if e.get("glob") in ("*mesa*", "edk2-*")}
        grids = {"*mesa*": (["9.0.0-2", "9.0.2-1.1build1", "25.2.8-0ubuntu0.24.04.1"],  # r2 versions (image facts, run 42354844339)
                            ["2.0", "25", "25.99", "26", "26~rc1", "26.0.1-1", "27.1", "29.0", "30.0", "99.9", "100.0", "260.1", "025.9",
                             "026.0", "0:25.1", "0:26.0", "1:9.0", "12:1"]),
                 "edk2-*": (["0.1.0-5", "0.1.0-7"],  # r2 0.1.0-5; 0.1.0-7 is the archived one (STACK.md:896)
                            ["0.0.9-99", "0.1-9", "0.1.0", "0.1.0-1ubuntu8", "0.1.0-7.1", "0.1.0~rc1-9", "0.1.0-8", "0.1.0-08", "0.1.0-8ubuntu1",
                             "0.1.0-9", "0.1.0-10", "0.1.0-80", "0.1.0.1-1", "0.1.0+git1-1", "0.1.05-1", "0.1.1-1", "0.1.10-1", "0.2-1",
                             "0.10.0-1", "00.1.0-8", "1.0-1", "10.0", "1:0.0.1", "0:0.1.0-8"])}
        for package, (held, grid) in grids.items():
            pin = pins[package]
            self.assertTrue(pin.startswith("/^") and pin.endswith("/"), pin)
            self.assertIsNone(re.search(r"\\[dDwWsSbB]|\(\?|[*+?}]\?", pin))  # POSIX ERE subset only (apt uses regcomp)
            regex = re.compile(pin[1:-1])
            for version in held + grid:
                forbidden = deploy.deb_compare(version, rules[package]) >= 0
                if forbidden or "~" not in version:  # a pre-release just below the threshold may be blocked (conservative)
                    self.assertEqual(regex.search(version) is not None, forbidden, (package, version))
            for version in held:
                self.assertIsNone(regex.search(version), (package, version))

    def test_mirror_sources_entry_is_the_lab_entry_with_its_own_suite(self):
        lab = deploy.deb822((HERE / "repo/srrx-lab.sources").read_text(encoding="utf-8"), "lab")[0]
        mirror = deploy.deb822((HERE / "repo/srrx-mirror.sources").read_text(encoding="utf-8"), "mirror")[0]
        self.assertEqual(set(mirror), set(lab))
        for key in ("types", "components", "architectures", "signed-by"):
            self.assertEqual(mirror[key], lab[key], key)
        self.assertEqual(mirror["signed-by"], deploy.load(deploy.REPO_POLICY)["keyring_path"])
        self.assertNotEqual(mirror["suites"], lab["suites"])
        self.assertTrue(mirror["uris"].startswith("file:/srv/srrx-repo/") and mirror["uris"] != lab["uris"])


# --- W2 SW-CI: package data trees (D-17) in deploy.verify_repo and check_repo.py tamper, and the
# sr-rx-packages.yml helpers of check_repo.py (heavy selection, release tarball vs tag, tag samples,
# runtime-check install set, chain identity). Synthetic inputs in temporary directories.
def load_check_repo(name):
    spec = importlib.util.spec_from_file_location(name, HERE / "repo/check_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def control_deb(control, files):
    """make_deb with another control file (Depends for the runtime-check install set)."""
    data = bytearray(make_deb(files))
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:xz") as archive:
        info = tarfile.TarInfo("./control")
        info.size = len(control.encode())
        archive.addfile(info, io.BytesIO(control.encode()))
    payload, out, offset = buffer.getvalue(), b"!<arch>\n", 8
    while offset < len(data):
        header = bytes(data[offset:offset + 60])
        size = int(header[48:58])
        name, body = header[:16].strip(), bytes(data[offset + 60:offset + 60 + size])
        if name == b"control.tar.xz":
            body = payload
        out += (name.decode().ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) + "100644".ljust(8) + str(len(body)).ljust(10) + "`\n").encode()
        out += body + (b"\n" if len(body) % 2 else b"")
        offset += 60 + size + (size & 1)
    return out


class DataInventoryTests(unittest.TestCase):
    """deploy.deb_data_inventory: types, SHA-256, modes and link targets, with deb_data_tree's refusals."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-inventory-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_inventory_lists_every_member_with_hash_mode_or_target(self):
        deb = self.root / "dev.deb"
        deb.write_bytes(rtl_deb("librtlsdr-dev"))
        entries = deploy.deb_data_inventory(deb)
        self.assertEqual(entries["usr/include/rtl-sdr.h"], {"type": "file", "sha256": sha(b"/* synthetic header */\n"), "mode": "0644"})
        self.assertEqual(entries[LIB + "librtlsdr.so"], {"type": "symlink", "target": "librtlsdr.so.2"})  # dangling in this package
        self.assertEqual(entries["usr"], {"type": "dir", "mode": "0755"})
        kinds = {"file": "file", "symlink": "link", "dir": "dir"}
        self.assertEqual({p: kinds[e["type"]] for p, e in entries.items()}, deploy.deb_data_tree(deb))
        for data, needle in ((b"opaque", "not a .deb"), (make_deb({"a": b"1"})[:80], "no data.tar"), (make_deb({"../escape": b"x"}), "unsafe")):
            (self.root / "bad.deb").write_bytes(data)
            with self.subTest(needle), self.assertRaisesRegex(deploy.DeploymentError, needle):
                deploy.deb_data_inventory(self.root / "bad.deb")

    def test_data_tree_file_needs_its_hash_package_and_schema(self):
        tree = self.root / "librtlsdr-dev.data-tree.json"
        document = {"schema_version": 1, "kind": "srrx_lab_data_tree", "package": "librtlsdr-dev", "version": RTL["version"], "entries": {}}
        tree.write_text(json.dumps(document), encoding="utf-8")
        self.assertEqual(deploy._data_tree(tree, deploy.sha(tree), "librtlsdr-dev", RTL["version"]), {})
        with self.assertRaisesRegex(deploy.DeploymentError, "differs from the build record"):
            deploy._data_tree(tree, "0" * 64, "librtlsdr-dev", RTL["version"])
        with self.assertRaisesRegex(deploy.DeploymentError, "differs from the build record"):
            deploy._data_tree(self.root / "absent.json", "0" * 64, "librtlsdr-dev", RTL["version"])
        for change in ({"package": "librtlsdr2"}, {"kind": "other"}, {"version": "2.0.1"}, {"entries": []}):
            tree.write_text(json.dumps(dict(document, **change)), encoding="utf-8")
            with self.subTest(change), self.assertRaisesRegex(deploy.DeploymentError, "another package or schema"):
                deploy._data_tree(tree, deploy.sha(tree), "librtlsdr-dev", RTL["version"])


@unittest.skipUnless(GPG, "gpg/gpgv not available (SRRX_RELEASE_BUILDER=1 makes this a failure)")
class DataTreeRepositoryTests(unittest.TestCase):
    """verify_repo with records that carry data trees: every package or none, each equal to the pool .deb."""
    setUpClass = classmethod(SignedRepositoryTests.setUpClass.__func__)
    tearDownClass = classmethod(SignedRepositoryTests.tearDownClass.__func__)
    setUp = SignedRepositoryTests.setUp
    publish = SignedRepositoryTests.publish
    record = SignedRepositoryTests.record
    verify = SignedRepositoryTests.verify
    refused = SignedRepositoryTests.refused

    def treed(self, edit=None, rebind=True, **overrides):
        """A record with a <package>.data-tree.json per package (as build_recipe writes them);
        edit(package, document) changes one, rebound to the record unless rebind is False."""
        path = self.record(**overrides)
        record = json.loads(path.read_text(encoding="utf-8"))
        for package, (_, _, data) in zip(record["packages"], self.packages):
            (self.root / "tree.deb").write_bytes(data)
            document = {"schema_version": 1, "kind": "srrx_lab_data_tree", "package": package["package"], "version": package["version"],
                        "entries": deploy.deb_data_inventory(self.root / "tree.deb")}
            tree = path.parent / (package["package"] + ".data-tree.json")
            tree.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
            package["data_tree_sha256"] = deploy.sha(tree)
            if edit and edit(package, document):
                tree.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
                if rebind:
                    package["data_tree_sha256"] = deploy.sha(tree)
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_matching_data_trees_pass_and_every_package_is_checked(self):
        repo = self.publish()
        result = self.verify(repo, [self.treed()])
        self.assertEqual((result["packages"], result["data_trees_checked"]), (2, 2))
        self.assertEqual(self.verify(repo, [self.record()])["data_trees_checked"], 0)  # a record written before data trees

    def test_a_changed_byte_mode_or_target_in_the_dev_tree_is_refused(self):
        repo = self.publish()

        def dev(change):
            return lambda package, document: package["package"] == "librtlsdr-dev" and (change(document["entries"]) or True)
        cases = {"one changed byte": lambda e: e["usr/include/rtl-sdr.h"].update(sha256=sha(b"/* synthetic header */\r\n")),
                 "another mode": lambda e: e["usr/include/rtl-sdr.h"].update(mode="0755"),
                 "another link target": lambda e: e[LIB + "librtlsdr.so"].update(target="librtlsdr.so.3"),
                 "an extra path": lambda e: e.update({"usr/share/doc/x": {"type": "file", "sha256": "0" * 64, "mode": "0644"}}),
                 "a missing path": lambda e: e.pop("usr/include/rtl-sdr.h")}
        for label, change in cases.items():
            with self.subTest(label):
                self.refused("data tree differs from the build record data tree: librtlsdr-dev", repo, [self.treed(dev(change))])
        self.refused("package data tree differs from the build record: librtlsdr-dev", repo,
                     [self.treed(dev(lambda e: e.pop("usr/include/rtl-sdr.h")), rebind=False)])
        self.refused("names another package", repo, [self.treed(lambda p, d: p["package"] == "librtlsdr-dev" and (d.update(package="x") or True))])

    def test_a_missing_or_partial_data_tree_is_refused(self):
        repo = self.publish()
        missing = self.treed()
        (missing.parent / "librtlsdr-dev.data-tree.json").unlink()
        self.refused("package data tree differs from the build record: librtlsdr-dev", repo, [missing])
        partial = self.treed()
        record = json.loads(partial.read_text(encoding="utf-8"))
        record["packages"][1].pop("data_tree_sha256")
        partial.write_text(json.dumps(record), encoding="utf-8")
        self.refused("data tree for some packages only", repo, [partial])

    def test_check_repo_tamper_refuses_the_data_tree_cases(self):
        check_repo = load_check_repo("srrx_check_repo_tamper_trees")
        repo = self.publish()
        result = check_repo.tamper(repo, self.keyring, self.wrong, self.fpr, [self.treed()], self.sources)
        trees = {k: v for k, v in result["cases"].items() if k.startswith(("data tree", "record without the data tree"))}
        self.assertEqual(sorted(trees), sorted(["data tree with one changed file hash (librtlsdr-dev)", "data tree with another mode (librtlsdr-dev)",
                                                "data tree with an extra path (librtlsdr-dev)", "data tree changed after the record (librtlsdr-dev)",
                                                "data tree of another package (librtlsdr-dev)", "data tree file missing (librtlsdr-dev)",
                                                "record without the data tree of one package (librtlsdr-dev)"]))
        self.assertEqual(set(result["cases"].values()), {"REFUSED"})
        self.assertFalse(any(k.startswith("data tree") for k in check_repo.tamper(repo, self.keyring, self.wrong, self.fpr, [self.record()],
                                                                                  self.sources)["cases"]))  # records without data trees


class HeavySelectionTests(unittest.TestCase):
    """check_repo.heavy_selection and the [lab-build-all] token of sr-rx-packages.yml."""
    PLAN = {"heavy": ["satdump", "sdrangel"], "recipes": {"satdump": {"chain": ["satdump"]}, "sdrangel": {"chain": ["rtlsdr", "sdrangel"]}}}

    def setUp(self):
        self.check_repo = load_check_repo("srrx_check_repo_heavy")

    def select(self, changed, lock_before=None, build_all=False):
        return sorted(self.check_repo.heavy_selection(self.PLAN, changed, lock_before, LOCK, build_all))

    def test_heavy_recipes_run_only_when_their_inputs_change(self):
        project = self.check_repo.PROJECT_PREFIX + "deployment/"
        self.assertEqual(self.check_repo.PROJECT_PREFIX, HERE.parent.name + "/")
        self.assertEqual(self.select([]), [])
        self.assertEqual(self.select([project + "deploy.py", project + "selftest.py", project + "recipes/README.md"]), [])
        self.assertEqual(self.select([project + "recipes/satdump/recipe.json"]), ["satdump"])
        self.assertEqual(self.select([project + "recipes/satdump/patches/0001-x.patch"]), ["satdump"])
        self.assertEqual(self.select([project + "recipes/rtlsdr/recipe.json"]), ["sdrangel"])  # rtlsdr is in its chain
        self.assertEqual(self.select([project + "patches/rtlsdr-rx-only.patch"]), ["sdrangel"])
        self.assertEqual(self.select([project + "recipes/satdumpx/recipe.json"]), [])  # a prefix, not the directory
        for builder in self.check_repo.BUILDER_INPUTS:
            with self.subTest(builder):
                self.assertEqual(self.select([builder]), ["satdump", "sdrangel"])
        self.assertIn(".github/workflows/sr-rx-packages.yml", self.check_repo.BUILDER_INPUTS)
        self.assertEqual(self.select(None), ["satdump", "sdrangel"])  # range unknown
        self.assertEqual(self.select([], build_all=True), ["satdump", "sdrangel"])
        reasons = self.check_repo.heavy_selection(self.PLAN, [], None, LOCK, True)
        self.assertEqual(set(reasons.values()), {"[lab-build-all]"})

    def test_a_changed_lock_entry_of_the_chain_selects_the_heavy_job(self):
        lock_path = self.check_repo.PROJECT_PREFIX + "deployment/sources.lock.json"
        self.assertEqual(self.select([lock_path], copy.deepcopy(LOCK)), [])  # the lock changed elsewhere
        before = copy.deepcopy(LOCK)
        next(c for c in before["components"] if c["id"] == "rtlsdr")["version"] = "2.0.3-0+lab0"
        self.assertEqual(self.select([lock_path], before), ["sdrangel"])
        self.assertEqual(self.select([lock_path], {}), ["satdump", "sdrangel"])  # no lock at the start of the range
        self.assertEqual(self.select([], before), [])  # the lock is not in the range

    def test_the_token_is_one_fixed_text(self):
        token = self.check_repo.LAB_BUILD_ALL
        for message in ("SW-X: rebuild [lab-build-all]", "[lab-build-all] [image-build]", "a\n\nbody [lab-build-all]\n"):
            self.assertTrue(token.search(message), message)
        for message in ("lab-build-all", "[lab-build-al]", "[LAB-BUILD-ALL]", "[lab build all]", "[lab-build-all ]", ""):
            self.assertFalse(token.search(message), message)

    def test_plan_and_job_outputs_of_the_real_tree(self):
        result = self.check_repo.plan([], {}, False)
        self.assertEqual((result["status"], result["heavy_run"], result["build"]), ("CI_RECIPE_PLAN", [], result["light"]))
        self.assertIn("rtlsdr", result["light"])
        outputs = dict(line.split("=", 1) for line in self.check_repo.github_outputs(result).splitlines())
        self.assertEqual((outputs["heavy_matrix"], outputs["heavy_count"]), ("[]", "0"))
        self.assertEqual(outputs["light"].split(), result["light"])
        forced = dict(result, heavy_run=["satdump"], recipes=dict(result["recipes"], satdump={"chain": ["rtlsdr", "satdump"]}))
        self.assertEqual(json.loads(dict(line.split("=", 1) for line in self.check_repo.github_outputs(forced).splitlines())["heavy_matrix"]),
                         [{"recipe": "satdump", "chain": "rtlsdr satdump"}])


def git_repo(root, files, tag="srrx-fixture-1.0"):
    """A local git repository with one commit of files {path: text} and a tag; returns its commit."""
    root.mkdir(parents=True)
    run = lambda *args: subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "user.name=SR-RX test", "-c", "user.email=builder@srrx.invalid"]  # noqa: E731
                                       + list(args), cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    run("init", "-q")
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(text.encode())
    run("add", "-A")
    run("commit", "-q", "-m", "synthetic")
    run("tag", tag)
    return run("rev-parse", "HEAD")


def tarball(path, root, files, mode="w:gz"):
    with tarfile.open(path, mode) as archive:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(root + "/" + name)
            data = data if type(data) is bytes else data.encode()
            info.size, info.mode = len(data), 0o644
            archive.addfile(info, io.BytesIO(data))
    return path


@unittest.skipUnless(shutil.which("git"), "git unavailable")
class ReleaseTarballTests(unittest.TestCase):
    """check_repo.py tarball-vs-tag and tag-samples against a local tag (no network)."""
    FILES = {"README": "synthetic project\n", "src/a.c": "int a;\n", "src/b.c": "int b;\n", "samples/FT8/x.wav": "RIFF synthetic\n"}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-release-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.check_repo = load_check_repo("srrx_check_repo_release")
        self.commit = git_repo(self.root / "clone", self.FILES)
        self.component = {"id": "srrx-fixture", "tag": "srrx-fixture-1.0", "commit": self.commit, "upstream_url": "https://example.invalid/x.git",
                          "source_cache_path": "sources/srrx-fixture.tar.gz"}

    def test_release_tarballs_are_lock_entries_with_a_tag_and_no_git_tree(self):
        self.assertEqual([c["id"] for c in self.check_repo.release_tarballs(LOCK)], ["gpredict", "wsjt-decoders"])

    def test_tree_ids_and_entries_equal_git(self):
        entries = self.check_repo.tag_entries(self.root / "clone")
        self.assertEqual(sorted(entries), sorted(self.FILES))
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=self.root / "clone", capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(self.check_repo.tree_id(entries), tree)
        same, root = self.check_repo.tar_entries(tarball(self.root / "same.tar.gz", "srrx-fixture-1.0", self.FILES))
        self.assertEqual((same, root), (entries, "srrx-fixture-1.0"))
        with self.assertRaisesRegex(self.check_repo.CheckError, "one safe root"):
            self.check_repo.tar_entries(self.two_roots())

    def two_roots(self):
        path = self.root / "two.tar"
        with tarfile.open(path, "w") as archive:
            for name in ("a/x", "b/y"):
                info = tarfile.TarInfo(name)
                archive.addfile(info, io.BytesIO(b""))
        return path

    def test_the_closest_nested_archive_is_reported(self):
        inner = dict(self.FILES)
        del inner["samples/FT8/x.wav"]  # the release lacks samples/
        inner["src/b.c"] = "int b; /* release */\n"
        inner["configure"] = "#!/bin/sh\n"  # generated in the release
        nested = tarball(self.root / "inner.tgz", "srrx-fixture", inner).read_bytes()
        outer = tarball(self.root / "superbuild.tar.gz", "srrx-fixture-1.0", {"src/inner.tgz": nested, "src/other-9.tar.gz":
                        tarball(self.root / "other.tar.gz", "other-9", {"x": "y\n"}).read_bytes(), "README": "superbuild\n"})
        report = self.check_repo.compare_release_tarball(self.component, outer, self.root / "clone")
        self.assertEqual((report["compared"], report["verdict"], report["tag_commit_matches_lock"]), ("srrx-fixture-1.0/src/inner.tgz", "DIFFERENT", True))
        self.assertEqual((report["missing"], report["extra"], report["changed"]), (1, 1, 1))
        self.assertEqual(report["differences"], {"missing": ["samples/FT8/x.wav"], "extra": ["configure"], "changed": ["src/b.c"], "mode": []})
        self.assertEqual(self.check_repo.compare_entries({"a": ("100644", "1" * 40), "b": ("100644", "2" * 40)},
                                                         {"a": ("100755", "1" * 40), "b": ("100755", "3" * 40)}),
                         {"missing": [], "extra": [], "changed": ["b"], "mode": ["a"]})  # an executable bit alone is "mode"
        self.assertEqual(len(report["candidates"]), 3)  # the tarball itself and both nested archives
        member = self.check_repo.compare_release_tarball(self.component, outer, self.root / "clone", "srrx-fixture-1.0/src/inner.tgz")
        self.assertEqual((member["compared"], len(member["candidates"])), ("srrx-fixture-1.0/src/inner.tgz", 1))
        equal = self.check_repo.compare_release_tarball(self.component, tarball(self.root / "equal.tar.gz", "srrx-fixture-1.0", self.FILES), self.root / "clone")
        self.assertEqual((equal["verdict"], equal["tarball_tree"], equal["missing"] + equal["extra"] + equal["changed"] + equal["mode"]),
                         ("EQUAL", equal["tag_tree"], 0))
        moved = self.check_repo.compare_release_tarball(dict(self.component, commit="0" * 40), outer, self.root / "clone")
        self.assertFalse(moved["tag_commit_matches_lock"])

    def test_tag_samples_are_the_declared_paths_of_the_locked_commit(self):
        record = self.check_repo.export_tag_samples(self.root / "clone", self.component, ["samples/FT8"], self.root / "out" / "srrx-fixture")
        self.assertEqual((self.root / "out/srrx-fixture/samples/FT8/x.wav").read_text(encoding="utf-8"), "RIFF synthetic\n")
        self.assertEqual((record["commit"], sorted(record["paths"])), (self.commit, ["samples/FT8"]))
        tree = subprocess.run(["git", "rev-parse", "HEAD:samples/FT8"], cwd=self.root / "clone", capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(record["paths"]["samples/FT8"], tree)
        with self.assertRaisesRegex(self.check_repo.CheckError, "not the locked"):
            self.check_repo.export_tag_samples(self.root / "clone", dict(self.component, commit="0" * 40), ["samples/FT8"], self.root / "out2")
        with self.assertRaisesRegex(self.check_repo.CheckError, "has no samples/WSPR"):
            self.check_repo.export_tag_samples(self.root / "clone", self.component, ["samples/WSPR"], self.root / "out3")
        for component in (dict(self.component, upstream_url="git://example.invalid/x"), dict(self.component, tag="--upload-pack=x")):
            with self.subTest(component), self.assertRaisesRegex(self.check_repo.CheckError, "https upstream_url and a tag"):
                self.check_repo.clone_tag(component, self.root / "never")
        self.assertFalse((self.root / "never").exists())


class RuntimeCheckTests(unittest.TestCase):
    """The runtime-check install set, its chroot argv and the probe contract (the run itself needs root)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "debs"
        self.check_repo = load_check_repo("srrx_check_repo_runtime")

    def record(self, component, packages):
        directory = self.out / component
        directory.mkdir(parents=True)
        entries = []
        for name, control, files in packages:
            deb = directory / ("%s_1_arm64.deb" % name)
            deb.write_bytes(control_deb("Package: %s\nVersion: 1\nArchitecture: arm64\n%s" % (name, control), files))
            entries.append({"package": name, "version": "1", "architecture": "arm64", "filename": deb.name, "sha256": deploy.sha(deb), "size": deb.stat().st_size})
        (directory / (component + ".build-record.json")).write_text(json.dumps({"component": component, "packages": entries}), encoding="utf-8")

    def test_install_set_follows_lab_depends_and_leaves_dev_and_held_packages_out(self):
        self.record("rtlsdr", [("librtlsdr2", "Depends: libc6 (>= 2.34), libusb-1.0-0 (>= 2:1.0.16)\n", {LIB + "librtlsdr.so.2.0.3": b"\x7fELF lib"}),
                               ("librtlsdr-dev", "Depends: librtlsdr2 (= 1)\n", {"usr/include/rtl-sdr.h": b"/* h */\n"})])
        self.record("limesuiteng", [("liblimesuiteng", "Depends: libc6\n", {LIB + "liblimesuiteng.so.0.3-1": b"\x7fELF lime"})])
        self.record("srrx-tool", [("srrx-tool", "Depends: librtlsdr2 (>= 1) | librtlsdr0, libstdc++6:any, python3:any\n", {"usr/bin/srrx-tool": b"\x7fELF tool"})])
        install, snapshot, held = self.check_repo.runtime_packages(self.out, ["srrx-tool", "limesuiteng", "rtlsdr"])
        self.assertEqual([i["package"] for i in install], ["srrx-tool", "librtlsdr2"])
        self.assertEqual(snapshot, ["libc6", "libstdc++6", "libusb-1.0-0", "python3"])
        self.assertEqual({h["package"] for h in held}, {"liblimesuiteng", "librtlsdr-dev"})
        self.assertIn("RX-08", next(h["reason"] for h in held if h["package"] == "liblimesuiteng"))
        self.assertEqual(set(install[1]), {"package", "version", "sha256", "component", "record_sha256", "path"})  # lab_build.install_lab_packages
        with self.assertRaisesRegex(self.check_repo.CheckError, "no build record for recipe sdrangel"):
            self.check_repo.runtime_packages(self.out, ["sdrangel"])
        self.assertEqual(self.check_repo.relation_groups("a (>= 1) | b, c:any, d [arm64], e <!nocheck>"), [["a", "b"], ["c"], ["d"], ["e"]])
        self.assertEqual(self.check_repo.deb_control(self.out / "rtlsdr/librtlsdr2_1_arm64.deb")["package"], "librtlsdr2")

    def test_chroot_is_the_pinned_snapshot_without_a_toolchain(self):
        keyring = "/w/keyring/archive-pinned.gpg"
        argv = self.check_repo.runtime_chroot_argv(LOCK, Path("/c"), keyring, ["libusb-1.0-0", "strace"])
        base = self.check_repo.lab_build.mmdebstrap_argv({"build_depends": []}, LOCK, Path("/c"), keyring)
        self.assertEqual([a for a in argv if not a.startswith(("--variant=", "--include="))], [a for a in base if not a.startswith(("--variant=", "--include="))])
        self.assertIn("--variant=apt", argv)
        self.assertIn("--include=libusb-1.0-0,python3,strace", argv)
        self.assertIn("--keyring=" + keyring, argv)
        compile(self.check_repo.PROBE, "probe.py", "exec")
        self.assertIn('os.listdir("/sys/class/net")', self.check_repo.PROBE)
        self.assertIn('"ldd"', self.check_repo.PROBE)
        if not (hasattr(os, "geteuid") and os.geteuid() == 0):
            with self.assertRaisesRegex(self.check_repo.CheckError, "needs root"):
                self.check_repo.runtime_check(self.out, ["rtlsdr"], Path(self.temp.name) / "work")

    def test_chroot_commands_report_like_recipe_hooks(self):
        log = Path(self.temp.name) / "x.log"
        for code, stdout, status in ((0, 'noise\n{"ok": true, "findings": []}\n', "CI_PASS"), (0, '{"ok": true, "findings": ["x"]}', "FAIL"),
                                     (2, '{"ok": true, "findings": []}', "FAIL"), (0, "not json", "FAIL"), (0, "", "FAIL")):
            with self.subTest(stdout=stdout, code=code), patch.object(self.check_repo.subprocess, "run",
                                                                      return_value=subprocess.CompletedProcess([], code, stdout, "")):
                self.assertEqual(self.check_repo.chroot_json(["unshare", "python3", "-I", "/srrx-runtime/probe.py"], log)["status"], status)

    def test_heavy_chains_are_compared_with_the_published_bytes(self):
        self.record("rtlsdr", [("librtlsdr2", "", {LIB + "librtlsdr.so.2.0.3": b"\x7fELF lib"})])
        chains = Path(self.temp.name) / "chains"
        self.assertEqual(self.check_repo.chain_identity(self.out, chains)["status"], "NO_HEAVY_CHAINS")
        (chains / "satdump/rtlsdr").mkdir(parents=True)
        shutil.copyfile(self.out / "rtlsdr/rtlsdr.build-record.json", chains / "satdump/rtlsdr/rtlsdr.build-record.json")
        result = self.check_repo.chain_identity(self.out, chains)
        self.assertEqual((result["status"], [c["heavy"] for c in result["comparisons"]]), ("CHAIN_BYTES_EQUAL", ["satdump"]))
        record = json.loads((chains / "satdump/rtlsdr/rtlsdr.build-record.json").read_text(encoding="utf-8"))
        record["packages"][0]["sha256"] = "0" * 64
        (chains / "satdump/rtlsdr/rtlsdr.build-record.json").write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(self.check_repo.chain_identity(self.out, chains)["status"], "CHAIN_BYTES_DIFFER")


def apt_version_pin_matches(pin, version):
    """apt's pkgVersionMatch for 'Pin: version' (apt-pkg/versionmatch.cc, Debian/apt main, read
    2026-11-07): one trailing '*' is cut off and the rest is tried as a literal prefix, then the same cut
    string goes to ExpressionMatches: /.../ is regcomp(REG_EXTENDED | REG_ICASE), anything else
    fnmatch(FNM_CASEFOLD). Python's re stands in for the POSIX ERE subset lab.pref uses."""
    import fnmatch
    prefix = pin.endswith("*")
    text = pin[:-1] if prefix else pin
    if version.lower() == text.lower() or (prefix and version.lower().startswith(text.lower())):
        return True
    if len(text) >= 2 and text.startswith("/") and text.endswith("/"):
        return re.search(text[1:-1], version, re.IGNORECASE) is not None
    return fnmatch.fnmatch(version.lower(), text.lower())


class AptVersionPinSemanticsTests(unittest.TestCase):
    """W2 IMG-1 review (IMG1-R3): 'Pin: version *20260825*' only matched versions ENDING in 20260825 under
    apt (the last '*' is dropped), so the dragonwing pin is an unanchored ERE that also takes rebuilds."""

    def test_the_model_reproduces_apts_trailing_star_rule(self):
        self.assertTrue(apt_version_pin_matches("*20260825*", "1.0.0+20260825"))
        self.assertFalse(apt_version_pin_matches("*20260825*", "20260825-1"))  # what the old pin missed
        self.assertTrue(apt_version_pin_matches("2.4*", "2.4.125-1"))  # documented prefix form
        self.assertTrue(apt_version_pin_matches("/^26\\./", "26.0.1-1"))

    def test_dragonwing_pin_takes_the_ppa_version_and_its_rebuilds_but_spares_r2(self):
        stanzas = deploy.deb822((HERE / "repo/lab.pref").read_text(encoding="utf-8"), "lab.pref")
        pin = next(s["pin"] for s in stanzas if s["package"] == "linux-firmware-dragonwing")
        self.assertEqual(pin, "version /20260825/")
        for version in ("20260825", "20260825-1", "1.0.0+20260825", "1.0.0+20260825ubuntu1", "20260825~bpo24.04.1"):
            self.assertTrue(apt_version_pin_matches(pin[len("version "):], version), version)
        for version in ("1.0.0+20251203", "1.0.0+20251203ubuntu1", "20260826"):
            self.assertFalse(apt_version_pin_matches(pin[len("version "):], version), version)

    def test_no_version_pin_relies_on_a_trailing_star_inside_a_glob(self):
        for stanza in deploy.deb822((HERE / "repo/lab.pref").read_text(encoding="utf-8"), "lab.pref"):
            if stanza["pin"].startswith("version "):
                value = stanza["pin"][len("version "):]
                self.assertTrue(value.startswith("/") and value.endswith("/"), stanza["package"])


class ReviewedHeavyInputsTests(unittest.TestCase):
    """W2 SW-CI review fixes: the lock's apt_snapshot and receive-only-policy.json select heavy jobs,
    a published package must be built against published lab bytes, a runtime_check.py that would
    test nothing fails, and the push range / mirror detection of sr-rx-packages.yml."""
    PLAN = HeavySelectionTests.PLAN
    WORKFLOW = HERE.parent.parent / ".github/workflows/sr-rx-packages.yml"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-review-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "debs"
        self.check_repo = load_check_repo("srrx_check_repo_review")

    def select(self, changed, lock_before):
        return self.check_repo.heavy_selection(self.PLAN, changed, lock_before, LOCK)

    def test_apt_snapshot_and_receive_only_policy_select_every_heavy_job(self):
        project = self.check_repo.PROJECT_PREFIX + "deployment/"
        lock_path = project + "sources.lock.json"
        moved = copy.deepcopy(LOCK)
        moved["apt_snapshot"]["timestamp"] = "20990101T000000Z"
        self.assertEqual(self.select([lock_path], moved), {"satdump": "changed: sources.lock.json apt_snapshot",
                                                           "sdrangel": "changed: sources.lock.json apt_snapshot"})
        self.assertEqual(self.select([], moved), {})  # the lock is not in the range
        self.assertEqual(self.select([lock_path], copy.deepcopy(LOCK)), {})  # same snapshot, same chain entries
        self.assertIn(project + "receive-only-policy.json", self.check_repo.BUILDER_INPUTS)
        self.assertEqual(sorted(self.select([project + "receive-only-policy.json"], None)), ["satdump", "sdrangel"])
        self.assertNotIn(project + "deploy.py", self.check_repo.BUILDER_INPUTS)  # only a [lab-build-all] run (build/15)
        self.assertEqual(self.select([project + "deploy.py"], None), {})

    def record(self, component, packages, lab_build_depends=()):
        directory = self.out / component
        directory.mkdir(parents=True)
        entries = []
        for name, files in packages:
            deb = directory / ("%s_1_arm64.deb" % name)
            deb.write_bytes(control_deb("Package: %s\nVersion: 1\nArchitecture: arm64\nDepends: libc6\n" % name, files))
            entries.append({"package": name, "version": "1", "architecture": "arm64", "filename": deb.name, "sha256": deploy.sha(deb), "size": deb.stat().st_size})
        path = directory / (component + ".build-record.json")
        path.write_text(json.dumps({"component": component, "packages": entries, "build_environment": {"lab_build_depends": list(lab_build_depends)}}),
                        encoding="utf-8")
        return path

    def test_published_packages_are_built_against_published_lab_bytes(self):
        rtl = self.record("rtlsdr", [("librtlsdr2", {LIB + "librtlsdr.so.2.0.3": b"\x7fELF lib"}), ("librtlsdr-dev", {"usr/include/rtl-sdr.h": b"/* h */\n"})])
        dev = deploy.load(rtl)["packages"][1]
        item = {"package": "librtlsdr-dev", "version": "1", "sha256": dev["sha256"], "component": "rtlsdr", "record_sha256": deploy.sha(rtl)}
        heavy = self.record("sdrangel", [("sdrangel", {"usr/bin/sdrangel": b"\x7fELF sdrangel"})], [item])
        self.assertEqual(self.check_repo.lab_depends_published(self.out),
                         [{"component": "sdrangel", "package": "librtlsdr-dev", "sha256": dev["sha256"], "record_equal": True}])
        for change, message in (({"record_sha256": "0" * 64}, None), ({"sha256": "1" * 64}, "bytes this run does not publish"),
                                ({"version": "2"}, "bytes this run does not publish"), ({"component": "other"}, "bytes this run does not publish"),
                                ({"package": "libairspyhf-dev"}, "no record builds it")):
            with self.subTest(change):
                record = deploy.load(heavy)
                record["build_environment"]["lab_build_depends"] = [dict(item, **change)]
                heavy.write_text(json.dumps(record), encoding="utf-8")
                if message is None:  # another record file, the same bytes: reported only
                    self.assertFalse(self.check_repo.lab_depends_published(self.out)[0]["record_equal"])
                else:
                    with self.assertRaisesRegex(self.check_repo.CheckError, message):
                        self.check_repo.lab_depends_published(self.out)
        with patch.object(self.check_repo, "records", return_value=[]), \
                patch.object(self.check_repo, "lab_depends_published", side_effect=self.check_repo.CheckError("unpublished lab bytes")):
            with self.assertRaisesRegex(self.check_repo.CheckError, "unpublished lab bytes"):
                self.check_repo.packages(self.out)  # packages() applies the gate

    def test_a_runtime_check_with_nothing_installed_fails(self):
        self.record("limesuiteng", [("liblimesuiteng", {LIB + "liblimesuiteng.so.0.3-1": b"\x7fELF lime"}),
                                    ("limesuiteng-dev", {"usr/include/limesuiteng.h": b"/* h */\n"})])
        self.record("rtlsdr", [("librtlsdr2", {LIB + "librtlsdr.so.2.0.3": b"\x7fELF lib"})])
        script = Path(self.temp.name) / "runtime_check.py"
        script.write_text("print('{\"ok\": true, \"findings\": []}')\n", encoding="utf-8")
        cases = ((["limesuiteng"], {"limesuiteng"}, "CI_RUNTIME_CHECK_FAILED"), (["limesuiteng", "rtlsdr"], {"limesuiteng"}, "CI_RUNTIME_CHECK_FAILED"),
                 (["limesuiteng"], set(), "NO_RUNTIME_PACKAGES"))
        for number, (recipes, hooks, status) in enumerate(cases):
            with self.subTest(recipes=recipes, hooks=hooks), patch.object(self.check_repo.os, "geteuid", create=True, return_value=0), \
                    patch.object(self.check_repo, "runtime_script", side_effect=lambda name: script if name in hooks else None), \
                    patch.object(self.check_repo.lab_build, "pinned_keyring", side_effect=AssertionError("no chroot for this case")):
                report = self.check_repo.runtime_check(self.out, recipes, Path(self.temp.name) / ("work%d" % number))
                self.assertEqual((report["status"], report["installed"], report["probe"]), (status, [], None))
                self.assertEqual([f.split("/", 1)[0] for f in report["findings"]], sorted(hooks))

    @unittest.skipUnless((HERE.parent.parent / ".github/workflows/sr-rx-packages.yml").is_file(), "workflow file not in this tree")
    def test_push_range_and_mirror_detection_fail_safe(self):
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('git diff --no-renames --name-only "$base" HEAD', text)
        self.assertNotIn("HEAD^", text)  # a new branch is an unknown range, not its last commit
        self.assertNotIn("check_repo.py mirror --help", text)
        self.assertIn('python3 deployment/repo/check_repo.py --help > "$RUNNER_TEMP/check-repo-help.txt"', text)


# --- W2 REPO-MIRROR: the srrx-mirror publication of the image package closure (repo-policy.json
# mirror object, publish.sh --mirror, deploy.verify_repo(closure=...), check_repo.py mirror pieces).
# Synthetic closures and debs in temporary directories; the signed cases use a throwaway key.
CLOSURE_FILE = HERE / "image/package-closure.json"


def closure_file(path, packages):
    """A package closure file (schema 1, the build_image closure entry keys) for synthetic debs:
    packages [(name, version, architecture, deb bytes)]."""
    entries = [{"package": n, "version": v, "architecture": a, "filename": "pool/main/%s/%s/%s_%s_%s.deb" % (n[0], n, n, v, a),
                "suite": "noble-updates", "sha256": sha(d), "size": len(d), "r2_version": None, "reason": "synthetic"}
               for n, v, a, d in sorted(packages)]
    Path(path).write_text(json.dumps({"schema_version": 1, "status": "CANDIDATE", "packages": entries}, indent=2), encoding="utf-8")
    return Path(path)


def zstd_deb(deb):
    """The same .deb with its data member recompressed as data.tar.zst (zstd CLI), as the Ubuntu archive packs."""
    import lzma
    out, offset = b"!<arch>\n", 8
    while offset < len(deb):
        header = deb[offset:offset + 60]
        size = int(header[48:58])
        name, body = header[:16].strip().decode(), deb[offset + 60:offset + 60 + size]
        if name == "data.tar.xz":
            name = "data.tar.zst"
            body = subprocess.run(["zstd", "-q", "-c"], input=lzma.decompress(body), capture_output=True, check=True, timeout=60).stdout
        out += (name.ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) + "100644".ljust(8) + str(len(body)).ljust(10) + "`\n").encode()
        out += body + (b"\n" if len(body) % 2 else b"")
        offset += 60 + size + (size & 1)
    return out


class MirrorPolicyTests(unittest.TestCase):
    """The repo-policy.json mirror object, the strict closure reader and the publish.sh --mirror mode."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-mirror-policy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_mirror_fields_match_lab_pref_and_the_mirror_sources_entry(self):
        policy = deploy.load(deploy.REPO_POLICY)
        mirror = policy["mirror"]
        self.assertEqual(tuple(mirror), deploy.MIRROR_POLICY_KEYS)
        self.assertEqual((policy["status"], mirror["origin"]), ("DRAFT", "srrx-mirror"))
        wildcards = [s for s in deploy.deb822((HERE / "repo/lab.pref").read_text(encoding="utf-8"), "lab.pref") if s["package"] == "*"]
        self.assertEqual((wildcards[1]["pin"], wildcards[1]["pin-priority"]), ("release o=" + mirror["origin"], "990"))
        entry = deploy.deb822((HERE / "repo/srrx-mirror.sources").read_text(encoding="utf-8"), "mirror")[0]
        self.assertEqual((entry["suites"], entry["components"], entry["architectures"], entry["signed-by"]),
                         (mirror["codename"], mirror["component"], mirror["architecture"], policy["keyring_path"]))  # one key, one keyring
        self.assertNotEqual(mirror["codename"], policy["codename"])
        self.assertEqual((HERE.parent / mirror["contents"]).resolve(), CLOSURE_FILE.resolve())
        self.assertTrue(CLOSURE_FILE.is_file())

    def test_the_closure_is_read_strictly(self):
        closure = deploy.load(CLOSURE_FILE)
        self.assertEqual(deploy.mirror_closure(CLOSURE_FILE, "arm64"),
                         {(p["package"], p["version"], p["architecture"]): (p["sha256"], p["size"]) for p in closure["packages"]})
        first = closure["packages"][0]
        bad = {"another schema": dict(closure, schema_version=2), "no packages": dict(closure, packages=[]),
               "a repeated package": dict(closure, packages=closure["packages"] + [first]),
               "a short SHA-256": dict(closure, packages=[dict(first, sha256="0" * 63)]),
               "a foreign architecture": dict(closure, packages=[dict(first, architecture="amd64")]),
               "no size": dict(closure, packages=[dict(first, size=0)]),
               "a missing key": dict(closure, packages=[{k: v for k, v in first.items() if k != "version"}])}
        for label, document in bad.items():
            path = self.root / "closure.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.subTest(label), self.assertRaisesRegex(deploy.DeploymentError, "package closure"):
                deploy.mirror_closure(path, "arm64")

    def test_publish_script_has_a_mirror_mode_named_by_the_policy(self):
        script = (HERE / "repo/publish.sh").read_text(encoding="utf-8")
        for needle in ('"${1-}" = --mirror', 'policy["mirror"]', 'names["contents"]', "not exactly the package closure",
                       'repo create -distribution="$codename"', 'repo add "$publication"', "srrx-lab:*+lab[1-9]*_arm64.deb"):
            self.assertIn(needle, script)
        self.assertEqual(script.count("python3 -B -I -"), 1)  # one reader for both publications

    def test_a_zstd_data_member_without_dpkg_deb_fails_closed(self):
        deb = self.root / "z.deb"
        deb.write_bytes(make_deb({"a": b"1"}).replace(b"data.tar.xz ", b"data.tar.zst"))  # same header length
        with patch.object(deploy.subprocess, "Popen", side_effect=OSError("no dpkg-deb")), \
                self.assertRaisesRegex(deploy.DeploymentError, "dpkg-deb unavailable for the data.tar.zst member"):
            deploy.deb_data_inventory(deb)

    def test_verify_repo_command_needs_records_or_a_closure(self):
        result = subprocess.run([sys.executable, "-I", str(HERE / "deploy.py"), "verify-repo", "--repo", "r", "--keyring", "k",
                                 "--fingerprint", "A" * 40, "--sources-entry", "s"], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs --build-record (srrx-lab) or --closure (srrx-mirror)", result.stderr)

    def test_check_repo_usage_lists_the_mirror_subcommand(self):
        # sr-rx-packages.yml reads the subcommands from the first {...} of the usage text.
        out = subprocess.run([sys.executable, "-I", str(HERE / "repo/check_repo.py"), "--help"], capture_output=True, text=True,
                             timeout=120, env=dict(os.environ, COLUMNS="80")).stdout
        self.assertIn("mirror", re.search(r"\{[a-z,-]*\}", out).group(0)[1:-1].split(","))


@unittest.skipUnless(shutil.which("dpkg-deb") and shutil.which("zstd"), "dpkg-deb and zstd needed for a data.tar.zst member")
class ZstdDataMemberTests(unittest.TestCase):
    """deploy.deb_data_inventory reads a data.tar.zst member (Ubuntu archive debs) through dpkg-deb --fsys-tarfile."""

    def test_zstd_and_xz_members_give_the_same_inventory(self):
        with tempfile.TemporaryDirectory(prefix="srrx-zstd-") as temporary:
            xz, zst = Path(temporary) / "x.deb", Path(temporary) / "z.deb"
            xz.write_bytes(rtl_deb("librtlsdr2"))
            zst.write_bytes(zstd_deb(xz.read_bytes()))
            self.assertIn(b"data.tar.zst", zst.read_bytes()[:400])
            self.assertEqual(deploy.deb_data_inventory(zst), deploy.deb_data_inventory(xz))
            data = bytearray(zst.read_bytes())
            data[-8] ^= 0xFF  # inside the zstd frame
            zst.write_bytes(bytes(data))
            with self.assertRaises(deploy.DeploymentError):
                deploy.deb_data_inventory(zst)


@unittest.skipUnless(GPG, "gpg/gpgv not available (SRRX_RELEASE_BUILDER=1 makes this a failure)")
class MirrorRepositoryTests(unittest.TestCase):
    """deploy.verify_repo(closure=...) on a synthetic srrx-mirror publication signed by a throwaway key."""
    setUpClass = classmethod(SignedRepositoryTests.setUpClass.__func__)
    tearDownClass = classmethod(SignedRepositoryTests.tearDownClass.__func__)
    LABEL = "SR-RX mirrored noble packages (image package closure)"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-mirror-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.keyring, self.wrong = self.root / "srrx-lab.gpg", self.root / "other.gpg"
        self.keys.export(self.fpr, self.keyring)
        self.keys.export(self.other, self.wrong)
        self.sources = HERE / "repo/srrx-mirror.sources"
        # Noble-style versions: no +labN rule in the mirror.
        self.packages = [("srrx-closure-data", "2026e-0ubuntu0.24.04.1", "all", make_deb({"usr/share/srrx-closure-data/zone": b"synthetic"})),
                         ("srrx-closure-tool", "1.0-1ubuntu0.24.04.1", "arm64", make_deb({"usr/sbin/srrx-closure-tool": b"\x7fELF synthetic"}))]
        self.closure = closure_file(self.root / "package-closure.json", self.packages)

    def publish(self, packages=None, origin="srrx-mirror", signer=None, extra=()):
        """A signed srrx-mirror publication (dists/noble-mirror) of packages; extra adds pool files."""
        repo = self.root / "repo"
        if repo.exists():
            shutil.rmtree(repo)
        dist = repo / "dists/noble-mirror"
        index = dist / "main/binary-arm64"
        index.mkdir(parents=True)
        stanzas = []
        for name, version, arch, data in packages or self.packages:
            filename = "pool/main/%s/%s/%s_%s_%s.deb" % (name[0], name, name, version, arch)
            (repo / filename).parent.mkdir(parents=True, exist_ok=True)
            (repo / filename).write_bytes(data)
            stanzas.append("Package: %s\nVersion: %s\nArchitecture: %s\nFilename: %s\nSize: %d\nSHA256: %s\n"
                           % (name, version, arch, filename, len(data), sha(data)))
        for filename, data in extra:
            (repo / filename).parent.mkdir(parents=True, exist_ok=True)
            (repo / filename).write_bytes(data)
        text = "\n".join(stanzas).encode()
        (index / "Packages").write_bytes(text)
        (index / "Packages.gz").write_bytes(gzip.compress(text, mtime=0))
        (index / "Release").write_bytes(b"Archive: noble-mirror\nComponent: main\nArchitecture: arm64\n")
        listed = "".join(" %s %d %s\n" % (sha((dist / p).read_bytes()), (dist / p).stat().st_size, p)
                         for p in ("main/binary-arm64/Packages", "main/binary-arm64/Packages.gz", "main/binary-arm64/Release"))
        release = ("Origin: %s\nLabel: %s\nSuite: noble-mirror\nCodename: noble-mirror\nDate: Sat, 07 Nov 2026 00:00:00 UTC\n"
                   "Architectures: arm64\nComponents: main\nSHA256:\n%s" % (origin, self.LABEL, listed))
        (dist / "InRelease").write_bytes(self.keys.clearsign(signer or self.fpr, release))
        return repo

    def verify(self, repo, **kwargs):
        arguments = dict(repo=repo, keyring=self.keyring, fingerprint=self.fpr, build_records=[], sources_entry=self.sources, closure=self.closure)
        arguments.update(kwargs)
        return deploy.verify_repo(**arguments)

    def refused(self, needle, repo, **kwargs):
        with self.assertRaisesRegex(deploy.DeploymentError, needle):
            self.verify(repo, **kwargs)

    def changed(self, index, **change):
        """self.packages with entry index changed (name, version, arch or deb bytes)."""
        packages = list(self.packages)
        name, version, arch, data = packages[index]
        packages[index] = (change.get("name", name), change.get("version", version), change.get("arch", arch), change.get("data", data))
        return packages

    def test_the_mirror_of_exactly_the_closure_passes(self):
        repo = self.publish()
        result = self.verify(repo)
        self.assertEqual((result["status"], result["publication"], result["packages"], result["hardware_ready"]),
                         ("SIGNED_MIRROR_MATCHES_PACKAGE_CLOSURE", "srrx-mirror", 2, False))
        self.assertEqual(result["closure"], {"path": str(self.closure), "sha256": deploy.sha(self.closure), "packages": 2})
        pinned = self.verify(repo, inrelease_sha256=result["inrelease_sha256"], release=True)
        self.assertTrue(pinned["release_path"])
        status = self.root / "status"
        status.write_text("".join("Package: %s\nStatus: hold ok installed\nVersion: %s\n\n" % (n, v) for n, v, _, _ in self.packages), encoding="utf-8")
        self.assertEqual(self.verify(repo, target_status=status)["packages"], 2)  # held at the closure versions: unchanged

    def test_changed_foreign_or_missing_packages_are_refused(self):
        repo = self.publish()
        deb = next(repo.rglob("srrx-closure-tool_*.deb"))
        deb.write_bytes(deb.read_bytes()[:-1] + bytes([deb.read_bytes()[-1] ^ 0xFF]))
        self.refused("pool .deb differs from the signed Packages index", repo)
        changed = make_deb({"usr/sbin/srrx-closure-tool": b"\x7fELF synthetic, one byte else"})
        self.refused("differs from its package closure entry", self.publish(self.changed(1, data=changed)))  # re-signed index, other bytes
        self.refused("differs from its package closure entry", self.publish(self.changed(1, version="1.0-1ubuntu0.24.04.2")))
        self.refused("differs from its package closure entry", self.publish(self.changed(0, arch="arm64")))
        foreign = ("srrx-foreign", "1.0", "all", make_deb({"usr/share/doc/srrx-foreign/README": b"x"}))
        self.refused("is not in the package closure", self.publish(self.packages + [foreign]))
        self.refused("lacks closure packages: srrx-closure-tool", self.publish(self.packages[:1]))
        self.refused("pool holds a file", self.publish(extra=[("pool/main/s/srrx-extra/srrx-extra_1.0_all.deb", b"unlisted")]))
        twice = self.packages + [self.packages[1]]
        self.refused("unsafe, duplicate or unhashed pool entry", self.publish(twice))

    def test_signature_fingerprint_and_origin_rules_are_the_lab_ones(self):
        repo = self.publish()
        self.refused("not a good signature", repo, keyring=self.wrong)
        self.refused("not a good signature", repo, fingerprint=self.other)  # wrong fingerprint, valid signature
        self.refused("not a good signature", self.publish(signer=self.other))
        repo = self.publish()
        inrelease = repo / "dists/noble-mirror/InRelease"
        inrelease.write_text(deploy.gpgv_signed_text(inrelease, self.keyring, [self.fpr]), encoding="utf-8")  # unsigned InRelease
        self.refused("not a good signature", repo)
        repo = self.publish()
        self.refused("InRelease differs from the reviewed release record", repo, inrelease_sha256="0" * 64)
        self.refused("foreign or unexpected repository origin", self.publish(origin="srrx-lab"))
        self.refused("foreign or unexpected repository origin", self.publish(origin="Ubuntu"))

    def test_records_apt_entry_and_release_pin(self):
        repo = self.publish()
        self.refused("has no build records", repo, build_records=[self.closure])
        self.refused("apt entry must be one deb822 stanza", repo, sources_entry=HERE / "repo/srrx-lab.sources")
        entry = self.root / "no-signed-by.sources"
        entry.write_text("".join(l for l in self.sources.read_text(encoding="utf-8").splitlines(True) if not l.startswith("Signed-By:")), encoding="utf-8")
        self.refused("apt entry must be one deb822 stanza", repo, sources_entry=entry)
        self.refused("pinned InRelease", repo, release=True)

    def test_held_kernel_and_receive_only_rules_still_apply(self):
        repo = self.publish()
        status = self.root / "status"
        status.write_text("Package: srrx-closure-tool\nStatus: hold ok installed\nVersion: 0.9-1\n\n", encoding="utf-8")
        self.refused("held package", repo, target_status=status)
        cases = (("linux-image-6.18.2-4-qcom", "6.18.2-4", {"boot/vmlinuz": b"synthetic"}, "kernel, bootloader"),
                 ("rtl-sdr", "2.0.1-2build1", {"usr/share/doc/rtl-sdr/README": b"synthetic"}, "receive-only policy forbids"),  # +labN only
                 ("wsjtx", "2.6.1-1build1", {"usr/share/doc/wsjtx/README": b"synthetic"}, "receive-only policy forbids"),
                 ("srrx-closure-tool", "1.0-1ubuntu0.24.04.1", {"usr/bin/rtl_tcp": b"\x7fELF tcp"}, "receive-only policy refuses the contents"))
        for name, version, files, needle in cases:
            packages = [(name, version, "arm64", make_deb(files))]
            with self.subTest(name):
                self.closure = closure_file(self.root / "package-closure.json", packages)
                self.refused(needle, self.publish(packages))

    def test_check_repo_mirror_tamper_refuses_every_case(self):
        check_repo = load_check_repo("srrx_check_repo_mirror_tamper")
        repo = self.publish()
        with patch.dict(os.environ, {"GNUPGHOME": self.keys.home}):
            result = check_repo.mirror_tamper(repo, self.keyring, self.wrong, self.fpr, self.closure)
        self.assertEqual((result["status"], result["untampered"]), ("MIRROR_TAMPER_CASES_REFUSED", "SIGNED_MIRROR_MATCHES_PACKAGE_CLOSURE"))
        self.assertEqual(set(result["cases"].values()), {"REFUSED"})
        for case in ("changed .deb byte, index re-signed by the same key (srrx-closure-data)", "foreign package re-signed by the same key",
                     "closure package missing, re-signed by the same key (srrx-closure-data)", "wrong fingerprint", "unsigned InRelease",
                     "srrx-lab origin re-signed by the same key", "held package would change (srrx-closure-data)"):
            self.assertIn(case, result["cases"])
        self.assertEqual(len(result["cases"]), 17)
        # resign() signs other contents validly: only the closure rules refuse them
        with patch.dict(os.environ, {"GNUPGHOME": self.keys.home}):
            check_repo.resign(repo, "noble-mirror", self.keyring, self.fpr)
        self.assertEqual(self.verify(repo)["status"], "SIGNED_MIRROR_MATCHES_PACKAGE_CLOSURE")


@unittest.skipUnless(shutil.which("dpkg-deb"), "dpkg-deb needed for the control fields")
class MirrorSelectionTests(unittest.TestCase):
    """check_repo.mirror_selection: every closure deb exactly its entry and free of receive-only findings, or no mirror."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-mirror-selection-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.check_repo = load_check_repo("srrx_check_repo_mirror_selection")

    CONTROL = "Package: %s\nVersion: %s\nArchitecture: %s\nMaintainer: SR-RX unit test\nDescription: synthetic\n"

    def select(self, packages, control=None):
        debs = {}
        for name, version, arch, files in packages:
            path = self.root / ("%s_%s_%s.deb" % (name, version, arch))
            path.write_bytes(control_deb((control or {}).get(name, self.CONTROL % (name, version, arch)), files))
            debs[name] = path
        closure = deploy.load(closure_file(self.root / "closure.json", [(n, v, a, debs[n].read_bytes()) for n, v, a, _ in packages]))
        return self.check_repo.mirror_selection(closure, debs), closure, debs

    def test_the_closure_debs_are_selected_or_the_mirror_is_refused(self):
        good = [("srrx-closure-data", "2026e-0ubuntu0.24.04.1", "all", {"usr/share/srrx-closure-data/zone": b"z"}),
                ("srrx-closure-tool", "1.0-1", "arm64", {"usr/sbin/srrx-closure-tool": b"\x7fELF t"})]
        selected, closure, debs = self.select(good)
        self.assertEqual([(s["package"], s["architecture"], s["data_member"]) for s in selected],
                         [("srrx-closure-data", "all", "data.tar.xz"), ("srrx-closure-tool", "arm64", "data.tar.xz")])
        self.assertEqual(self.check_repo.deb_members(debs["srrx-closure-tool"]), ["debian-binary", "control.tar.xz", "data.tar.xz"])
        debs["srrx-closure-tool"].write_bytes(debs["srrx-closure-tool"].read_bytes() + b"\n")
        with self.assertRaisesRegex(self.check_repo.CheckError, "differs from its package-closure.json entry"):
            self.check_repo.mirror_selection(closure, debs)
        with self.assertRaisesRegex(self.check_repo.CheckError, "control Version differs"):
            self.select(good, control={"srrx-closure-tool": self.CONTROL % ("srrx-closure-tool", "1.0-2", "arm64")})
        for name, version, files, needle in (("srrx-closure-tool", "1.0-1", {"usr/bin/rtl_tcp": b"\x7fELF"}, "TX/control executable"),
                                             ("wsjtx", "2.6.1-1build1", {"usr/share/doc/wsjtx/README": b"x"}, "receive-only policy forbids wsjtx"),
                                             ("sdrangel", "7.22.0-1", {"usr/share/doc/sdrangel/README": b"x"}, "receive-only policy forbids sdrangel"),
                                             ("linux-image-6.18.2-4-qcom", "6.18.2-4", {"boot/x": b"x"}, "never_in_lab_repo_globs: linux-image-*")):
            with self.subTest(name), self.assertRaisesRegex(self.check_repo.CheckError, "cannot be mirrored: .*" + re.escape(needle)):
                self.select([(name, version, "arm64", files)])


@unittest.skipUnless(os.name == "posix" and shutil.which("sh") and shutil.which("python3"), "POSIX sh and python3 needed")
class MirrorPublishRefusalTests(unittest.TestCase):
    """publish.sh --mirror refuses anything but the closure debs before aptly runs (no aptly needed here)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-mirror-publish-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def publish(self, *args):
        return subprocess.run(["sh", str(HERE / "repo/publish.sh")] + [str(a) for a in args], capture_output=True, text=True, timeout=120)

    def test_only_the_closure_debs_get_past_the_check(self):
        closure = deploy.load(CLOSURE_FILE)
        fakes = []
        for entry in closure["packages"]:
            fakes.append(self.root / Path(entry["filename"]).name)
            fakes[-1].write_bytes(b"not the closure deb")
        foreign = self.root / "srrx-foreign_1.0_all.deb"
        foreign.write_bytes(b"x")
        for label, debs in (("other bytes", fakes), ("one missing", fakes[1:]), ("a foreign deb", fakes + [foreign])):
            target = self.root / ("repo-" + label.replace(" ", "-"))
            with self.subTest(label):
                result = self.publish("--mirror", target, "A" * 40, *debs)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("not exactly the package closure deployment/image/package-closure.json", result.stderr)
                self.assertFalse(target.exists())
        tarball = self.root / "x.tar.gz"
        tarball.write_bytes(b"x")
        self.assertIn("not an arm64 or all package", self.publish("--mirror", self.root / "m", "A" * 40, tarball).stderr)
        self.assertIn("not a +labN arm64 package", self.publish(self.root / "lab", "A" * 40, fakes[0]).stderr)  # the lab rule is unchanged


if __name__ == "__main__":
    unittest.main()
