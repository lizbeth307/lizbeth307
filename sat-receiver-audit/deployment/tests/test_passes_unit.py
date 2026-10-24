"""Staging of srrx-passes@.service, its polkit rule and plan directory (candidate only, nothing enabled)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy

sys.path.insert(0, str(deploy.PROJECT / "software"))
from srrx import pass_jobs


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

    def test_deploy_skips_the_guard_for_exactly_this_template(self):
        text = Path(deploy.__file__).read_text(encoding="utf-8")
        self.assertIn('if unit.name == "' + pass_jobs.UNIT_TEMPLATE + '":', text)


if __name__ == "__main__":
    unittest.main()
