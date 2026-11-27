# Opt-in Smart thermal policy

Coordination: TeaShaman-cyber/local-lab#289. Development in this fork;
upstream submission is separate, after hardware acceptance.

## Intent

Quiet useful cooling without lowering PSC7 CPU performance. Do not raise
fan speed merely for a transient temperature spike. Increase cooling when
heat actually persists or safety requires it. Reduce speed without chatter.
Physical RPM, temperature and performance are acceptance evidence, not
just a smooth mathematical target. No firmware, driver or power-plan changes.

## Approaches

* Native Smart table only: smallest change, already has asymmetric temperature
  hysteresis; no duration or adjacent-step guarantee.
* Extend the existing Smart engine with an opt-in decision policy: selected
  direction. Reuse native fan commands, existing telemetry and profile UI.
  Keep the legacy policy and INI behavior unchanged by default.
* A separate daemon or direct PWM control: rejected here. Another EC owner
  is unnecessary and fine RPM transport is not verified for R17.

Reference: tpnsfand at 132c6e2adabc381445ce17babc7c738742020c22
(linear RPM target and control-state hysteresis, not its model-specific
registers); local-lab PR #292 (curve and quantizer), #295 (raw tach).
Current fork main differs from installed f4a0bcae35c2e7cd92433e79d57c5009f29ad798.
Do not deploy an arbitrary main build: its strict OBF path has failed on L14.

## Proposed policy

Pure deterministic C++ decision component, no Windows or EC IO in the
component. Explicit elapsed monotonic time, observed/acknowledged fan level,
validity/freshness, and temperature inputs. Piecewise monotone RPM target
mapped to measured adjacent levels with hysteresis. Reject inconsistent
calibration rather than fabricate a level. The normal transition requires
sustained demand (shorter for increases, longer for decreases); at most one
adjacent step per confirmed transition. A transient that clears the threshold
cancels its pending transition. A pending command does not count as applied.
Reset history on manual/Smart transitions, suspend/resume, discontinuities,
and profile changes. Normal smoothing must never hide an urgent sample.

### Revised control authority (2026-11-27, issue #289, iterations 137–138)

The host policy is a workaround for the known R17 firmware fan-regulation
defect, not an enhancement that assumes the firmware automatic regulator
is trustworthy. Vendor contact and defect localization continue separately;
a vendor fix, commitment, release date or acceptance is not established.
The host solution must not depend on any of them. No firmware modification
or disabling of CPU/platform hardware thermal protections is in scope.

The earlier universal automatic handback assumption is superseded.
The following are design requirements for the next candidate, not claims
about the existing implementation or demonstrated hardware safety.

| Condition | Required behavior / evidence |
| --- | --- |
| Fresh valid thermal frame, confirmed running calibrated level, late poll | Retain host ownership. Discard unobserved dwell credit; use current measured demand. An isolated scheduling delay is not a thermal emergency. Repeated gaps require a bounded response that cannot starve rising cooling demand. |
| Urgent credible temperature | Bypass ordinary dwell. Evaluate a verified high-cooling fixed command under host control. Do not assume the top calibrated ordinary step is adequate emergency cooling. Preserve independent CPU/platform protections. |
| Invalid or stale thermal frame, command path still available | No downward transition based on unknown temperature. Evaluate conservative fixed cooling with explicit fault state and recovery evidence, not an automatic return to the defective policy. |
| Failed EC read/write or inconsistent confirmation | Distinguish telemetry failure from actual loss of actuator authority. A fixed command and a BIOS command both use the EC interface; neither can be claimed applied without verified readback. Escalate an unresolved loss of authority rather than pretend cooling is confirmed. |
| Explicit BIOS selection, shutdown, suspend, service ownership loss | Separate lifecycle cases, not ordinary Smart control. Preserve existing protective lifecycle behavior until an alternative is demonstrated safe; operator selection remains authoritative. |

The host controls requested fan levels through the existing EC command
interface. It does not directly own PWM or replace the embedded RPM loop:
fixed levels may still encounter the retained PWM-floor defect. A command
readback confirms the control byte, not physical RPM, heat removal or
safety. Before choosing a high-cooling fallback, validate command support,
spin-up, physical response and thermal effectiveness on this model. If the
host cannot command cooling, evaluate available platform protections and a
safe relinquishment/escalation path separately. No unvalidated replacement
for the existing emergency or lifecycle protections is deployable.

Observed triggers motivating this revision: gaps of 2640 ms at selected
69 C (CPU age 15 ms) and 2828 ms at selected 77 C (CPU age 63 ms) both
caused BIOS handback under the previous 2000 ms guard. Neither was an
urgent thermal sample. The c651c7d bounded-gap candidate is an intermediate
offline/CI experiment only, not a hardware-approved solution. Its remaining
automatic handbacks and repeated-gap behavior require review.

Thresholds, durations and RPM table are explicit experiment parameters,
not universal device defaults. For L14 the prior provisional upper target
is about 85 C, not a demonstrated safety threshold. Valid short plateaus:
level 4 = 3610 RPM, level 5 = 4132 RPM (10/10 each); no sustained-load
certification. Current user manual level 1 is observed ~2542 RPM, not a
validated plateau. Levels 3 and 6 not calibrated; trial aborted on changed
user mode. Preserve the user's active selection during development.

## Acceptance

1. RED/GREEN deterministic tests on real decision code: short spike,
   sustained warming, cooling dwell, oscillation, adjacent transitions,
   urgent/invalid/stale input, time discontinuity, command failure,
   manual override and recovery; legacy default parity. In particular,
   reproduce both observed delayed polls, repeated/long/nonmonotonic gaps,
   stale/invalid temperatures, high demand during timing faults, stopped
   fan, failed writes and false or delayed confirmations. Prove no
   unobserved downward dwell credit and no starvation of urgent cooling.
   Fault recovery must not produce recurrent host/firmware oscillation.
2. Replay measured traces offline against legacy Smart; compare number of
   changes, maximum temperature and time above temperature bands where
   measured. Replay cannot establish the physical outcome of a different
   policy. No fictitious RPM or temperatures.
3. Integrate only into existing Smart engine; retain single owner,
   native command readback and emergency handling. Validate reliable
   thermal input, including plausible false-low EC samples. No new
   privileged interface or daemon. Run existing fork QA and exact-head review.
4. Separately reviewed Windows candidate: bounded reversible trial with
   independent temperature observations and verified rollback; compare matched
   workloads, clocks/power, raw RPM, subjective noise and behavior on resume.
   No extra throttling; no unnecessary RPM; no recurrent floor saturation.
5. Only after live acceptance consider an upstream PR, with explicit
   publication authorization. Keep working installed binary until candidate
   acceptance.

First offline implementation: see the core plan and fancontrol/smart_policy.h.
The decision core is integrated in the experimental candidate branch.
The revised authority requirements above are not yet implemented or accepted.
Integration, candidate CI and hardware acceptance remain separate. Additional objective: reduce needless
fan revolutions and airflow exposure as wear/dust proxies; neither is a
validated bearing-lifetime or dust-accumulation model.

### Iteration 140 experimental implementation

A fresh validated frame after a late poll no longer causes a BIOS handback
solely for lateness. No missing interval contributes to rise/fall dwell.
Two late observations of upward demand with no intervening reversal or
level change permit an adjacent increase; this evidence-count rule is
provisional, not a measured timing optimum. Cooling downward requires
continuous ordinary dwell. A late observation of a stopped fan requests
restart. Unconfirmed commands, actual invalid inputs, nonmonotonic time
and unexpected level changes are separate faults.

The pure Policy constructor also supports an explicitly selected regulated
emergency level (nonzero, at least the top calibration step, at most 7)
for offline comparison. It requests high cooling immediately on invalid
or urgent thermal input, latches it through the valid cool recovery
window and restarts normal down dwell afterward. Failed confirmation
remains a separate loss-of-authority path; existing fallback is retained
there, not evidence that firmware is reliable. The Live and Shadow
adapters intentionally do not enable this experimental argument. Physical
emergency setpoint adequacy, transport-loss semantics, and hardware
acceptance remain open. No live emergency behavior is changed by this
prototype.

### Iteration 143 transport experiment (opt-in)

The R17 conversion and mailbox replay (issue #289 iteration 142) motivate
separate readiness evidence for registers 84, 85 and 78. The new
EcTelemetryWaitMs setting defaults to -1 (disabled). Zero observes OBF
without deliberately waiting; 1..30 waits for at most the configured
software time budget per byte in the first pair only (six waits, at most
180 ms nominal additional wait, excluding scheduling and IO latency).
Existing retries are observation-only. No additional EC read command,
address write or data-port read is issued. Strict mode is unchanged;
legacy compatibility data without observed OBF is still unverified.
Readiness is not proof of physical accuracy or correct mailbox ownership.

EcPair records both received tach words and sensor slot 0 (subject to
existing sensor offset configuration), three readiness values per sample,
pair attempts and mutex/total durations. It reports suspect samples and
a periodic sample of accepted pairs. It does not overwrite measured
data, reject an otherwise accepted status poll, change command
verification, or modify the Smart decision law. It does not yet cover
all rejected-pair contents. The layer is restricted to the existing
single-fan, non-TWR status poll and is disabled by default. The
fault-injection result is not hardware validation. Start with observation
only in a separately authorized live trial; compare readiness, raw
anomalies and timing before trying bounded waiting. Keep strict global
OBF disabled on this model until evidence supports changing it.
