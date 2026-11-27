# R17 P-code lifting pilot

Research only. No firmware bytes, binary patch or deployment. Original firmware
payload SHA-256 08faaa8146c65e96164a5e73cc21864c7fb7403ea774ad92055ff77f0579ab4e.
Ghidra 12.2 CR16C:LE:16:default. Selection slice raw offsets 19afc..19b12
(exclusive), inside 19afa. 9 instructions / 57 P-code operations. The small
derived P-code excerpt is the deterministic translation input; original payload
is obtained independently from Lenovo. No generated code for the remaining
write/MMIO/call/return portion, no proof of full ISA or SLEIGH correctness.

The input ABI fixes R3:R2 to record 0x11454, memory at record+0x1c and +0x1e
to symbolic 16-bit upper/lower words, R4 to request, PSR arbitrary.
Other uninitialized reads, overlapping varnodes, unknown loads/opcodes,
non-forward branches, and incomplete extracts fail closed. This is a bounded
acyclic symbolic translator, not a general CR16 disassembler. The Lean output
preserves bit widths, flags and branches rather than translating mnemonics.
The independently specified clamp theorem covers even reversed bounds via
upper-first selection; ordered bounds are required for range preservation.

Local regeneration:
  cd research/ec/lift
  python3 -m unittest -v test_lift
  python3 lift.py clamp.pcode oracle.tsv > /tmp/LiftedClamp.lean
  cmp LiftedClamp.lean /tmp/LiftedClamp.lean
  lean LiftedClamp.lean

Oracle vectors were produced by executing the original selection instructions
in Ghidra PcodeEmulator, 225 boundary combinations plus 128 seeded random cases,
including arbitrary PSR values and reversed bounds. They are finite differential
evidence, not a separate physical CR16 implementation. Extraction and oracle
Java scripts are retained for replay with the same pinned payload and Ghidra
headless launcher. Oracle rows are decimal lower, upper, request, PSR, output.
CI checks regeneration, bitvector theorems and all 353 oracle examples, plus
a false theorem canary. GitHub runner does not retrieve original firmware;
local exact-payload extraction remains a distinct evidence step.

## Recovery floor slice (iteration 159)

Raw offsets 199ea..19a08 (exclusive), 11 instructions / 79 P-code operations,
including the actual word store to record+0x1e. The shared lifter now supports
BOOL_AND, INT_SEXT, INT_CARRY, INT_SCARRY and a path-local, exactly-once floor
store. Other stores reject. The input word at record+0x20 is current PWM.
The emitted model implements 16-bit wrap before upper clamping, not unbounded
natural-number addition. Under lower/output <= upper <= 500, the floor cannot
decrease and stays bounded. At all three inputs 65535 it wraps to zero; this
is an out-of-domain counterexample, not evidence of a live fault. 353 original
instruction oracle cases are in recovery.tsv; replay scripts require the same
pinned original payload. Regenerate with:
  python3 lift.py recovery.pcode recovery.tsv recovery > /tmp/LiftedRecovery.lean
  cmp LiftedRecovery.lean /tmp/LiftedRecovery.lean
  lean LiftedRecovery.lean
CI runs clamp and recovery in separate matrix jobs with exact-head artifacts.
The recovery slice ends before the subsequent substep increment, not a full
recovery routine. Universal bv_decide results rely on Lean's native reflection
axioms; concrete by decide examples do not add that dependency.

## Sample decision slice (iteration 160)

Raw 199aa..199e8 exclusive is the body of sample validation. The translated
projection stops at 199be (recovery branch) or 199ce (normal branch), before
flag writes, helper call and epilogue. Initial ABI R3:R2 and R8:R7 fixed to
record 11454; symbolic R0, PSR, 16-bit RPM and 8-bit miss count. Output is a
16-bit word: updated count in low byte, recovery decision in bit 8.
The shared lifter checks cycles by path rather than address ordering,
permits the exact low-byte R0 read and 3-byte constants, and emits SSA-like
let bindings for the larger expression. Only the counter byte may be stored
and exactly once on each path. All decision ops must be covered; the
explicitly excluded continuation is not a proof of its effects.
The original-code oracle runs the full sample body from 199a6 through the
stage helper up to 199cc (before return), with initial stage11 and substep8;
observes stage11/12, substep0 and stored count. 2176 cases: all 256 counts
times 8 RPM boundaries, plus 128 seeded random cases, with varying R0/PSR.
Signed comparison after increment: recovery on missing sample iff new count
9..127, not all unsigned counts >8. 127 -> 128 and 255 -> 0 are concrete
out-of-domain counterexamples, not established reachable scheduler states.
Ordinary valid RPM >=300 clears misses; 0..299 recovers immediately.
The prior Nat abstraction in Authority.lean is only accurate for normal
reachable counts; do not generalize its unsigned comparison to arbitrary
byte state. CI separately verifies the translated decision and all examples.

Conditional composition: Compose.lean uses all three generated models, rather
than repeating the manually transcribed functions. CI verifies that eight or
fewer misses and valid RPM preserve the floor in the composed decision/update,
while the ninth miss at current output 500 sets floor 500 and any subsequent
clamp returns 500. This composes the slices under the explicit assumption
that the EC scheduler dispatches recovery after the decision and invokes
clamp subsequently, without an intervening change of bounds. It does not
prove scheduler reachability or entire machine behavior.

## Candidate decay guard (iteration 161)

The research-only overlay body at 3a002..3a07a (exclusive) is decoded from
actual assembler bytes emitted by the prior iteration157 run. Fresh assembly
from the unchanged R17DecayCandidate source matches those bytes. The lift
stops at 3a080 before the original clamp call; excludes stack prologue/epilogue.
Inputs: stage, substep, misses, lower, upper, output, request, target RPM,
reported RPM, R0, PSR. Exactly zero or one store to the lower word. 512 original
overlay emulator oracle cases, 216 decrement / 296 hold, including individual
guard violations and mixed boundary values. The mathematical model tests all
inputs, but does not model physical validity of reported RPM or scheduler
reachability. In particular a single high non-sentinel value (e.g. 65534)
can permit decrement if the other guards hold. This is not proof such a value
is reachable at the real EC. Missing sentinel, nonzero misses, non-regulation
stage/substep and reported underspeed prevent decay. The composed model checks
the original clamp with the updated floor, not the stack/ABI or hardware
write/call/return. No firmware deployment.

## Capture domain (iteration 162)

CaptureDomain.lean is explicitly an arithmetic projection, not an automatic
lift of original 192fe (loop and division helpers remain to be lifted). For
channel factor 5 and nonzero integer mean period, the original calculation
reduces to floor(60000000/mean) mod 65536. The capture-domain original
instruction emulator executes 20 synthetic cases through capture ISR,
conversion and validation. 65535 capture period is discarded; zero may be
stored (mixed zero/12000 gives 10000 RPM); all-zero conversion hits an
unmodeled write at address 0, therefore unknown rather than accepted.
Finite arithmetic domain 1..65534 yields no 65534 or 65535 RPM, maximum
65502, and 96 short-period aliases in 2000..6500 RPM. Actual equal period
48 produces 4816 RPM, accepted; a real-like 12458 period produces the
same mathematical word. R17AliasDecay runs complete fault/restart plus
subsequent capture and correction: synthetic period48 reduces candidate
floor499->498, just as normal period12000; period916 gives 65502 and requests
upward correction (no decay), period52585 yields1141 and no decay.
Correction consumes previous validated measurement before next acquisition;
the first replay initially measured the wrong phase, then corrected.
No electrical reachability or hardware timing proof. No changes to overlay.
Lean finite enumeration uses native_decide; concrete examples use decide.

## Numeric bug-pattern screening (iteration 164)

Method agreed in local-lab#289: use embedded C/C++ defect patterns to guide
P-code inspection, then original-instruction replay and Lean. Pattern hits
are hypotheses, not bugs or compiler identification. audit.py is a small
local straight-line screening tool, not whole-program dataflow. Scans three
known decoded ranges (192e6..19356, 199aa..19a08, 19d56..19daa), flags a
16-bit subtraction reaching a signed comparison, and the specific previously
traced wide-return-to-word store. Branches/calls kill local tracked values;
the wide-return rule is explicitly seeded with known 192fe contract, not
generic interprocedural inference. Known NOPs allowed only in audit parsing.
Three candidates: known 192ee->192f2, 19d6c->19d6e, 19d82->19d8a.
Original helper 19d7e executes 24 test inputs in guarded Ghidra emulator:
target2550, RPM35318 -> -20, 35319 -> +25; RPM65502 -> +25 (also at target4600).
This explains the full-cycle upward request previously observed for 65502.
CorrectionDomain.lean projects only SUBW and signed direction, not lookup
table or scheduler. Its universal proofs use bv_decide; direct examples
use decide. Remaining 19d6c candidate needs separate branch/effect replay.
No real electrical reachability, firmware patch, or deployment.

## File-driven Wolfram reachability witness (iteration 167)

Reuse the math-research-lab MCPorter transport rather than a new service.
Node 24.20.0 and MCPorter 0.13.8; package.json, package-lock.json and
config.ci.json at math-research-lab revision 28069cb46c880e0c4d85b9552a715dd83742883d
were independently compared with the exe.dev copies. Lock SHA-256
37e45e866983d84689b1d1a44d40736cf7330dcb95d8eb82d1125f1ef9a09750.
Node Linux x64 tar.gz SHA-256
855d581f8a4eb1a8117e3426de25fe02770592febcfb31369aee1ffbfee9e8ec
is the existing cookbook pin. No system Node replacement.

The exe.dev installation is scoped to
~/workdata/local-lab-289-bios/tools/iteration167 (not a Git artifact).
Rebuild from those pinned package/config files using npm ci --ignore-scripts
--no-audit --no-fund with the pinned Node on PATH. Run from this directory:

    d="$HOME/workdata/local-lab-289-bios/tools/iteration167"
    export PATH="$d/runtime/node-v24.20.0-linux-x64/bin:$PATH"
    python3 wolfram_witness.py reachability-example.json \
      --mcporter "$d/mcp/node_modules/.bin/mcporter" \
      --config "$d/mcp/config.ci.json" \
      --out "$d/witness-new"

Output directory must not exist. The wrapper validates integer graph inputs,
renders Wolfram Language from the same graph as the independent local BFS,
uses the file-driven code=@file call, preserves exact source and output
hashes, and returns MATCH (0), MISMATCH (1), or DEGRADED (2).
CI tests the deterministic adapter offline; external computation is advisory
and explicitly invoked, not a required network-dependent CI gate.
Graph sample is the conditional 22-state abstraction of iteration166;
the reset edge represents full initialization and subsequent return, not a
proven enabled action from every firmware state. A match certifies agreement
on graph calculations only, not correspondence to the entire EC.

## Original dispatcher extraction (iteration 168)

Pinned original payload, Ghidra 12.2 CR16C. ExtractDispatcher.java decodes
raw 190da..191e2 (exclusive), reads the tables at runtime 55248..553dc
(exclusive) via raw offset = runtime address - 20100. The stage index is
0..16 inclusive; word-address code pointers convert as 2*word - 20100.
dispatch_graph.py extracts the second-level table bases from P-code COPY,
checks terminal null entries and indirect pointer scaling, and identifies
stage 10's direct call. Stage 15's special multiple-call path and
flag-controlled bypass are not modeled. This is a layout-specific extractor,
not full symbolic evaluation of arbitrary machine code.

84 table slots (15 null terminators) plus the direct stage-10 handler.
R17DispatchTrace.java replays the original saturated-return harness,
logs selected handler at the call site and before/after state on each
completed dispatcher call. 429 calls / 35 distinct stage/substep pairs;
all selections match the extracted table/direct-call contract. Timers and
hardware remain modeled by the existing guarded emulator.

    python3 -m unittest -v test_dispatch_graph test_wolfram_witness test_audit test_lift
    python3 dispatch_graph.py dispatcher.pcode dispatch.trace --out /tmp/dispatch-graph.json
    cmp dispatch-graph.json /tmp/dispatch-graph.json

The graph contains only observed completed call edges, projected onto
(stage, substep, floor==500), encoded as stage*512+substep*2+saturated.
44 vertices, 46 edges, 28 strongly connected components (two 9-node
cycles and 26 singletons). The saturated normal cycle reaches only its
nine vertices within this observed graph. This is not an exhaustive
reachability or no-escape proof: unobserved edges may be missing, and
projection may join incompatible concrete states. No reset edges are
invented; reset_edges duplicates edges for the existing witness schema.
Wolfram comparison uses canonical SCC ordering by minimum vertex, not
Wolfram's default list ordering. Actual MCPorter run MATCH; failed
ordering-only comparison retained locally as regression evidence.

## Local-to-global reachability bridge (iteration 170)

Inspired by CDCLean.FiniteGraph.reachable_of_adj_reachable (NashWilliams.lean
757–765, source 577e9d9ea326d520f80672ee69b830bf1d513df5), generalize to
directed relations and a projection function. Reachability.lean proves a
generic invariant-preserving simulation of arbitrary finite walks by local
steps, which may map to zero or more abstract steps. Instantiate on the
three lifted slice functions with fixed upper=500, bounded initial floor
and output, and explicit abstract resume. Shows monotone floor for all
finite walks in that model and closure of saturated floor. Reset is an
explicit counterexample outside the relation. This is a theorem about
composition of lifted slices, not a claim that every original dispatcher
or interrupt step is covered. Native bv_decide dependence remains in
the instantiated arithmetic lemmas; generic path induction is separate.
No new dependency on Mathlib.

R17RepeatFaultTrace.java executes a second nine-miss episode after the
original recovery, returning to stage11/sub0 with floor/output500.
330 additional completed dispatch calls; same table checks.
Union with baseline trace: 759 calls, 45 projected vertices, 48 edges,
SCC sizes 35,9,1, 35 vertices reachable from saturated normal state
(previously 9); no observed saturated-to-unsaturated edge.
The 35-state saturated SCC now includes recovery and restart. The
Wolfram/Python comparison uses the same graph JSON; still an observed
projection, not a complete upper approximation. CI regenerates both graphs
and verifies the bridge and a false reset canary. No firmware modification.
