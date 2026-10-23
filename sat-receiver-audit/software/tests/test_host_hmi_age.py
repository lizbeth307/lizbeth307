from pathlib import Path
import unittest
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.link import SimLink

ROOT = Path(__file__).resolve().parents[2]


def sample():
    return {"ok":True,"fresh":True,"age_ms":0,"keys":1,"presses":[1,0,0,0,0,0,0,0],
            "encoders":[7,-2],"lux":100.5,"lux_valid":True,"lux_age_ms":800,
            "sequence":5,"generation":0,"error":None}


class HostHMIAgeTests(unittest.TestCase):
    def setUp(self):
        self.engine=Engine(SimHardware(),SimLink(ROOT))
        self.engine.now_ms=1000
        self.engine.last_status_ms=1000
        self.engine.hmi_sample=(1000,sample())
    def tearDown(self):self.engine.close()

    def test_rx_age_is_added_and_stale_keys_are_not_replayed(self):
        self.assertEqual(self.engine.status()['hmi']['age_ms'],100)
        self.engine.now_ms=1400
        h=self.engine.status()['hmi']
        self.assertFalse(h['fresh']);self.assertIsNone(h['presses']);self.assertEqual(h['keys'],0)

    def test_lux_expires_independently_from_recent_keys(self):
        value=sample();value['lux_age_ms']=1900
        self.engine.hmi_sample=(1000,value)
        h=self.engine.status()['hmi']
        self.assertTrue(h['fresh']);self.assertFalse(h['lux_valid']);self.assertIsNone(h['lux'])

    def test_malformed_counter_age_or_mask_is_unavailable(self):
        for field,value in [('keys',True),('keys',256),('presses',[0]*7),('encoders',[2**31,0]),
                            ('age_ms',-1),('age_ms',False),('sequence',2**32)]:
            s=sample();s[field]=value;self.engine.hmi_sample=(1000,s)
            self.assertFalse(self.engine.status()['hmi']['fresh'],field)

    def test_new_session_clears_old_hmi_and_imu_immediately(self):
        self.engine.imu_sample=(1000,{'old':True})
        self.engine._receive({'v':1,'t':'HELLO','s':123,'q':0,'p':{}})
        self.assertIsNone(self.engine.hmi_sample);self.assertIsNone(self.engine.imu_sample)
