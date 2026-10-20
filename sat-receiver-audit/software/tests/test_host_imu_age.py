from pathlib import Path
import unittest
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SimLink

ROOT = Path(__file__).resolve().parents[2]


class HostImuAgeTests(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(SimHardware(), SimLink(ROOT))
        self.engine.tick(1000)

    def tearDown(self): self.engine.close()

    def sample(self, age=150, quaternion=None):
        self.engine.imu_sample = (1000, {"ok": True, "fresh": True, "age_ms": age,
            "quaternion": quaternion or [0, 0, 0, 1], "status": 2, "report_id": 5})

    def test_source_and_host_age_accumulate_and_expire(self):
        self.sample()
        self.assertEqual(self.engine.status()["imu"]["age_ms"], 250)
        self.engine.now_ms = 1250
        self.assertFalse(self.engine.status()["imu"]["fresh"])
        self.assertIsNone(self.engine.status()["imu"]["quaternion"])

    def test_invalid_age_norm_and_sensor_accuracy_are_not_live(self):
        for age, quaternion in [(-100, None), (500, None), (150, [1, 1, 1, 1])]:
            self.sample(age, quaternion)
            self.assertFalse(self.engine.status()["imu"]["fresh"])
        self.sample()
        self.engine.imu_sample[1]["status"] = 0
        self.assertFalse(self.engine.status()["imu"]["fresh"])

    def test_host_scheduling_gap_discards_cached_imu(self):
        self.sample()
        self.engine.tick(1200)
        self.assertIsNone(self.engine.imu_sample)
        self.assertFalse(self.engine.status()["imu"]["fresh"])
