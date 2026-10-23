"""The simulation report is PASS only when every scenario check really held."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from srrx import demo

ROOT = Path(__file__).resolve().parents[2]


class DemoReportTests(unittest.TestCase):
    def test_report_uses_project_mapping_and_stays_simulation(self):
        with patch("srrx.demo.load_mapping", wraps=demo.load_mapping) as mapping:
            report = demo.run_scenario(ROOT)
        mapping.assert_called_once_with(ROOT / "design/E3.json")
        self.assertEqual((report["status"], report["backend"], report["physical_tests_performed"]),
                         ("PASS", "SIMULATION", False))
        self.assertEqual(report["scenarios"][-1]["label"], "fault_latched")

    def test_failed_check_raises_and_writes_no_report(self):
        real = demo.Engine.request

        def refuse_recover(engine, request, now_ms=None):
            if request.get("op") == "recover":
                return {"ok": False, "error": "refused"}
            return real(engine, request, now_ms)
        with patch.object(demo.Engine, "request", refuse_recover):
            with self.assertRaisesRegex(RuntimeError, "explicit recover"):
                demo.run_scenario(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "software-simulation.json"
            with patch("srrx.demo.run_scenario", side_effect=RuntimeError("demo scenario failed: x")):
                with self.assertRaises(RuntimeError):
                    demo.main(["--project", str(ROOT), "--output", str(output)])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
