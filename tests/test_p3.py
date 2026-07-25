"""Tests for human field names and terminal/HTML dissector."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from protocol_ast.field_names import enrich_format
from protocol_ast.fixtures.real_protocols import DNS_MESSAGES
from protocol_ast.pcap_build import ethernet_ipv4_udp, write_pcap
from protocol_ast.terminal_dissect import dissect_flow_text, dissect_packet, export_flow_html
from protocol_ast.wireshark_export import format_to_lua


class TestFieldNames(unittest.TestCase):
    def test_dns_fields_renamed(self) -> None:
        fmt = {
            "fields": [
                {"name": "byte_0", "offset": 0, "size": 1, "kind": "variable"},
                {"name": "byte_1", "offset": 1, "size": 1, "kind": "variable"},
                {"name": "enum_2", "offset": 2, "size": 1, "kind": "enum"},
            ]
        }
        out = enrich_format("UDP:53", fmt)
        self.assertEqual(out["fields"][0]["name"], "transaction_id")
        self.assertEqual(out["fields"][2]["name"], "flags")

    def test_lua_uses_display_labels(self) -> None:
        fmt = enrich_format(
            "UDP:53",
            {
                "endian": "be",
                "fields": [
                    {"name": "transaction_id", "offset": 0, "size": 2, "kind": "enum"},
                    {"name": "flags", "offset": 2, "size": 2, "kind": "enum"},
                    {"name": "payload", "offset": 12, "size": -1, "kind": "payload"},
                ],
            },
        )
        lua = format_to_lua(fmt, flow="UDP:53")
        self.assertIn("DNS transaction ID", lua)
        self.assertIn("DNS flags", lua)


class TestTerminalDissect(unittest.TestCase):
    def test_dns_tree(self) -> None:
        msg = DNS_MESSAGES[0]
        tree = dissect_packet("UDP:53", msg)
        text = "\n".join(tree.label for tree in [tree])  # noqa: PLW2901
        self.assertIn("DNS", tree.label)

    def test_flow_text_contains_domain(self) -> None:
        out = dissect_flow_text("UDP:53", DNS_MESSAGES[:2], limit=2)
        self.assertIn("Packet #0", out)
        self.assertIn("Question", out)

    def test_html_export(self) -> None:
        html = export_flow_html("UDP:53", DNS_MESSAGES[:2], limit=2)
        self.assertIn("<html>", html.lower())
        self.assertIn("UDP:53", html)

    def test_cli_dissect_on_pcap(self) -> None:
        frames = [
            ethernet_ipv4_udp((10, 0, 0, 2), (10, 0, 0, 1), 40000 + i, 53, msg)
            for i, msg in enumerate(DNS_MESSAGES[:3])
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "dns.pcap"
            write_pcap(pcap, frames)
            import subprocess
            import sys

            root = Path(__file__).resolve().parents[1]
            proc = subprocess.run(
                [sys.executable, str(root / "analyze_pcap.py"), str(pcap), "--dissect", "--flow", "53", "--limit", "2"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("transaction_id", proc.stdout)


if __name__ == "__main__":
    unittest.main()
