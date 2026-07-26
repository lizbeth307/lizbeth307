"""SIGNAL SCAN CLI smoke."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scan_app


class TestScanApp(unittest.TestCase):
    def test_help(self) -> None:
        self.assertEqual(scan_app.main(["help"]), 0)

    def test_unknown(self) -> None:
        self.assertEqual(scan_app.main(["nope"]), 2)

    def test_sdk_missing(self) -> None:
        with mock.patch.object(scan_app, "_sdk_path", return_value=None):
            self.assertEqual(scan_app.cmd_sdk(), 1)

    def test_unpin_missing_launcher(self) -> None:
        with mock.patch.object(scan_app, "UNPIN", Path("/nonexistent/unpin")):
            self.assertEqual(scan_app.cmd_unpin(), 1)

    def test_unpin_runs_launcher(self) -> None:
        with tempfile.NamedTemporaryFile(prefix="unpin-", delete=False) as fh:
            path = Path(fh.name)
        try:
            with mock.patch.object(scan_app, "UNPIN", path):
                with mock.patch.object(scan_app, "_run", return_value=0) as run:
                    self.assertEqual(scan_app.main(["unpin", "guide"]), 0)
                    run.assert_called_once()
                    args = run.call_args[0][0]
                    self.assertEqual(args[0], "bash")
                    self.assertEqual(args[1], str(path))
                    self.assertIn("guide", args)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
