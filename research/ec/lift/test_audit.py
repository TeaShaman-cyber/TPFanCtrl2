import unittest
from pathlib import Path
from audit import scan

class TestAudit(unittest.TestCase):
    def test_actual_sites(self):
        hits=scan(Path("fan-audit.pcode").read_text())
        self.assertIn(("signed-word-difference",0x19d82,0x19d8a),hits)
        self.assertIn(("known-wide-return-store",0x192ee,0x192f2),hits)
    def test_no_signed_comparison(self):
        s=Path("fan-audit.pcode").read_text().replace("INT_SLESS","INT_LESS")
        self.assertNotIn(("signed-word-difference",0x19d82,0x19d8a),scan(s))
    def test_no_known_wide_call(self):
        s=Path("fan-audit.pcode").read_text().replace("ram:192fe:4","ram:192fc:4")
        self.assertNotIn(("known-wide-return-store",0x192ee,0x192f2),scan(s))
    def test_incomplete(self):
        with self.assertRaises(ValueError): scan(Path("fan-audit.pcode").read_text().replace("EXTRACT_PASS",""))
