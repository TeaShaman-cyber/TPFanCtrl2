import unittest
from pathlib import Path
from dispatch_graph import table, observed, graph

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.ir=Path("dispatcher.pcode").read_text()
        self.trace=Path("dispatch.trace").read_text()
    def test_table(self):
        t=table(self.ir)
        self.assertEqual(t[(11,8)],0x199a6)
        self.assertEqual(t[(12,0)],0x199ea)
        self.assertIsNone(t[(6,2)])
        self.assertEqual(t[(10,None)],0x19af2)
        self.assertNotIn((10,0),t)
        self.assertNotIn((15,0),t)
        self.assertIn((16,0),t)
    def test_trace(self):
        rows=observed(self.trace,table(self.ir))
        self.assertEqual(len(rows),429)
        self.assertTrue(any(a[:2]==(11,8) and b[:2]==(12,0) for a,b in rows))
        self.assertTrue(any(a[:2]==(12,0) and a[2]==25 and b[2]==500 for a,b in rows))
    def test_bad_target(self):
        s=self.trace.replace("SELECT 11 8 199a6","SELECT 11 8 199ea",1)
        self.assertNotEqual(s,self.trace)
        with self.assertRaises(ValueError): observed(s,table(self.ir))
    def test_missing_selection(self):
        s=self.trace.splitlines()
        i=next(i for i,x in enumerate(s) if x.startswith("SELECT"))
        with self.assertRaises(ValueError): observed("\n".join(s[:i]+s[i+1:]),table(self.ir))
    def test_bad_table_pointer(self):
        s=self.ir.replace("TABLE 55334 1cd53","TABLE 55334 ffffffff",1)
        with self.assertRaises(ValueError): table(s)
    def test_incomplete(self):
        with self.assertRaises(ValueError): table(self.ir.replace("EXTRACT_PASS",""))
    def test_observed_graph(self):
        g=graph(observed(self.trace,table(self.ir)))
        self.assertIn(g["initial"],g["states"])
        self.assertNotEqual(g["initial"],g["saturated"])
        self.assertEqual(g["edges"],g["reset_edges"])
        self.assertEqual(g["missing_edges"],[])
