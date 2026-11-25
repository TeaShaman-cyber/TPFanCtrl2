# EC authority model — #289

This is a conditional abstraction of observed R17HT34W firmware instructions,
not a firmware modification or a verified translation of the entire CR16 ISA.
The vendor firmware stays outside Git. Source identity: FL2 SHA256
08faaa8146c65e96164a5e73cc21864c7fb7403ea774ad92055ff77f0579ab4e.

| Transition | Payload offset | Evidence |
|---|---|---|
| Stage 11 feedback check | 0x199a6 | Six instruction-emulation cases, iteration47 |
| Stage 12 first action, raise floor | 0x199ea | Three cases, iteration46 |
| Clamp corrected output | 0x19afa | Five overspeed cases, iteration46 |

Stage table 0x55314 contains the normal correction and sample-check handlers;
0x5533c contains the floor-raise handler first. Stage 12 is entered on
feedback <=299 or a ninth consecutive invalid word (0xffff), starting with
a zero counter. A valid sample clears the counter. The counter is 8-bit.
The model omits other flags, substeps, output enable, timing, thermal policy
and scheduler. Its natural-number arithmetic is restricted to ordered bounds
and ordinary output/decrement ranges (no unsigned underflow or overflow).
A return from recovery to normal correction while retaining the raised floor
is **not yet established**. The counterexample is conditional, not a diagnosis
of the physical laptop. The research objective is to discover what permits
or prevents that return.

CI reuses the standalone Lean approach from
[theseus-math-research-lab@28069cb](https://github.com/TeaShaman-cyber/theseus-math-research-lab/blob/28069cb46c880e0c4d85b9552a715dd83742883d/.github/workflows/lean-livestore-model.yml):
same pinned Elan, Lean 4.33.1, runner and bounded positive/negative probe.
No Mathlib or Lake build needed. Exact toolchain cache, no broad restore key;
proof source is always freshly checked. The negative canary asserts a false
strict-decrease property and must fail with its expected proof diagnostic.

## Iteration49: conditional return and accumulation

Original table-selected recovery handlers, restart and ramp handlers reach
stage 11 again with floor retained. Earlier measurement substeps in stages
7 and 9 are supplied as conditional entry snapshots; timer and peripheral
services are stubbed. This is not an end-to-end hardware reachability proof.
At target 3950 and processed feedback 5100, four rounds on a single emulator
give floor/output 401,402,403,404. Starting at 498 gives 499,500,500,500.
These are arbitrary PWM command units, not RPM. The abstract recovery round
is conditional on the observed path, not a total transition relation.
The counter check in the existing model assumes ordinary reachable counter
values (0..9), not arbitrary corrupt signed-byte values. No reset path
outside the examined handlers has been ruled out.

Evidence: local-lab#289, iteration49 logs and scripts on governed exe.dev.
The original firmware is not included.
