"""Streaming living-signal agent tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from protocol_ast.fixtures.real_protocols import DNS_MESSAGES
from protocol_ast.pcap_build import ethernet_ipv4_udp, write_pcap
from protocol_ast.stream_agent import StreamAgent, analyze_pcap_streaming, events_to_report


class TestStreamAgent(unittest.TestCase):
    def test_feed_emits_every_n(self) -> None:
        agent = StreamAgent(every_n=3, min_messages=2, max_depth=3, max_emits_per_flow=3)
        events = []
        for m in DNS_MESSAGES[:7]:
            ev = agent.feed("UDP:53", m)
            if ev:
                events.append(ev)
        events.extend(agent.flush())
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0].flow, "UDP:53")
        self.assertTrue(events[0].path)
        # phone-safe: never spam emits
        self.assertLessEqual(len(events), 3)

    def test_analyze_pcap_streaming(self) -> None:
        frames = [
            ethernet_ipv4_udp((10, 0, 0, 1), (1, 1, 1, 1), 53000, 53, m)
            for m in DNS_MESSAGES[:10]
        ]
        with tempfile.TemporaryDirectory() as td:
            pcap = Path(td) / "dns.pcap"
            write_pcap(pcap, frames)
            events = analyze_pcap_streaming(pcap, every_n=4, max_depth=3, max_flows=3)
            self.assertGreaterEqual(len(events), 1)
            self.assertLessEqual(len(events), 3)
            rep = events_to_report(events)
            self.assertEqual(rep["count"], len(events))


if __name__ == "__main__":
    unittest.main()
