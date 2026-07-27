"""Game mine — glue HTTP exchanges + full SDK session (no redaction)."""

from __future__ import annotations

import unittest
import zlib

from protocol_ast.game_mine import (
    _ja3_ish,
    build_sdk_session,
    format_mine_report,
    glue_http_exchanges,
    merge_bidirectional,
)


class TestGameMine(unittest.TestCase):
    def test_ja3_stable(self) -> None:
        ch = {
            "client_version": "0x0303",
            "cipher_suites": ["0x1301", "0x1302"],
            "extensions": ["server_name", "alpn"],
            "alpn": ["h2", "http/1.1"],
        }
        self.assertEqual(_ja3_ish(ch), _ja3_ish(ch))

    def test_glue_login_heartbeat_keeps_secrets(self) -> None:
        login_req = (
            b"POST /v2/api/sdk/login HTTP/1.1\r\n"
            b"Host: 34.149.80.225\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Content-Length: 28\r\n\r\n"
            b"player_id=13527894&pass=SECRETTOKEN99"
        )
        login_resp = (
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            b'{"result":{"code":0,"msg":"success"},"data":{"app_token":"SECRETTOKEN99",'
            b'"app_uid":13527894,"uid":12782450,"access_token":"LONGSECRETTOKEN"}}'
        )
        hb_req = (
            b"POST /v2/api/sdk/account/heart_beat HTTP/1.1\r\n"
            b"Host: 34.149.80.225\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Content-Length: 20\r\n\r\n"
            b"app_uid=13527894&app_token=SECRETTOKEN99"
        )
        hb_resp = (
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            b'{"result":{"code":0},"data":{"can_play":false,"heartbeat_interval":900,'
            b'"online_limit":"guest_timeout"}}'
        )
        # Pipelined: both requests, then both responses (real PCAPdroid order)
        ex = glue_http_exchanges([login_req, hb_req, login_resp, hb_resp])
        self.assertEqual(len(ex), 2)
        self.assertEqual(ex[0]["path"], "/v2/api/sdk/login")
        self.assertEqual(ex[0]["status"], 200)
        self.assertEqual(ex[0]["request"]["pass"], "SECRETTOKEN99")
        self.assertEqual(ex[0]["response"]["data"]["app_token"], "SECRETTOKEN99")
        self.assertEqual(ex[0]["response"]["data"]["access_token"], "LONGSECRETTOKEN")
        self.assertEqual(ex[1]["path"], "/v2/api/sdk/account/heart_beat")
        self.assertEqual(ex[1]["response"]["data"]["heartbeat_interval"], 900)

        sdk = build_sdk_session([{"sni": [], "exchanges": ex}])
        self.assertEqual(sdk["identity"]["app_token"], "SECRETTOKEN99")
        self.assertEqual(sdk["identity"]["access_token"], "LONGSECRETTOKEN")
        self.assertEqual(sdk["login"]["status"], 200)
        self.assertEqual(sdk["heartbeat"]["response"]["data"]["can_play"], False)
    def test_merge_bidirectional_sni(self) -> None:
        legs = [
            {
                "sport": 40000,
                "dport": 443,
                "stream_bytes": 100,
                "appdata_bytes": 50,
                "sni": ["app.lilithgame.com"],
                "alpn": ["http/1.1"],
                "ja3_ish": ["abc"],
                "client_hellos": 1,
                "client_randoms": ["aa"],
                "decrypt": {"status": "ok", "tls_version": "1.3", "plain_msgs": 1},
                "plains": [
                    b"POST /api/sdk/sls/token HTTP/1.1\r\nHost: app.lilithgame.com\r\n"
                    b"Content-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"
                ],
            },
            {
                "sport": 443,
                "dport": 40000,
                "stream_bytes": 200,
                "appdata_bytes": 80,
                "sni": [],
                "alpn": [],
                "ja3_ish": [],
                "client_hellos": 0,
                "client_randoms": [],
                "decrypt": {"status": "ok", "tls_version": "1.3", "plain_msgs": 1},
                "plains": [
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                    b'{"access_key_id":"STS.AAAA","access_key_secret":"BBBSECRET99"}'
                ],
            },
        ]
        sessions = merge_bidirectional(legs)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["sni"], ["app.lilithgame.com"])
        resp = sessions[0]["exchanges"][0]["response"]
        self.assertEqual(resp["access_key_id"], "STS.AAAA")
        self.assertEqual(resp["access_key_secret"], "BBBSECRET99")

    def test_json_body_separate_tls_record(self) -> None:
        """Lilith SDK: 200 headers in one record, JSON body in the next."""
        login_req = (
            b"POST /v2/api/sdk/login HTTP/1.1\r\nHost: 34.149.80.225\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Content-Length: 11\r\n\r\nplayer_id=1"
        )
        login_hdr = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 80\r\n\r\n"
        login_json = (
            b'{"result":{"code":0,"msg":"success"},"data":{"app_token":"TOK",'
            b'"app_uid":13527894,"access_token":"ACC","uid":9}}'
        )
        hb_req = (
            b"POST /v2/api/sdk/account/heart_beat HTTP/1.1\r\nHost: 34.149.80.225\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Content-Length: 9\r\n\r\napp_uid=1"
        )
        hb_hdr = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 60\r\n\r\n"
        hb_json = b'{"result":{"code":0},"data":{"can_play":false,"heartbeat_interval":900}}'
        for order in (
            [login_req, hb_req, login_hdr, login_json, hb_hdr, hb_json],
            [login_req, hb_req, login_hdr, hb_hdr, login_json, hb_json],
        ):
            ex = glue_http_exchanges(order)
            self.assertEqual(ex[0]["status"], 200, order)
            self.assertEqual(ex[0]["response"]["data"]["app_token"], "TOK")
            self.assertEqual(ex[0]["response"]["data"]["access_token"], "ACC")
            self.assertEqual(ex[1]["response"]["data"]["heartbeat_interval"], 900)
            sdk = build_sdk_session([{"sni": [], "exchanges": ex}])
            self.assertEqual(sdk["identity"]["access_token"], "ACC")
            self.assertIsNotNone(sdk["login"]["response"])
            self.assertIsNotNone(sdk["heartbeat"]["response"])

    def test_gzip_orphan_body(self) -> None:
        html = b'{"ok":true}'
        gz = zlib.compress(html, wbits=16 + zlib.MAX_WBITS)
        plains = [
            b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\nContent-Encoding: gzip\r\n\r\n"
            % len(gz),
            gz,
        ]
        ex = glue_http_exchanges(plains)
        self.assertEqual(ex[0]["status"], 200)
        self.assertEqual(ex[0]["response"], {"ok": True})

    def test_format_includes_sdk(self) -> None:
        text = format_mine_report(
            {
                "file": "x.pcap",
                "keylog": "k",
                "connections": 1,
                "legs": 2,
                "decrypted_connections": 1,
                "sealed_connections": 0,
                "sni_table": [],
                "sealed_game_hosts": [],
                "sessions": [],
                "sdk_session": {
                    "identity": {"app_uid": 1, "app_token": "RAWTOKEN"},
                    "login": {"host": "h", "status": 200, "request": {"player_id": "1"}},
                    "heartbeat": {
                        "host": "h",
                        "status": 200,
                        "response": {
                            "data": {
                                "can_play": False,
                                "heartbeat_interval": 900,
                                "online_limit": "guest_timeout",
                            }
                        },
                    },
                    "endpoints": [],
                },
            }
        )
        self.assertIn("--- SDK SESSION ---", text)
        self.assertIn("interval=900", text)
        self.assertNotIn("redacted", text.lower())


if __name__ == "__main__":
    unittest.main()
