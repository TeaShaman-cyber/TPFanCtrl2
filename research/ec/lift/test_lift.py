import unittest
from pathlib import Path
from lift import lift, with_oracle, LiftError

class TestLift(unittest.TestCase):
    def test_actual(self):
        src=Path("clamp.pcode").read_text()
        out=lift(src)
        self.assertEqual(out,lift(src))
        self.assertIn("def lifted",out)
        self.assertIn("theorem ordered_clamp",out)
        self.assertNotIn("sorry",out)
    def test_oracle(self):
        src=Path("clamp.pcode").read_text()
        rows=Path("oracle.tsv").read_text()
        self.assertEqual(with_oracle(src,rows).count("example : lifted"),353)
        with self.assertRaises(LiftError): with_oracle(src,rows.splitlines()[0])
    def test_recovery(self):
        src=Path("recovery.pcode").read_text()
        result=lift(src, "recovery")
        self.assertIn("theorem recovery_nondecreasing",result)
        self.assertIn("theorem wrap_counterexample",result)
        self.assertEqual(result,lift(src,"recovery"))
    def test_recovery_bad_store(self):
        src=Path("recovery.pcode").read_text().replace("unique:68200:4 register:0:2","unique:68200:4 register:0:1")
        with self.assertRaises(LiftError): lift(src,"recovery")
    def test_recovery_wrong_store_address(self):
        src=Path("recovery.pcode").read_text().replace("unique:68000:4 const:1e:2","unique:68000:4 const:20:2")
        with self.assertRaises(LiftError): lift(src,"recovery")
    def test_sample(self):
        src=Path("sample.pcode").read_text()
        result=lift(src,"sample")
        self.assertIn("theorem ninth_miss",result)
        self.assertIn("theorem signed_counterexample",result)
        self.assertEqual(result,lift(src,"sample"))
    def test_sample_loop(self):
        src=Path("sample.pcode").read_text().replace("ram:199b4:4","ram:199dc:4")
        with self.assertRaises(LiftError): lift(src,"sample")
    def test_sample_store_width(self):
        src=Path("sample.pcode").read_text().replace("unique:62300:4 register:0:1","unique:62300:4 register:0:2")
        with self.assertRaises(LiftError): lift(src,"sample")
    def test_decay(self):
        src=Path("decay.pcode").read_text()
        result=lift(src,"decay")
        self.assertIn("theorem exact_decay",result)
        self.assertIn("theorem missing_feedback",result)
        self.assertEqual(result,lift(src,"decay"))
    def test_decay_escape(self):
        src=Path("decay.pcode").read_text().replace("ram:3a080:4","ram:3a082:4",1)
        with self.assertRaises(LiftError): lift(src,"decay")
    def test_decay_wrong_store(self):
        src=Path("decay.pcode").read_text().replace("unique:68000:4 const:1e:2","unique:68000:4 const:20:2")
        with self.assertRaises(LiftError): lift(src,"decay")
    def test_unknown(self):
        src=Path("clamp.pcode").read_text().replace("INT_ZEXT","UNSUPPORTED",1)
        with self.assertRaises(LiftError): lift(src)
    def test_wrong_address(self):
        src=Path("clamp.pcode").read_text().replace("const:1c:2","const:1d:2",1)
        with self.assertRaises(LiftError): lift(src)
    def test_backward_branch(self):
        src=Path("clamp.pcode").read_text().replace("ram:19b06:4","ram:19afc:4",1)
        with self.assertRaises(LiftError): lift(src)
    def test_undefined_register(self):
        src=Path("clamp.pcode").read_text().replace("register:8:2 register:0:2","register:a:2 register:0:2",1)
        with self.assertRaises(LiftError): lift(src)
    def test_width_mismatch(self):
        src=Path("clamp.pcode").read_text().replace("register:8:2 register:0:2","register:8:1 register:0:2",1)
        with self.assertRaises(LiftError): lift(src)
    def test_incomplete(self):
        with self.assertRaises(LiftError): lift(Path("clamp.pcode").read_text().replace("EXTRACT_PASS",""))
if __name__=="__main__": unittest.main()
