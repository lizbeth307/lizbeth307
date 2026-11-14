"""Unit tests of build/kicad/boards/PWR_A/board_audit.py (W2 PWR-L6-SCRIPT review fixes): rule H-TRIM on the drawn board."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # sat-receiver-audit
sys.path.insert(0, str(ROOT / 'pcb'))
sys.path.insert(0, str(ROOT / 'build/kicad/boards/PWR_A'))
import board_audit as ba  # noqa: E402


class HTrimAuditTests(unittest.TestCase):
    """RV-PWRL6-PRE-C-04: under a PWR-B THT pin field (+ window_margin) a part needs a read height of at most the zone height; a part
    without a height or with a lower-bound height is a finding too (synthesis htrim_decision), not an 'unverified' note."""
    FIELDS = [{'ref': 'J9', 'field_mm': [10.0, 10.0, 12.0, 20.0]}]

    def test_unread_and_lower_bound_heights_are_findings(self):
        spec = {'heights': {'C1': 2.7, 'C2': 2.8, 'C4': 2.5, 'C5': 9.0}, 'heights_lower_bound': {'refs': ['C4']}}
        boxes = {'C1': (11, 11, 12, 12), 'C2': (11, 13, 12, 14), 'C3': (11, 15, 12, 16), 'C4': (11, 17, 12, 18),
                 'C5': (30, 30, 31, 31), 'C6': (12.4, 20.4, 13, 21)}  # C5 far away, C6 inside the 0.5 mm margin
        spec['heights']['C6'] = 2.0
        rows, findings = ba.htrim_check(spec, boxes, self.FIELDS, 2.7, 0.5)
        self.assertEqual(sorted(f['item'] for f in findings), ['C2', 'C3', 'C4'])
        self.assertEqual(sorted(r['ref'] for r in rows), ['C1', 'C2', 'C3', 'C4', 'C6'])
        self.assertTrue(any('not read' in f['detail'] for f in findings if f['item'] == 'C3'))
        self.assertTrue(any('lower bound' in f['detail'] for f in findings if f['item'] == 'C4'))

    def test_clear_board(self):
        rows, findings = ba.htrim_check({'heights': {'C1': 1.0}}, {'C1': (11, 11, 12, 12)}, self.FIELDS, 2.7, 0.5)
        self.assertEqual(findings, [])
        self.assertEqual([r['ok'] for r in rows], [True])


if __name__ == '__main__':
    unittest.main()
