import json
import unittest
from pathlib import Path
from wolfram_witness import validate, expected, render, parse_result, classify

class WitnessTests(unittest.TestCase):
    def setUp(self):
        self.model=json.loads(Path("reachability-example.json").read_text())
    def test_baseline(self):
        m=validate(self.model)
        r=expected(m)
        self.assertEqual(r["edges"],77)
        self.assertEqual(r["saturatedReachable"],list(range(10,20))+[21])
        self.assertEqual(len(r["components"]),2)
        self.assertEqual(len(r["resetComponents"]),1)
    def test_changed_edge(self):
        self.model["edges"].append([10,0])
        self.model["reset_edges"]=sorted(set(map(tuple,self.model["reset_edges"]))|{(10,0)})
        self.model["reset_edges"]=[list(x) for x in self.model["reset_edges"]]
        m=validate(self.model)
        self.assertEqual(len(expected(m)["components"]),1)
        self.assertIn("DirectedEdge[10,0]",render(m))
    def test_bad_endpoint(self):
        self.model["edges"].append([0,99])
        with self.assertRaises(ValueError): validate(self.model)
    def test_noninteger(self):
        self.model["states"][0]=True
        with self.assertRaises(ValueError): validate(self.model)
    def test_duplicate_edge(self):
        self.model["edges"].append(self.model["edges"][0])
        with self.assertRaises(ValueError): validate(self.model)
    def test_output(self):
        e=expected(validate(self.model))
        raw="Out[1]= "+json.dumps(json.dumps(e))
        self.assertEqual(parse_result(raw),e)
        self.assertEqual(classify(0,raw,e),"MATCH")
        e2=dict(e,edges=78)
        self.assertEqual(classify(0,raw,e2),"MISMATCH")
        self.assertEqual(classify(1,raw,e),"DEGRADED")
        self.assertEqual(classify(0,"Failure[timeout]",e),"DEGRADED")
        self.assertEqual(classify(0,"Warning: error\n"+raw,e),"DEGRADED")
        self.assertEqual(classify(0,raw+"\n"+raw,e),"DEGRADED")
    def test_wrong_type(self):
        e=expected(validate(self.model)); e["vertices"]=22.0
        self.assertEqual(classify(0,"Out[1]= "+json.dumps(json.dumps(e)),expected(validate(self.model))),"MISMATCH")
