"""Termux update helpers — newest pcap + URL resolve."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protocol_ast.termux_update import file_url, pick_newest_pcap, resolve_base


class TestPickNewest(unittest.TestCase):
    def test_picks_newest_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            a = d / "a.pcap"
            b = d / "b.pcap"
            a.write_bytes(b"\x00" * 24)
            b.write_bytes(b"\x00" * 24)
            # bump mtime of b
            import os
            import time

            now = time.time()
            os.utime(a, (now - 100, now - 100))
            os.utime(b, (now, now))
            picked = pick_newest_pcap([str(a), str(b)])
            self.assertEqual(picked, b)

    def test_ignores_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = d / "only.pcap"
            f.write_bytes(b"\x00" * 8)
            picked = pick_newest_pcap([str(d / "missing.pcap"), str(f)])
            self.assertEqual(picked, f)


class TestResolve(unittest.TestCase):
    def test_file_url_jsdelivr(self) -> None:
        u = file_url("https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@abc", "analyze_pcap.py")
        self.assertEqual(u, "https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@abc/analyze_pcap.py")

    def test_resolve_fallback(self) -> None:
        with mock.patch("protocol_ast.termux_update._fetch", side_effect=RuntimeError("no net")):
            base, ref = resolve_base("cursor/signal-pipeline-p4-a4e6")
        self.assertIn("raw.githubusercontent.com", base)
        self.assertIn("cursor/signal-pipeline-p4-a4e6", ref)


if __name__ == "__main__":
    unittest.main()
