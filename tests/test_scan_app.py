"""SIGNAL SCAN CLI smoke."""

from __future__ import annotations

import unittest
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


if __name__ == "__main__":
    unittest.main()
