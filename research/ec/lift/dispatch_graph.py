"""Extract R17 table dispatch and observed transition projection.

A table slot describes handler selection, not a state transition. Only
completed original-code dispatch traces supply the observed graph edges.
"""
import argparse
import json
from pathlib import Path
from lift import parse
from wolfram_witness import validate

BASE=0x20100
ROM_SIZE=237568

def need(ok,msg):
    if not ok: raise ValueError(msg)

def table(src):
    lines=src.splitlines()
    need(bool(lines) and lines[-1]=="EXTRACT_PASS","incomplete extract")
    records=[]; words={}; data=False
    for line in lines[:-1]:
        if line.startswith("TABLE "):
            data=True
            _,a,v=line.split();a=int(a,16);v=int(v,16)
            need(a not in words,"duplicate table word");words[a]=v
        else:
            need(not data,"instruction after table")
            records.append(line)
    blocks,end=parse("\n".join(records+["EXTRACT_PASS"]),allow_nop=True)
    need(min(blocks)==0x190da and end==0x191e2,"dispatcher boundary")
    need(set(words)==set(range(0x55248,0x553dc,4)),"table coverage")
    # Explicit ISA/layout contract: two indirect word-address transfers,
    # stage index and substage index both scaled by 4, null fallback.
    for addr,opcode in [(0x1910e,"BRANCHIND"),(0x191d2,"CALLIND"),(0x191da,"STORE"),(0x191dc,"STORE")]:
        need(any(op==opcode for op,_,_ in blocks[addr][1]),"dispatcher contract")
    for addr in (0x1910e,0x191d2):
        need(any(op=="INT_LEFT" and args[-1].space=="const" and args[-1].offset==1 for op,_,args in blocks[addr][1]),"word address scaling")
    def raw(word):
        a=2*word-BASE
        need(0<=a<ROM_SIZE and a%2==0,"pointer outside payload")
        return a
    bases={}
    for stage in range(17):
        entry=raw(words[0x55398+4*stage])
        need(entry in blocks,"stage target outside dispatcher")
        candidates=[a[0].offset for op,out,a in blocks[entry][1]
                    if op=="COPY" and out and out.space=="register" and out.offset==8 and out.size==4 and len(a)==1 and a[0].space=="const"]
        if not candidates:
            need(stage in (10,15),"unexpected non-table stage")
            continue
        need(len(candidates)==1,"ambiguous base")
        bases[stage]=candidates[0]
    need(len(bases)==15 and len(set(bases.values()))==15,"stage table coverage")
    limits=sorted(bases.values())+[0x55398]
    result={}
    for stage,start in bases.items():
        need(start in words and start%4==0,"table base")
        stop=limits[limits.index(start)+1]
        for i,a in enumerate(range(start,stop,4)):
            w=words[a]
            need((w==0)==(a==stop-4),"expected one terminal null")
            result[stage,i]=raw(w) if w else None
    direct=[args[0].offset for op,_,args in blocks[0x19172][1]
            if op=="CALL" and len(args)==1 and args[0].space=="ram"]
    need(len(direct)==1 and 0<=direct[0]<ROM_SIZE,"direct stage 10")
    result[10,None]=direct[0]
    return result

def observed(src,slots):
    out=[]; selection=None
    for line in src.splitlines():
        fields=line.split()
        if fields[0]=="SELECT":
            need(len(fields)==4 and selection is None,"unpaired selection")
            stage,sub=map(int,fields[1:3])
            target=None if fields[3]=="null" else int(fields[3],16)
            key=(stage,None) if (stage,None) in slots else (stage,sub)
            need(key in slots and slots[key]==target,"table/trace mismatch")
            selection=(stage,sub)
        elif fields[0]=="TRANS":
            need(len(fields)==11,"transition schema")
            a=tuple(map(int,fields[1:6]));b=tuple(map(int,fields[6:]))
            need(selection==a[:2],"transition/selection mismatch")
            for st,su,f,m,p in (a,b):
                need(0<=st<=16 and 0<=su<=255 and 25<=f<=500 and 0<=m<=255 and 0<=p<=500,"trace domain")
            out.append((a,b));selection=None
        else: raise ValueError("unknown trace record")
    need(selection is None and bool(out),"incomplete trace")
    return out

def graph(rows):
    # Projection of observed dispatcher calls: stage, substage, floor==500.
    # No edges inferred between calls, no unobserved reset/missing edges.
    def node(s): return s[0]*512+s[1]*2+int(s[2]==500)
    e=sorted({(node(a),node(b)) for a,b in rows})
    initial=node(rows[0][0]);sat=11*512+1
    return validate({"states":sorted({x for edge in e for x in edge}),
        "edges":[list(x) for x in e],"reset_edges":[list(x) for x in e],
        "missing_edges":[],"initial":initial,"saturated":sat})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("ir",type=Path);p.add_argument("trace",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    slots=table(a.ir.read_text());rows=observed(a.trace.read_text(),slots)
    g=graph(rows)
    a.out.write_text(json.dumps(g,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"table_slots":len(slots),"handlers":len(set(v for v in slots.values() if v is not None)),
     "observed_calls":len(rows),"observed_slots":len({x[:2] for x,_ in rows}),"states":len(g["states"]),"edges":len(g["edges"])}))

if __name__=="__main__": main()
