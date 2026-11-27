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
