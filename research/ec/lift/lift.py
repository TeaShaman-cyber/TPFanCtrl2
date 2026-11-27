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

def lift(src, kind="clamp"):
    require(kind in ("clamp","recovery"),"unknown slice")
    recovery=kind=="recovery"
    blocks,end=parse(src)
    require((min(blocks),end)==((0x199ea,0x19a08) if recovery else (0x19afc,0x19b12)),"unexpected slice")
    # Known ABI inputs; abstract memory only for two exact record offsets.
    initial={V("register",4,4):const(4,0x11454),
             V("register",8,2):E(2,"request"),
             V("register",0x50,2):E(2,"psr")}
    mem={0x11454+0x1c:E(2,"upper"),0x11454+0x1e:E(2,"lower")}
    if recovery:
        del initial[V("register",8,2)]
        mem[0x11454+0x20]=E(2,"output")
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
    def step(pc,idx,env,memory,writes=0):
        if pc==end:
            if recovery:
                require(writes==1,"recovery must store floor exactly once")
                return memory[0x11454+0x1e].lean
            require(writes==0,"unexpected store")
            return get(env,V("register",2,2)).lean
        require(pc in blocks,"bad target")
        nxt,ops=blocks[pc]
        if idx==len(ops): return step(nxt,0,{k:v for k,v in env.items() if k.space!="unique"},dict(memory),writes)
        visited.add((pc,idx))
        name,out,args=ops[idx]
        if name in ("BRANCH","CBRANCH"):
            require(out is None and len(args)==(1 if name=="BRANCH" else 2),"branch arity")
            dst=args[0]
            require(dst.space=="ram" and pc<dst.offset<=end and (dst.offset in blocks or dst.offset==end),"invalid/loop branch")
            yes=step(dst.offset,0,{k:v for k,v in env.items() if k.space!="unique"},dict(memory),writes)
            if name=="BRANCH": return yes
            cond=get(env,args[1])
            require(cond.size==1,"condition width")
            no=step(pc,idx+1,dict(env),dict(memory),writes)
            return f"(if {truth(cond)} then {yes} else {no})"
        if name=="STORE":
            require(recovery and out is None and len(args)==3 and args[0]==V("const",0x1a1,8),"unsupported store")
            addr,value=get(env,args[1]),get(env,args[2])
            require(addr.size==4 and addr.known==0x11454+0x1e and value.size==2 and writes==0,"store outside floor contract")
            memory=dict(memory);memory[addr.known]=value
            return step(pc,idx+1,env,memory,writes+1)
        require(out is not None,"missing output")
        a=[get(env,v) for v in args]
        n=out.size
        if name=="COPY":
            require(len(a)==1 and a[0].size==n,"copy width");e=a[0]
        elif name=="LOAD":
            require(len(a)==2 and args[0]==V("const",0x1a1,8) and a[1].size==4 and a[1].known in memory,"unknown load")
            e=memory[a[1].known]
            require(e.size==n,"load width")
        elif name=="INT_ZEXT":
            require(len(a)==1 and a[0].size<=n,"extension width")
            e=const(n,a[0].known) if a[0].known is not None else E(n,f"(BitVec.setWidth {8*n} {a[0].lean})")
        elif name=="INT_SEXT":
            require(len(a)==1 and a[0].size<=n,"signed extension width")
            if a[0].known is not None:
                val=a[0].known
                if val >= 1<<(a[0].size*8-1): val-=1<<(a[0].size*8)
                e=const(n,val)
            else: e=E(n,f"(BitVec.signExtend {8*n} {a[0].lean})")
        elif name in ("INT_CARRY","INT_SCARRY"):
            require(len(a)==2 and a[0].size==a[1].size and n==1,"carry width")
            x,y=a[0].lean,a[1].lean
            if name=="INT_CARRY": b=f"(BitVec.ult ({x} + {y}) {x})"
            else:
                sx=f"(BitVec.slt {x} 0)";sy=f"(BitVec.slt {y} 0)"
                ss=f"(BitVec.slt ({x} + {y}) 0)"
                b=f"(({sx} == {sy}) && ({sx} != {ss}))"
            e=boolean(b)
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
        elif name in ("BOOL_OR","BOOL_AND"):
            require(len(a)==2 and a[0].size==a[1].size==n==1,"bool width")
            op="||" if name=="BOOL_OR" else "&&"
            e=boolean(f"({truth(a[0])} {op} {truth(a[1])})")
        elif name=="BOOL_NEGATE":
            require(len(a)==1 and a[0].size==n==1,"bool width")
            e=boolean(f"(!{truth(a[0])})")
        else: raise LiftError("unsupported operation "+name)
        put(env,out,e)
        return step(pc,idx+1,env,memory,writes)
    body=step(min(blocks),0,initial,mem)
    require(visited=={(pc,i) for pc,(_,ops) in blocks.items() for i in range(len(ops))},"unvisited operations")
    if recovery:
        return """import Std.Tactic.BVDecide
set_option warningAsError true
namespace R17Recovery
-- Generated from the floor update including its original STORE.
def lifted (lower upper output psr : BitVec 16) : BitVec 16 :=
  """+body+"""
def spec (lower upper output : BitVec 16) : BitVec 16 :=
  let inc := (if output < lower then lower else output) + 1
  if upper ≤ inc then upper else inc

theorem exact_recovery (lower upper output psr : BitVec 16) :
    lifted lower upper output psr = spec lower upper output := by
  unfold lifted spec
  bv_decide

theorem recovery_nondecreasing (lower upper output psr : BitVec 16)
    (h₁ : lower ≤ upper) (h₂ : output ≤ upper) (h₃ : upper ≤ 500) :
    lower ≤ lifted lower upper output psr ∧ lifted lower upper output psr ≤ upper := by
  rw [exact_recovery]
  unfold spec
  bv_decide

theorem saturation (lower psr : BitVec 16) (h : lower ≤ 500) :
    lifted lower 500 500 psr = 500 := by
  rw [exact_recovery]
  unfold spec
  bv_decide

theorem wrap_counterexample : lifted 65535 65535 65535 0 = 0 := by decide

#print axioms exact_recovery
#print axioms recovery_nondecreasing
#print axioms saturation
#print axioms wrap_counterexample
end R17Recovery
"""
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
def with_oracle(src, rows, kind="clamp"):
    out=lift(src,kind)
    examples=[]
    for line in rows.splitlines():
        a=line.split()
        require(len(a)==5 and all(x.isdecimal() and 0<=int(x)<=65535 for x in a),"invalid oracle row")
        lo,hi,req,psr,result=map(int,a)
        examples.append(f"example : lifted {lo} {hi} {req} {psr} = {result} := by decide")
    require(len(examples)==353,"incomplete oracle corpus")
    end="end R17Recovery" if kind=="recovery" else "end R17Lift"
    return out.replace(end,"\n".join(examples)+"\n"+end)

if __name__=="__main__":
    src=Path(sys.argv[1]).read_text()
    kind=sys.argv[3] if len(sys.argv)==4 else "clamp"
    sys.stdout.write(with_oracle(src,Path(sys.argv[2]).read_text(),kind) if len(sys.argv)>=3 else lift(src,kind))
