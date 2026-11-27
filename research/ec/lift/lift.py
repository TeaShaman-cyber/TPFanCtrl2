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
        require((v.size in (1,2,4,8) or (v.space=="const" and v.size==3)), "unsupported width")
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

def parse(src, allow_nop=False):
    blocks={}; pc=None; end=0; done=False; nops=set()
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
            if allow_nop and p[3:]==["NOP"]: nops.add(pc)
        elif p[0]=="OP":
            require(pc is not None and len(p)>=4,"operation outside instruction")
            blocks[pc][1].append((p[1],None if p[2]=="-" else V.parse(p[2]),tuple(V.parse(x) for x in p[3:])))
        else: raise LiftError("unknown record")
    require(done and bool(blocks) and all(ops or pc in nops for pc,(_,ops) in blocks.items()),"incomplete input")
    return blocks,end

def lift(src, kind="clamp"):
    require(kind in ("clamp","recovery","sample","decay"),"unknown slice")
    recovery=kind=="recovery"
    sample=kind=="sample"
    decay=kind=="decay"
    blocks,end=parse(src)
    require((min(blocks),end)==({"recovery":(0x199ea,0x19a08),"clamp":(0x19afc,0x19b12),"sample":(0x199aa,0x199e8),"decay":(0x3a002,0x3a07a)}[kind]),"unexpected slice")
    # Known ABI inputs; abstract memory only for two exact record offsets.
    initial={V("register",4,4):const(4,0x11454),
             V("register",8,2):E(2,"request"),
             V("register",0x50,2):E(2,"psr")}
    mem={0x11454+0x1c:E(2,"upper"),0x11454+0x1e:E(2,"lower")}
    if recovery:
        del initial[V("register",8,2)]
        mem[0x11454+0x20]=E(2,"output")
    if sample:
        initial.pop(V("register",8,2))
        initial[V("register",14,4)]=const(4,0x11454)
        initial[V("register",0,2)]=E(2,"r0")
        mem={0x11454+0x10:E(2,"rpm"),0x11454+0xac:E(1,"misses")}
    if decay:
        initial[V("register",0,2)]=E(2,"r0")
        for off,size,name in [(7,1,"stage"),(12,1,"sub"),(0xac,1,"misses"),(0x20,2,"output"),(0x16,2,"target"),(0x10,2,"rpm")]:
            mem[0x11454+off]=E(size,name)
    def get(env,v):
        if v.space=="const": return const(v.size,v.offset)
        if (sample or decay) and v==V("register",0,1):
            word=get(env,V("register",0,2))
            return E(1,f"(BitVec.setWidth 8 {word.lean})")
        require(v in env,"uninitialized "+repr(v))
        return env[v]
    def put(env,v,e):
        require(v is not None and v.space in ("register","unique") and v.size==e.size,"output mismatch")
        for old in list(env):
            if old.space==v.space and old!=v and old.offset < v.offset+v.size and v.offset < old.offset+old.size:
                raise LiftError("overlapping varnodes unsupported")
        env[v]=e
    visited=set()
    serial=0
    def step(pc,idx,env,memory,writes=0,active=frozenset()):
        nonlocal serial
        require((pc,idx) not in active,"control-flow cycle")
        active=active|{(pc,idx)}
        if sample and pc in (0x199be,0x199ce):
            require(writes==1,"sample must store counter exactly once")
            value=memory[0x11454+0xac].lean
            return f"((BitVec.setWidth 16 {value}) ||| ({256 if pc==0x199be else 0} : BitVec 16))"
        require(not sample or pc!=end,"sample escaped decision boundary")
        if decay and pc==0x3a080:
            require(writes in (0,1),"decay write count")
            return memory[0x11454+0x1e].lean
        require(not decay or pc!=end,"decay escaped tail")
        if pc==end:
            if recovery:
                require(writes==1,"recovery must store floor exactly once")
                return memory[0x11454+0x1e].lean
            require(writes==0,"unexpected store")
            return get(env,V("register",2,2)).lean
        require(pc in blocks,"bad target")
        nxt,ops=blocks[pc]
        if idx==len(ops): return step(nxt,0,{k:v for k,v in env.items() if k.space!="unique"},dict(memory),writes,active)
        visited.add((pc,idx))
        name,out,args=ops[idx]
        if name in ("BRANCH","CBRANCH"):
            require(out is None and len(args)==(1 if name=="BRANCH" else 2),"branch arity")
            dst=args[0]
            require(dst.space=="ram" and (sample or pc<dst.offset) and (dst.offset in blocks or dst.offset==end or (decay and dst.offset==0x3a080)),"invalid/loop branch")
            yes=step(dst.offset,0,{k:v for k,v in env.items() if k.space!="unique"},dict(memory),writes,active)
            if name=="BRANCH": return yes
            cond=get(env,args[1])
            require(cond.size==1,"condition width")
            no=step(pc,idx+1,dict(env),dict(memory),writes,active)
            return f"(if {truth(cond)} then {yes} else {no})"
        if name=="STORE":
            require((recovery or sample or decay) and out is None and len(args)==3 and args[0]==V("const",0x1a1,8),"unsupported store")
            addr,value=get(env,args[1]),get(env,args[2])
            require(addr.size==4 and addr.known==0x11454+(0xac if sample else 0x1e) and value.size==(1 if sample else 2) and writes==0,"store outside slice contract")
            memory=dict(memory);memory[addr.known]=value
            return step(pc,idx+1,env,memory,writes+1,active)
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
        elif name in ("INT_CARRY","INT_SCARRY","INT_SBORROW"):
            require(len(a)==2 and a[0].size==a[1].size and n==1,"carry width")
            x,y=a[0].lean,a[1].lean
            if name=="INT_CARRY": b=f"(BitVec.ult ({x} + {y}) {x})"
            else:
                sx=f"(BitVec.slt {x} 0)";sy=f"(BitVec.slt {y} 0)"
                ss=f"(BitVec.slt ({x} {'-' if name=='INT_SBORROW' else '+'} {y}) 0)"
                b=f"(({sx} {'!=' if name=='INT_SBORROW' else '=='} {sy}) && ({sx} != {ss}))"
            e=boolean(b)
        elif name=="SUBPIECE":
            require(len(a)==2 and a[1].known is not None and a[1].known+n<=a[0].size,"subpiece bounds")
            e=E(n,f"(BitVec.setWidth {8*n} (BitVec.ushiftRight {a[0].lean} {8*a[1].known}))")
        elif name in ("INT_ADD","INT_SUB","INT_AND","INT_OR"):
            require(len(a)==2 and a[0].size==a[1].size==n,"arithmetic width")
            op={"INT_ADD":"+","INT_SUB":"-","INT_AND":"&&&","INT_OR":"|||"}[name]
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
        if (sample or decay) and e.known is None:
            serial+=1;name=f"{'_v' if decay else 'v'}{serial}"
            put(env,out,E(e.size,name))
            return f"(let {name} : BitVec {e.size*8} := {e.lean}; {step(pc,idx+1,env,memory,writes,active)})"
        put(env,out,e)
        return step(pc,idx+1,env,memory,writes,active)
    body=step(min(blocks),0,initial,mem)
    require(visited=={(pc,i) for pc,(_,ops) in blocks.items() for i in range(len(ops)) if not sample or not 0x199be<=pc<=0x199d0},"unvisited operations")
    if decay:
        return """import Std.Tactic.BVDecide
set_option warningAsError true
set_option maxRecDepth 8192
set_option maxHeartbeats 16000000
namespace R17Decay
def lifted (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16) : BitVec 16 :=
  """+body+"""
def enabled (stage sub misses : BitVec 8)
    (lower upper output request target rpm : BitVec 16) : Prop :=
  stage = 11 ∧ sub = 0 ∧ misses = 0 ∧ upper = 500 ∧
  25 < lower ∧ lower ≤ 500 ∧ output = lower ∧ request < lower ∧
  0 < target ∧ target ≤ 10000 ∧ rpm ≠ 65535 ∧ target + 100 < rpm

def spec (stage sub misses : BitVec 8)
    (lower upper output request target rpm : BitVec 16) : BitVec 16 :=
  if stage = 11 ∧ sub = 0 ∧ misses = 0 ∧ upper = 500 ∧
    25 < lower ∧ lower ≤ 500 ∧ output = lower ∧ request < lower ∧
    0 < target ∧ target ≤ 10000 ∧ rpm ≠ 65535 ∧ target + 100 < rpm
  then lower - 1 else lower

theorem exact_decay (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16) :
    lifted stage sub misses lower upper output request target rpm r0 psr =
    spec stage sub misses lower upper output request target rpm := by
  unfold lifted spec
  bv_decide

theorem missing_feedback (stage sub misses : BitVec 8)
    (lower upper output request target r0 psr : BitVec 16) :
    lifted stage sub misses lower upper output request target 65535 r0 psr = lower := by
  rw [exact_decay]
  simp [spec]

theorem disabled_when_recovering (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : stage ≠ 11 ∨ sub ≠ 0 ∨ misses ≠ 0) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem no_underspeed_decay (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : rpm ≤ target) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem bounded_step (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : 25 ≤ lower) (h2 : lower ≤ 500) :
    25 ≤ lifted stage sub misses lower upper output request target rpm r0 psr ∧
    (lifted stage sub misses lower upper output request target rpm r0 psr = lower ∨
     lifted stage sub misses lower upper output request target rpm r0 psr = lower - 1) := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem progress_on_eligible_sample (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : enabled stage sub misses lower upper output request target rpm) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower - 1 := by
  rw [exact_decay]
  unfold enabled at h
  unfold spec
  exact if_pos h

-- A single high but non-sentinel value is sufficient; physical validity is external.
theorem high_reading_counterexample : lifted 11 0 0 500 500 500 499 2550 65534 0 0 = 499 := by decide

#print axioms high_reading_counterexample
#print axioms exact_decay
#print axioms missing_feedback
#print axioms disabled_when_recovering
#print axioms no_underspeed_decay
#print axioms bounded_step
#print axioms progress_on_eligible_sample
end R17Decay
"""
    if sample:
        return """import Std.Tactic.BVDecide
set_option warningAsError true
set_option maxRecDepth 8192
set_option maxHeartbeats 8000000
namespace R17Sample
-- Low byte: stored counter. Bit 8: entry to recovery branch, not its effects.
def lifted (misses : BitVec 8) (rpm r0 psr : BitVec 16) : BitVec 16 :=
  """+body+"""
def spec (misses : BitVec 8) (rpm : BitVec 16) : BitVec 16 :=
  let next := if rpm == 65535 then misses + 1 else 0
  let recover := if rpm == 65535 then BitVec.slt (8 : BitVec 8) next else decide (rpm ≤ 299)
  (BitVec.setWidth 16 next) ||| (if recover then 256 else 0)

theorem exact_sample (misses : BitVec 8) (rpm r0 psr : BitVec 16) :
    lifted misses rpm r0 psr = spec misses rpm := by
  unfold lifted spec
  bv_decide

theorem eighth_or_less (misses : BitVec 8) (r0 psr : BitVec 16) (h : misses < 8) :
    lifted misses 65535 r0 psr = BitVec.setWidth 16 (misses + 1) := by
  rw [exact_sample]
  unfold spec
  bv_decide

theorem ninth_miss (r0 psr : BitVec 16) :
    lifted 8 65535 r0 psr = 265 := by
  rw [exact_sample]
  decide

theorem valid_reset (misses : BitVec 8) (rpm r0 psr : BitVec 16)
    (h : 300 ≤ rpm) (h2 : rpm ≠ 65535) :
    lifted misses rpm r0 psr = 0 := by
  rw [exact_sample]
  unfold spec
  bv_decide

theorem low_speed (misses : BitVec 8) (rpm r0 psr : BitVec 16) (h : rpm ≤ 299) :
    lifted misses rpm r0 psr = 256 := by
  rw [exact_sample]
  unfold spec
  bv_decide

theorem signed_counterexample : lifted 127 65535 0 0 = 128 := by decide
theorem wrap_counterexample : lifted 255 65535 0 0 = 0 := by decide

#print axioms exact_sample
#print axioms eighth_or_less
#print axioms ninth_miss
#print axioms valid_reset
#print axioms low_speed
#print axioms signed_counterexample
#print axioms wrap_counterexample
end R17Sample
"""
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
    if kind=="decay":
        for line in rows.splitlines():
            a=line.split()
            require(len(a)==12 and all(x.isdecimal() and 0<=int(x)<=65535 for x in a),"invalid decay oracle row")
            require(all(int(x)<=255 for x in a[:3]),"decay byte width")
            examples.append("example : lifted "+" ".join(a[:-1])+" = "+a[-1]+" := by decide")
        require(len(examples)==512,"incomplete decay oracle")
        return out.replace("end R17Decay","\n".join(examples)+"\nend R17Decay")
    for line in rows.splitlines():
        a=line.split()
        require(len(a)==5 and all(x.isdecimal() and 0<=int(x)<=65535 for x in a),"invalid oracle row")
        if kind=="decay":
            raise LiftError("use decay oracle schema")
        lo,hi,req,psr,result=map(int,a)
        require(kind!="sample" or (lo<=255 and result<=511),"sample oracle width")
        examples.append(f"example : lifted {lo} {hi} {req} {psr} = {result} := by decide")
    require(len(examples)==(2176 if kind=="sample" else 353),"incomplete oracle corpus")
    end={"recovery":"end R17Recovery","clamp":"end R17Lift","sample":"end R17Sample"}[kind]
    return out.replace(end,"\n".join(examples)+"\n"+end)

if __name__=="__main__":
    src=Path(sys.argv[1]).read_text()
    kind=sys.argv[3] if len(sys.argv)==4 else "clamp"
    sys.stdout.write(with_oracle(src,Path(sys.argv[2]).read_text(),kind) if len(sys.argv)>=3 else lift(src,kind))
