"""Staging of srrx-passes@.service, its polkit rule and plan directory (candidate only, nothing enabled)."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy

sys.path.insert(0, str(deploy.PROJECT / "software"))
from srrx import pass_jobs, passes


class PassesStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-passes-stage-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_stage_ships_the_unit_rule_and_directory_without_activation(self):
        result = deploy.stage(self.root / "candidate")
        self.assertFalse(result["services_enabled"])
        rootfs = self.root / "candidate/rootfs"
        units = rootfs / "etc/systemd/system"
        source = deploy.PROJECT / "software/systemd" / pass_jobs.UNIT_TEMPLATE
        self.assertEqual((units / pass_jobs.UNIT_TEMPLATE).read_bytes(), source.read_bytes())
        # Started only by labd (polkit) after labd's own release guard: no drop-in, no device wait.
        self.assertFalse((units / (pass_jobs.UNIT_TEMPLATE + ".d")).exists())
        self.assertTrue((units / "srrx.service.d/20-release-guard.conf").is_file())
        self.assertFalse(any(rootfs.rglob("*.wants")))
        for relative, text in pass_jobs.staged_files().items():
            self.assertEqual((rootfs / relative).read_text(), text)
        files = json.loads((self.root / "candidate/stage-files.json").read_text())["files"]
        for relative in ("etc/systemd/system/" + pass_jobs.UNIT_TEMPLATE, pass_jobs.POLKIT_RULE, pass_jobs.TMPFILES):
            self.assertIn(relative, files)
        self.assertTrue((rootfs / "opt/srrx/software/srrx/pass_jobs.py").is_file())
        self.assertFalse((rootfs / "etc/srrx/orbit-allowlist.json").exists())  # never shipped: an operator record

    def test_documented_passes_venv_lock_can_build_the_project(self):
        # The venv's last install step builds /opt/srrx/software with --no-build-isolation, so the
        # setuptools.build_meta backend of software/pyproject.toml must come from the reviewed lock:
        # a CPython 3.12 venv has no setuptools of its own.
        lines = (deploy.PROJECT / "software/DEPLOYMENT.md").read_text(encoding="utf-8").splitlines()
        start = lines.index("python3 -m venv --copies /opt/srrx/passes-venv")
        block = lines[start:lines.index("```", start)]
        self.assertTrue(any("--no-build-isolation --no-deps /opt/srrx/software" in line for line in block))
        self.assertIn('build-backend = "setuptools.build_meta"',
                      (deploy.PROJECT / "software/pyproject.toml").read_text(encoding="utf-8"))
        paragraph = next(line for line in lines[start + len(block):] if line.strip() and line != "```")
        pins = set(re.findall(r"`([A-Za-z0-9_.-]+==[0-9][^`]*)`", paragraph))
        names = {pin.split("==")[0] for pin in pins}
        self.assertEqual(names, {"numpy", "skyfield", "sgp4", "jplephem", "certifi", "setuptools"})
        guest = (deploy.PROJECT / "deployment/linux_lab/wheelhouse-requirements.txt").read_text(encoding="utf-8")
        hashed = {line.split()[0] for line in guest.splitlines() if "--hash=sha256:" in line}
        self.assertLessEqual(pins, hashed)  # every documented pin already has a guest-lock hash
        # The plan_passes allowlist bound is the predictor's, stated with its stable code.
        self.assertEqual(passes.MAX_RECORDS, 64)
        self.assertIn("не більше 64 цілей (`passes.MAX_RECORDS`", paragraph)
        self.assertIn("`PASSES_ALLOWLIST_TOO_LARGE`", paragraph)
        self.assertIn("PASSES_ALLOWLIST_TOO_LARGE", pass_jobs.ERRORS)

    def test_deploy_skips_the_guard_for_exactly_this_template(self):
        # stage() skips the release-guard drop-in for every RELEASE_GUARD_EXEMPT unit name.
        self.assertIn(pass_jobs.UNIT_TEMPLATE, deploy.RELEASE_GUARD_EXEMPT)
        text = Path(deploy.__file__).read_text(encoding="utf-8")
        self.assertIn("if unit.name in RELEASE_GUARD_EXEMPT:", text)


if __name__ == "__main__":
    unittest.main()
