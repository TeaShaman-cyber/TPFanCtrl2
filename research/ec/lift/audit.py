"""Local P-code pattern screening, not a vulnerability detector or global dataflow."""
from pathlib import Path
import sys
from lift import parse

def scan(src):
    ranges=[]; cur=None
    lines=src.splitlines()
    if not lines or lines[-1]!="EXTRACT_PASS":
        raise ValueError("incomplete extraction")
    for line in lines[:-1]:
        if line.startswith("RANGE "):
            _,lo,hi=line.split()
            cur=(int(lo,16),int(hi,16),[])
            ranges.append(cur)
        elif cur is None: raise ValueError("missing range")
        else: cur[2].append(line)
    if not ranges: raise ValueError("missing ranges")
    hits=set()
    for lo,hi,records in ranges:
        blocks,end=parse("\n".join(records+["EXTRACT_PASS"]), allow_nop=True)
        if min(blocks)!=lo or end!=hi: raise ValueError("range mismatch")
        subs={}; wide=None
        for pc,(_,ops) in blocks.items():
            # Compare reads before their instruction's flag writes.  No cross-branch tracking.
            for name,out,args in ops:
                if name=="INT_SLESS":
                    for a in args:
                        if a in subs: hits.add(("signed-word-difference",subs[a],pc))
                if name=="STORE" and wide is not None and args[-1].space=="register" and args[-1].offset==0 and args[-1].size==2:
                    hits.add(("known-wide-return-store",wide,pc))
                if out is not None and out.space=="register":
                    for v in list(subs):
                        if v.offset<out.offset+out.size and out.offset<v.offset+v.size:
                            del subs[v]
                    if out.offset<4 and wide is not None: wide=None
                if name=="INT_SUB" and out is not None and out.space=="register" and out.size==2:
                    subs[out]=pc
                if name in ("BRANCH","CBRANCH","BRANCHIND","CALL","CALLIND","RETURN"):
                    subs.clear();wide=None
                    # This specific ABI contract is supported by iteration163 trace,
                    # not inferred for all CALL instructions.
                    if name=="CALL" and args[0].space=="ram" and args[0].offset==0x192fe: wide=pc
    return sorted(hits)

if __name__=="__main__":
    for kind,a,b in scan(Path(sys.argv[1]).read_text()):
        print(f"{kind}\t{a:05x}\t{b:05x}")
