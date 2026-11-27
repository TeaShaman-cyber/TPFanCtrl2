"""Strict, acyclic P-code slice -> Lean bitvectors. No ISA mnemonic translation."""
from dataclasses import dataclass
from pathlib import Path
import re, sys

class LiftError(ValueError): pass

def require(condition, why):
    if not condition: raise LiftError(why)

@dataclass(frozen=True)
class V:
    space: str
    offset: int
    size: int
    @classmethod
    def parse(cls, text):
        m=re.fullmatch(r"(const|register|unique|ram):([0-9a-f]+):([1-9][0-9]*)",text)
        require(m is not None, "invalid varnode "+text)
        v=cls(m[1],int(m[2],16),int(m[3]))
        require(v.size in (1,2,4,8), "unsupported width")
        return v

@dataclass(frozen=True)
class E:
    size: int
    lean: str
    known: int|None=None

def const(size, n):
    n %= 1<<(size*8)
    return E(size,f"({n} : BitVec {size*8})",n)

def boolean(b):
    return E(1,f"(if {b} then (1 : BitVec 8) else 0)")

def truth(e): return f"({e.lean} != 0)"

def parse(src):
    blocks={}; pc=None; end=0; done=False
    for line in src.splitlines():
        require(not done,"data after marker")
        if line=="EXTRACT_PASS": done=True;continue
        p=line.split()
        require(bool(p),"empty line")
        if p[0]=="INS":
            require(len(p)>=4,"invalid instruction")
            pc=int(p[1],16);n=int(p[2])
            require(pc not in blocks and (not blocks or pc==end) and n in (2,4,6),"noncontiguous instructions")
            blocks[pc]=(pc+n,[]);end=pc+n
        elif p[0]=="OP":
            require(pc is not None and len(p)>=4,"operation outside instruction")
            blocks[pc][1].append((p[1],None if p[2]=="-" else V.parse(p[2]),tuple(V.parse(x) for x in p[3:])))
        else: raise LiftError("unknown record")
    require(done and bool(blocks) and all(ops for _,ops in blocks.values()),"incomplete input")
    return blocks,end

def lift(src):
    blocks,end=parse(src)
    require(min(blocks)==0x19afc and end==0x19b12,"unexpected slice")
    # Known ABI inputs; abstract memory only for two exact record offsets.
    initial={V("register",4,4):const(4,0x11454),
             V("register",8,2):E(2,"request"),
             V("register",0x50,2):E(2,"psr")}
    mem={0x11454+0x1c:E(2,"upper"),0x11454+0x1e:E(2,"lower")}
    def get(env,v):
        if v.space=="const": return const(v.size,v.offset)
        require(v in env,"uninitialized "+repr(v))
        return env[v]
    def put(env,v,e):
        require(v is not None and v.space in ("register","unique") and v.size==e.size,"output mismatch")
        for old in list(env):
            if old.space==v.space and old!=v and old.offset < v.offset+v.size and v.offset < old.offset+old.size:
                raise LiftError("overlapping varnodes unsupported")
        env[v]=e
    visited=set()
    def step(pc,idx,env):
        if pc==end:
            return get(env,V("register",2,2)).lean
        require(pc in blocks,"bad target")
        nxt,ops=blocks[pc]
        if idx==len(ops): return step(nxt,0,{k:v for k,v in env.items() if k.space!="unique"})
        visited.add((pc,idx))
        name,out,args=ops[idx]
        if name in ("BRANCH","CBRANCH"):
            require(out is None and len(args)==(1 if name=="BRANCH" else 2),"branch arity")
            dst=args[0]
            require(dst.space=="ram" and pc<dst.offset<=end and (dst.offset in blocks or dst.offset==end),"invalid/loop branch")
            yes=step(dst.offset,0,{k:v for k,v in env.items() if k.space!="unique"})
            if name=="BRANCH": return yes
            cond=get(env,args[1])
            require(cond.size==1,"condition width")
            no=step(pc,idx+1,dict(env))
            return f"(if {truth(cond)} then {yes} else {no})"
        require(out is not None,"missing output")
        a=[get(env,v) for v in args]
        n=out.size
        if name=="COPY":
            require(len(a)==1 and a[0].size==n,"copy width");e=a[0]
        elif name=="LOAD":
            require(len(a)==2 and args[0]==V("const",0x1a1,8) and a[1].known in mem,"unknown load")
            e=mem[a[1].known]
        elif name=="INT_ZEXT":
            require(len(a)==1 and a[0].size<=n,"extension width")
            e=const(n,a[0].known) if a[0].known is not None else E(n,f"(BitVec.setWidth {8*n} {a[0].lean})")
        elif name=="SUBPIECE":
            require(len(a)==2 and a[1].known is not None and a[1].known+n<=a[0].size,"subpiece bounds")
            e=E(n,f"(BitVec.setWidth {8*n} (BitVec.ushiftRight {a[0].lean} {8*a[1].known}))")
        elif name in ("INT_ADD","INT_AND","INT_OR"):
            require(len(a)==2 and a[0].size==a[1].size==n,"arithmetic width")
            op={"INT_ADD":"+","INT_AND":"&&&","INT_OR":"|||"}[name]
            if name=="INT_ADD" and all(x.known is not None for x in a): e=const(n,a[0].known+a[1].known)
            else: e=E(n,f"({a[0].lean} {op} {a[1].lean})")
        elif name in ("INT_LEFT","INT_RIGHT"):
            require(len(a)==2 and a[0].size==n and a[1].known is not None,"shift width")
            op="shiftLeft" if name=="INT_LEFT" else "ushiftRight"
            e=E(n,f"(BitVec.{op} {a[0].lean} {a[1].known})")
        elif name in ("INT_EQUAL","INT_LESS","INT_SLESS"):
            require(len(a)==2 and a[0].size==a[1].size and n==1,"compare width")
            b=f"({a[0].lean} == {a[1].lean})" if name=="INT_EQUAL" else f"(BitVec.{ 'ult' if name=='INT_LESS' else 'slt'} {a[0].lean} {a[1].lean})"
            e=boolean(b)
        elif name=="BOOL_OR":
            require(len(a)==2 and a[0].size==a[1].size==n==1,"bool width")
            e=boolean(f"({truth(a[0])} || {truth(a[1])})")
        elif name=="BOOL_NEGATE":
            require(len(a)==1 and a[0].size==n==1,"bool width")
            e=boolean(f"(!{truth(a[0])})")
        else: raise LiftError("unsupported operation "+name)
        put(env,out,e)
        return step(pc,idx+1,env)
    body=step(min(blocks),0,initial)
    require(visited=={(pc,i) for pc,(_,ops) in blocks.items() for i in range(len(ops))},"unvisited operations")
    return """import Std.Tactic.BVDecide
set_option warningAsError true
namespace R17Lift
-- Generated from raw P-code of the selection slice; no MMIO or whole-function claim.
def lifted (lower upper request psr : BitVec 16) : BitVec 16 :=
  """+body+"""
def spec (lower upper request : BitVec 16) : BitVec 16 :=
  if upper ≤ request then upper else if request < lower then lower else request

theorem exact_selection (lower upper request psr : BitVec 16) :
    lifted lower upper request psr = spec lower upper request := by
  unfold lifted spec
  bv_decide

theorem ordered_clamp (lower upper request psr : BitVec 16) (h : lower ≤ upper) :
    lower ≤ lifted lower upper request psr ∧ lifted lower upper request psr ≤ upper := by
  rw [exact_selection]
  unfold spec
  bv_decide

theorem saturated (request psr : BitVec 16) :
    lifted 500 500 request psr = 500 := by
  rw [exact_selection]
  unfold spec
  bv_decide

#print axioms exact_selection
#print axioms ordered_clamp
#print axioms saturated
end R17Lift
"""
def with_oracle(src, rows):
    out=lift(src)
    examples=[]
    for line in rows.splitlines():
        a=line.split()
        require(len(a)==5 and all(x.isdecimal() and 0<=int(x)<=65535 for x in a),"invalid oracle row")
        lo,hi,req,psr,result=map(int,a)
        examples.append(f"example : lifted {lo} {hi} {req} {psr} = {result} := by decide")
    require(len(examples)==353,"incomplete oracle corpus")
    return out.replace("end R17Lift","\n".join(examples)+"\nend R17Lift")

if __name__=="__main__":
    src=Path(sys.argv[1]).read_text()
    sys.stdout.write(with_oracle(src,Path(sys.argv[2]).read_text()) if len(sys.argv)==3 else lift(src))
