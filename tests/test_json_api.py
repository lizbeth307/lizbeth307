"""JSON API schema peel tests."""

from __future__ import annotations

import json
import unittest

from protocol_ast.json_api import json_api_deep, looks_like_json_api
from protocol_ast.signal import propagate_flow


class TestJsonApi(unittest.TestCase):
    def test_schema_merge(self) -> None:
        bodies = [
            json.dumps({"user": {"id": "abc-123", "email": "a@b.co"}, "items": [{"name": "x"}]}).encode(),
            json.dumps({"user": {"id": "def-456", "email": "c@d.co"}, "items": [{"name": "y"}], "ok": True}).encode(),
        ]
        self.assertTrue(looks_like_json_api(bodies))
        deep = json_api_deep(
            bodies,
            headers=[{":status": "200", ":path": "/api/v1/user", ":authority": "api.example.com"}],
        )
        self.assertEqual(deep["kind"], "json_api")
        self.assertEqual(deep["bodies"], 2)
        self.assertGreaterEqual(deep["field_count"], 3)
        paths = [f["path"] for f in deep["fields"]]
        self.assertTrue(any(p.startswith("user") for p in paths))
        self.assertIn("api.example.com/api/v1/user", deep["paths"])

    def test_signal_spawns_json_api_child(self) -> None:
        bodies = [
            b'{"status":"ok","data":{"n":1}}',
            b'{"status":"ok","data":{"n":2}}',
            b'{"status":"err","data":null}',
        ]
        # Pretend http2_data leaf via high-entropy child path: use app_body peel
        # by feeding through a Signal that already looks like decrypted bodies.
        from protocol_ast.signal import Signal

        sig = Signal(label="TCP:443/http2_data", messages=bodies, flow="TCP:443", depth=1)
        sig.deep = {"kind": "http2_data", "headers": [{":path": "/v1", ":status": "200"}]}
        sig.entropy = "high"
        sig.propagate(max_depth=3)
        notes = "\n".join(sig.format_notes())
        self.assertIn("json_api", notes)
        self.assertTrue(any(c.label.endswith("json_api") for c in sig.children))


if __name__ == "__main__":
    unittest.main()
