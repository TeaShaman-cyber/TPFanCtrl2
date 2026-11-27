"""Read-only external graph witness. One validated graph, two independent algorithms."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import subprocess

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate(m):
    if not isinstance(m,dict) or set(m)!={"states","edges","reset_edges","missing_edges","initial","saturated"}:
        raise ValueError("graph schema")
    s=m["states"]
    if not isinstance(s,list) or not 1<=len(s)<=256 or any(type(x) is not int or not 0<=x<=65535 for x in s) or len(set(s))!=len(s):
        raise ValueError("state domain")
    for name in ("initial","saturated"):
        if type(m[name]) is not int or m[name] not in s: raise ValueError("initial state")
    result=dict(m,states=sorted(s))
    for name in ("edges","reset_edges","missing_edges"):
        edges=m[name]
        if not isinstance(edges,list) or len(edges)>4096: raise ValueError("edge domain")
        if any(not isinstance(e,list) or len(e)!=2 or any(type(x) is not int or x not in s for x in e) for e in edges):
            raise ValueError("edge endpoint")
        if len(set(map(tuple,edges)))!=len(edges): raise ValueError("duplicate edge")
        result[name]=sorted(edges)
    if not set(map(tuple,result["edges"]))<=set(map(tuple,result["reset_edges"])) or not set(map(tuple,result["missing_edges"]))<=set(map(tuple,result["edges"])):
        raise ValueError("edge subset")
    return result

def expected(m):
    s=m["states"]
    def closure(edges,start):
        adj={v:[] for v in s}
        for a,b in edges: adj[a].append(b)
        q=deque([start]); seen={start}
        while q:
            for b in adj[q.popleft()]:
                if b not in seen: seen.add(b);q.append(b)
        return seen
    def components(edges):
        reach={v:closure(edges,v) for v in s}
        return [list(c) for c in sorted({tuple(sorted(w for w in reach[v] if v in reach[w])) for v in s})]
    return {"vertices":len(s),"edges":len(m["edges"]),
            "reachable":sorted(closure(m["edges"],m["initial"])),
            "saturatedReachable":sorted(closure(m["edges"],m["saturated"])),
            "components":components(m["edges"]),"resetComponents":components(m["reset_edges"])}

def render(m):
    def arr(xs): return "{"+",".join(map(str,xs))+"}"
    def edges(xs): return "{"+",".join(f"DirectedEdge[{a},{b}]" for a,b in xs)+"}"
    return f'''Module[{{s={arr(m["states"])},g,h,c,out}},
g=Graph[s,{edges(m["edges"])}];
h=Graph[s,{edges(m["reset_edges"])}];
c[x_]:=Sort[DeleteDuplicates[Table[Sort[Intersection[VertexOutComponent[x,i],VertexInComponent[x,i]]],{{i,s}}]]];
out=<|"vertices"->VertexCount[g],"edges"->EdgeCount[g],"reachable"->Sort[VertexOutComponent[g,{m["initial"]}]],"saturatedReachable"->Sort[VertexOutComponent[g,{m["saturated"]}]],"components"->c[g],"resetComponents"->c[h]|>;
ExportString[out,"RawJSON","Compact"->True]]
'''

def parse_result(raw):
    match=re.fullmatch(r"\s*Out\[\d+\]\s*=\s*(.+?)\s*",raw)
    if not match: raise ValueError("unexpected output")
    obj=json.loads(match[1])
    if isinstance(obj,str): obj=json.loads(obj)
    if not isinstance(obj,dict): raise ValueError("not an object")
    return obj

def classify(rc,raw,want):
    if rc!=0: return "DEGRADED"
    try: got=parse_result(raw)
    except ValueError: return "DEGRADED"
    return "MATCH" if json.dumps(got,sort_keys=True)==json.dumps(want,sort_keys=True) else "MISMATCH"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("graph",type=Path);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mcporter",required=True);p.add_argument("--config",type=Path,required=True)
    a=p.parse_args()
    data=a.graph.read_bytes();m=validate(json.loads(data))
    want=expected(m);code=render(m);a.out.mkdir(parents=True,exist_ok=False)
    wl=a.out/"graph.wl";wl.write_text(code)
    cmd=[a.mcporter,"--config",str(a.config),"call","wolfram.WolframLanguageEvaluator",f"code=@{wl.resolve()}","timeConstraint=30"]
    try:
        version=subprocess.run([a.mcporter,"--version"],capture_output=True,text=True,timeout=10,check=True).stdout.strip()
        if version!="0.13.8": raise ValueError("unexpected MCPorter version")
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        rc,raw,err=proc.returncode,proc.stdout,proc.stderr
    except (OSError,subprocess.SubprocessError,ValueError) as exc:
        version=locals().get("version","UNAVAILABLE");rc=127;raw="";err=str(exc)
    status=classify(rc,raw,want) if not err.strip() else "DEGRADED"
    (a.out/"result.raw").write_text(raw);(a.out/"result.err").write_text(err)
    try: got=parse_result(raw)
    except ValueError: got=None
    receipt={"status":status,"graph_sha256":digest(data),"wolfram_sha256":digest(code.encode()),
             "config_sha256":digest(a.config.read_bytes()),"raw_sha256":digest(raw.encode()),
             "mcporter_version":version,"returncode":rc,"expected":want,"observed":got,
             "scope":"conditional graph, not concrete firmware equivalence"}
    (a.out/"receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return {"MATCH":0,"MISMATCH":1,"DEGRADED":2}[status]

if __name__=="__main__": raise SystemExit(main())
