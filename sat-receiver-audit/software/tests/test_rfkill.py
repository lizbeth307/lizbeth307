"""rfkill second layer: exact kernel block events, never unblock, fail-closed check."""
from pathlib import Path
import tempfile
import unittest

from srrx import rfkill


class RfkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-rfkill-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def switch(self, name, kind, soft="0", hard="0"):
        path = self.root / "sys" / name
        path.mkdir(parents=True)
        (path / "type").write_text(kind + "\n")
        (path / "soft").write_text(soft + "\n")
        (path / "hard").write_text(hard + "\n")
        return path

    def test_events_match_kernel_change_all_block_layout(self):
        # struct rfkill_event v1: u32 idx, u8 type, u8 op, u8 soft, u8 hard (8 bytes)
        self.assertEqual(rfkill.block_event("wlan"), b"\x00\x00\x00\x00\x01\x03\x01\x00")
        self.assertEqual(rfkill.block_event("bluetooth"), b"\x00\x00\x00\x00\x02\x03\x01\x00")
        with self.assertRaises(KeyError):
            rfkill.block_event("all")

    def test_block_writes_wlan_and_bluetooth_only_as_blocks(self):
        device = self.root / "rfkill-device"
        device.write_bytes(b"")
        rfkill.block(str(device))
        data = device.read_bytes()
        self.assertEqual(data, rfkill.block_event("wlan") + rfkill.block_event("bluetooth"))
        self.assertTrue(all(data[i + 6] == 1 for i in range(0, len(data), 8)))  # soft=1, never 0
        with self.assertRaises(OSError):
            rfkill.block(str(self.root / "missing" / "rfkill"))

    def test_check_fails_while_any_wlan_or_bluetooth_switch_is_unblocked(self):
        sysfs = self.root / "sys"
        self.switch("rfkill0", "wlan", soft="1")
        self.switch("rfkill1", "bluetooth", hard="1")
        self.switch("rfkill2", "gps")
        self.assertEqual(rfkill.unblocked(sysfs), [])
        self.assertEqual(rfkill.main(["check", "--sysfs", str(sysfs)]), 0)
        self.switch("rfkill3", "bluetooth")
        self.assertEqual(rfkill.unblocked(sysfs), ["rfkill3 bluetooth"])
        self.assertEqual(rfkill.main(["check", "--sysfs", str(sysfs)]), 1)
        self.assertEqual(rfkill.main(["block", "--device", str(self.root / "missing"), "--sysfs", str(sysfs)]), 2)


if __name__ == "__main__":
    unittest.main()
