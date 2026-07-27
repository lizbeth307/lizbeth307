"""CLI integration tests for discover_protocol_ast.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "discover_protocol_ast.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class TestDiscoverScript(unittest.TestCase):
    def test_demo_exits_zero(self):
        proc = run_cli("demo", "--count", "20", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["success_rate"], 0.95)
        self.assertIn("format", data)

    def test_gen_discover_parse_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            hex_path = Path(tmp) / "corpus.hex"
            fmt_path = Path(tmp) / "format.json"

            gen = run_cli("gen-corpus", "-o", str(hex_path), "--count", "25")
            self.assertEqual(gen.returncode, 0, gen.stderr)
            self.assertTrue(hex_path.exists())

            disc = run_cli(
                "discover", "-i", str(hex_path), "-o", str(fmt_path), "--json"
            )
            self.assertEqual(disc.returncode, 0, disc.stderr)
            fmt = json.loads(fmt_path.read_text())
            kinds = [f["kind"] for f in fmt["fields"]]
            self.assertIn("length", kinds)
            self.assertIn("payload", kinds)

            parse = run_cli("parse", "-f", str(fmt_path), "-i", str(hex_path), "--json")
            self.assertEqual(parse.returncode, 0, parse.stderr)
            parsed = json.loads(parse.stdout)
            self.assertGreaterEqual(parsed["success_rate"], 0.95)

    def test_online_mode(self):
        proc = run_cli("online", "--count", "40", "--refine-every", "8", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["success_rate"], 0.95)


if __name__ == "__main__":
    unittest.main()
