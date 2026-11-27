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
