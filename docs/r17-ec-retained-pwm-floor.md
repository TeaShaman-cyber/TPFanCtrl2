# Known hardware limitation: retained EC PWM lower bound on ThinkPad L14 Gen 1

Scope: observed on Intel L14 Gen 1 (20U2), BIOS R17ET45W 1.28,
EC R17HT34W 1.18. Do not generalize to every ThinkPad.

## What a user may notice

Fan speed stays high even when the requested level is lower, the
temperature decreases, and TPFanControl reports successful command
readback. A command acknowledgement confirms the host-facing register,
not the actual motor speed or the firmware's internal PWM limits.
The Smart algorithm cannot guarantee quiet operation when the embedded
controller (EC) retains an elevated minimum output.

## Hardware evidence

The diagnostic row contains target RPM, processed measured RPM,
PWM output, upper PWM bound, and lower PWM bound. PWM values are
firmware command units, not RPM or percentages.

| Observation | Target RPM | Measured RPM | Output | Upper | Lower |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before vendor diagnostic, Nov 25–26 investigation | 4600 | 5432 | 482 | 500 | 482 |
| Before short S3 cycles, Nov 26 | 4600 | 5489 | 498 | 500 | 498 |
| After short S3 cycles | 4600 | 5501 | 498 | 500 | 498 |
| After Intel DTT service restart | 4600 | 5464 | 498 | 500 | 498 |
| After Lenovo LITS downgrade, before reboot | 4600 | 5475 | 498 | 500 | 498 |
| After Windows reboot, Nov 26 | 4600 | 4586 | 360 | 500 | 25 |

Sources: [initial elevated floor](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7175085172),
[S3 comparison](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7200721759),
[DTT restart](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7201286249),
[LITS downgrade](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7201757488),
[verified reboot recovery](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7201936027).

The before/after reboot readings establish that the retained lower
bound returned to 25 on this occasion. Reboot is the only recovery
confirmed by these direct measurements. The preceding LITS downgrade
confounds conclusions about prevention of recurrence. Short S3 cycles
did not provide a sustained reset; other supported recovery paths
remain unverified. A successful application/service restart or a
change of requested level must not be assumed to reset EC state.

## Mechanism and limits of the evidence

Instruction-level experiments with the original R17 firmware show
that consecutive missing tachometer samples can trigger a recovery
path that raises the PWM lower bound. The normal feedback controller
then clamps the requested output to that bound. In one conditional
experiment, repeated recovery raised the bound from 400 to 401,
402, 403 and 404; starting at 498 it reached 499 and 500.

The original command callback and virtual stop/restart experiments
did not clear the elevated bound. These are emulated scenarios,
not physical reproduction of the initiating fault. The reason for
tachometer loss on the actual laptop, the precise recurrence
conditions, and whether another OS or driver can prevent it are
unknown. Host EC transport errors and the internal tachometer
recovery mechanism are distinct; no causal link is established.

See [upstream report #3](https://github.com/mews-se/TPFanCtrl2/issues/3),
[conditional repeated recovery](https://github.com/TeaShaman-cyber/local-lab/issues/289#issuecomment-7160601369)
and [pinned R17 research harness](https://github.com/TeaShaman-cyber/TPFanCtrl2/tree/8129cc326628199e7ba3091cfdeb2bf4bbce509e/research/ec/r17).
An experimental emulator-only decay overlay is documented there;
it is not an approved or installable firmware fix.

## Implications for Smart development

- Separate requested level, confirmed register, fresh tachometer
  observation and real cooling response. Never infer effective RPM
  solely from the selected level.
- If speed remains unexpectedly high, first distinguish genuine
  thermal demand, spin-up/down transients, invalid tach readings
  and a possible retained floor. Do not repeatedly issue commands
  or override the firmware's safety controls to force a lower speed.
- Reboot was observed to recover this machine; it is not an automatic
  action of the controller. Save work and use a normal OS restart
  if appropriate. No guaranteed non-reboot reset is documented.
- Keep temperature protection independent of any RPM discrepancy.
  Accurate CPU MSR measurements can improve the policy's thermal
  input, but cannot repair a retained firmware PWM floor.
- No new driver, firmware flash, raw EC write or CPU power limit
  modification is proposed as a workaround.

## Offline work and hardware acceptance

Offline: improve measurement freshness/validity, replay captured
temperature and power traces, test asymmetric ramp timing, inject
stale/invalid sensors and command acknowledgements with fake I/O,
and continue the pinned firmware emulator research in its separate
branch. Compare predicted policy actions, not hypothetical physical
temperature or acoustics. Keep NVMe monitoring informational.

Hardware-only: validate service-context MSR reads, independently
measure actual fan response and settled low speeds, capture floor
and tach state before/after ordinary lifecycle events, and test
the active Smart policy with bounded safeguards and rollback.
Do not treat offline CI as physical acceptance.
