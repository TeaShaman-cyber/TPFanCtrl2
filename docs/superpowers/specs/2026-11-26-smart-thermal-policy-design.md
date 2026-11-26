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
and profile changes. Invalid or stale thermal input and urgent credible
temperature bypass dwell and return to firmware cooling; normal smoothing
must never hide an urgent sample. Distinguish handback from reacquisition
and require valid cooling-side evidence before resuming host control.

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
   manual override and recovery; legacy default parity.
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
The decision core is not wired to the shipping application. Integration and
hardware acceptance remain separate. Additional objective: reduce needless
fan revolutions and airflow exposure as wear/dust proxies; neither is a
validated bearing-lifetime or dust-accumulation model.
