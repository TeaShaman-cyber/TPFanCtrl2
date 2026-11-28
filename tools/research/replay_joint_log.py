"""Convert iteration214 diagnostic exports to actual C++ offline replay inputs.

Each JSONL object contains a build name and matched selected EcPair / EcTempShadow
gate rows. Source log SHA and byte count identify the snapshot. Not all polls
are logged. No interpolation, no physical feedback or real acknowledgements.
"""
import argparse
import collections
import json
from pathlib import Path
import subprocess

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for line in args.export.read_text().splitlines():
        d = json.loads(line)
        rows = d["rows"]
        inputs = []
        for r in rows:
            end,a,ta,al,ah,ra,b,tb,bl,bh,rb,ms,now,pair,value,delta,age,fresh,permit,epoch,tach = r
            if end != pair or not 0 <= age <= now or now < end:
                raise ValueError("invalid correlation")
            inputs.append(" ".join(map(str, [now-age,end,now,a,al,ah,ta,ra,b,bl,bh,tb,rb,fresh,epoch])))
        data = "\n".join(inputs)+"\n"
        print(d["build"], "n", len(rows), "gaps>2s", sum(b[12]-a[12]>2000 for a,b in zip(rows,rows[1:])))
        for seed in [1,4,128]:
            result = subprocess.run([str(args.executable.resolve()),args.config,str(seed)],input=data,text=True,capture_output=True,check=True)
            out = [x.split() for x in result.stdout.splitlines()]
            if len(out)!=len(rows) or any(int(x[2])!=r[14] for x,r in zip(out,rows)):
                raise ValueError("temperature replay mismatch")
            if any(r[-1] is not None and (int(x[4])!=r[-1][1] or x[5]!=r[-1][4]) for x,r in zip(out,rows)):
                raise ValueError("tach replay mismatch")
            (args.output/(d["build"]+f"-seed{seed}.txt")).write_text(result.stdout)
            print("seed",seed,"quality",dict(collections.Counter(x[5] for x in out)),
                  "joint permitted",sum(x[6]=="1" for x in out),
                  "baseline",dict(collections.Counter(x[8] for x in out if x[9]!="-1")),
                  "guarded",dict(collections.Counter(x[11] for x in out if x[12]!="-1")),
                  "decision differences",sum(x[8:10]!=x[11:13] for x in out))

if __name__ == "__main__":
    main()
