"""Pick pcap that overlaps keylog secrets."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protocol_ast.find_keylog import pick_pcap_for_keylog


class TestPair(unittest.TestCase):
    def test_prefers_overlapping_pcap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            old = d / "old.pcap"
            good = d / "good.pcap"
            key = d / "sslkeylogfile.txt"
            old.write_bytes(b"\x00" * 24)
            good.write_bytes(b"\x00" * 24)
            key.write_text("CLIENT_TRAFFIC_SECRET_0 " + "ab" * 32 + " " + "cd" * 48 + "\n")
            with mock.patch(
                "protocol_ast.find_keylog.count_keylog_overlap",
                side_effect=lambda p, k: 2 if Path(p).name == "good.pcap" else 0,
            ), mock.patch(
                "protocol_ast.termux_update.iter_pcaps_under",
                return_value=[],
            ):
                path, ov, msg = pick_pcap_for_keylog(
                    key, seed_paths=[old, good], max_candidates=4
                )
            self.assertEqual(path, good)
            self.assertEqual(ov, 2)
            self.assertIn("overlap=2", msg)


if __name__ == "__main__":
    unittest.main()
