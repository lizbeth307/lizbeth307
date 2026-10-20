from pathlib import Path
import unittest
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SimLink

ROOT = Path(__file__).resolve().parents[2]


class ModeRecoveryTests(unittest.TestCase):
    def test_mode_is_staged_while_disarmed_and_applied_during_explicit_arm(self):
        engine = Engine(SimHardware(), SimLink(ROOT))
        try:
            engine.tick(0)
            self.assertTrue(engine.request({"op": "mode", "value": "lab"})["ok"])
            self.assertTrue(engine.request({"op": "arm"})["ok"])
            for now in range(20, 900, 20): engine.tick(now)
            self.assertTrue(engine.policy.armed)
            self.assertEqual(engine.policy.mode, "lab")
            self.assertFalse(engine.request({"op": "mode", "value": "field"})["ok"])
            engine.request({"op": "disarm"})
            for now in range(900, 1200, 20): engine.tick(now)
            self.assertTrue(engine.request({"op": "mode", "value": "field"})["ok"])
            self.assertFalse(any(v for k, v in engine.hardware.outputs.items() if k.startswith("EN_")))
        finally:
            engine.close()
