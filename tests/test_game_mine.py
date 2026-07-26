"""Game mine helpers — fingerprints + report formatting."""

from __future__ import annotations

import unittest

from protocol_ast.game_mine import _ja3_ish, _protobuf_strings, _strings, format_mine_report


class TestGameMine(unittest.TestCase):
    def test_ja3_stable(self) -> None:
        ch = {
            "client_version": "0x0303",
            "cipher_suites": ["0x1301", "0x1302"],
            "extensions": ["server_name", "alpn"],
            "alpn": ["h2", "http/1.1"],
        }
        a = _ja3_ish(ch)
        b = _ja3_ish(ch)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 32)

    def test_strings_and_protobuf(self) -> None:
        # field 1 string "RqdServer", field 2 varint 2
        blob = b"\x0a\x09RqdServer\x10\x02"
        ss = _protobuf_strings(blob)
        self.assertTrue(any("RqdServer" in s for s in ss), ss)
        self.assertIn("RqdServer", _strings(blob))

    def test_format_report(self) -> None:
        text = format_mine_report(
            {
                "file": "x.pcap",
                "keylog": "k.txt",
                "connections": 2,
                "decrypted_connections": 1,
                "sealed_connections": 1,
                "sni_table": [
                    {
                        "sni": "app-global.lilithgame.com",
                        "conns": 1,
                        "appdata_bytes": 90000,
                        "stream_bytes": 100000,
                        "decrypted_conns": 0,
                        "plain_msgs": 0,
                        "alpn": {"h2": 1},
                        "ja3_ish_top": [("abcd", 1)],
                        "game_like": True,
                        "sdk_like": False,
                    }
                ],
                "http_requests": [],
                "protobuf_strings": ["RqdServer"],
                "strings": ["googleplay"],
                "sealed_game_hosts": [
                    {
                        "sni": "app-global.lilithgame.com",
                        "conns": 1,
                        "appdata_bytes": 90000,
                        "ja3_ish_top": [("abcd", 1)],
                    }
                ],
                "open_hosts": [],
                "connections_detail": [],
            }
        )
        self.assertIn("GAME", text)
        self.assertIn("SEALED", text)
        self.assertIn("RqdServer", text)


if __name__ == "__main__":
    unittest.main()
