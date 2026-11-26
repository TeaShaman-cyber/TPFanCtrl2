# TPFanCtrl2

Fan control for ThinkPads running Windows 10/11.

This repository carries on FanDjango's TPFanCtrl2 line, which was archived
in August 2026. The full history is preserved here: every branch and tag,
and the release binaries from V2.3.4 through V2.3.23 mirrored under
[Releases](../../releases).

## Lineage

troubadix's TPFanControl (thinkwiki.de) → [ThinkPad-Forum/TPFanControl](https://github.com/ThinkPad-Forum/TPFanControl)
→ [byrnes' dual-fan mod](https://github.com/byrnes/TPFanControl)
→ [Shuzhengz/TPFanCtrl2](https://github.com/Shuzhengz/TPFanCtrl2)
→ [FanDjango/TPFanCtrl2](https://github.com/FanDjango/TPFanCtrl2) (archived)
→ this repository. Public domain all the way through.

## How it works

One executable, two roles:

- The **engine** owns the embedded controller and drives the fan from a
  configurable temperature curve. It runs either as a plain window or as
  the `TPFanControl` Windows service, which controls the fan from boot as
  SYSTEM with no window.
- The **tray window** is a client of the engine. With the service running
  it needs no rights at all: it draws the state the engine publishes,
  mirrors the engine's log and hands over mode changes.

## Changes since FanDjango V2.3.23

- Fixed a crash that killed a tray client on its first data cycle
  (uninitialized sensor name pointers in the client path).
- The engine log is mirrored into client windows, timestamps intact,
  including a backlog of recent lines when the window starts.
- The tray menu no longer competes with the engine for the EC mutex;
  the hardware toggles are grayed out in a client.
- `ErraticSensorGuard` quarantines sensors that swing tens of degrees
  back and forth between cycles: multiplexed EC registers on newer
  machines that hold no temperature.
- `LidSmartLevel` runs a second smart profile while the lid is closed,
  for machines that work docked. It needs `PowerSuspendMode=2`, smart
  mode and `Level2=` lines in the ini.
- The EC is reached through [PawnIO](https://pawnio.eu), so fan control
  works with memory integrity (HVCI) enabled. TVicPort remains as a
  fallback in the x86 build, loaded dynamically only when needed.
- **Start with Windows** manages a Startup folder shortcut instead of a
  run key entry, which Windows 11 was seen silently skipping at logon.

## Requirements

The EC is reached through one of two port drivers, tried in this order
(override with `PortBackend=` in the ini):

- **PawnIO**: install it from [pawnio.eu](https://pawnio.eu) or
  `winget install namazso.PawnIO`, and keep `LpcACPIEC.bin` and
  `LpcThinkpadEC.bin` (bundled here under `fancontrol/pawnio/`, separate
  files on each release) next to the exe. The driver is WHQL-signed and
  works with memory integrity (HVCI) enabled; this is the right choice
  on any current Windows 11 machine, where TVicPort's driver is refused.
  `LpcThinkpadEC.bin` reaches the EC through the ThinkPad window at
  0x1600, `UseTWR` included, and only loads on ThinkPads;
  `LpcACPIEC.bin` covers the classic ports 0x62/0x66. The program uses
  whichever of the two load and tries 0x1600 first.
- **TVicPort**: put `TVicPort.dll` next to the exe with its kernel
  driver (`TVicPort64.sys` in `System32\drivers`) in place. Both ship
  with the original TPFanControl installer from the SourceForge days;
  uninstalling that program removes them again, so keep your own
  copies. Only works with memory integrity off. `TVicPort.dll` is
  32-bit, so it needs the x86 build.

## Install

1. Put `TPFanControl.exe`, `TPFanControl.ini`, `LpcACPIEC.bin` and
   `LpcThinkpadEC.bin` (or `TVicPort.dll`) in a folder of their own, e.g.
   `C:\Program Files\TPFanCtrl2`. Releases ship the x64 build as
   `TPFanControl.exe` and the x86 build as `TPFanControl-x86.exe`; take
   the x64 one unless you run 32-bit Windows or need TVicPort. The exe
   works under either name.
2. Run the exe as administrator once and enable **Start with Windows** in
   the tray menu. That installs and starts the service and puts a
   shortcut in your Startup folder that brings up the tray window at
   logon, without elevation prompts. `TPFanControl.exe -i` as
   administrator only installs and starts the service, no shortcut. Up
   to 2.5.0 the toggle wrote a run key entry instead, which Windows 11
   was seen silently skipping at logon. Flipping the toggle in either
   direction also cleans up such a leftover entry.
3. Adjust `TPFanControl.ini` next to the exe. The ones that matter most:
   - `Level=temp fan hystUp hystDown`: the fan curve, one line per step
   - `IgnoreSensors=`: sensors that should not drive the fan
   - `SingleFan=1`: on machines with one fan
   - `PowerSuspendMode=2`: keep controlling the fan with the lid closed,
     for docked use; the default hands the fan to the BIOS on lid close

To uninstall, disable **Start with Windows** in the menu and delete the
folder. `TPFanControl.exe -u` as administrator only removes the service
and leaves `TPFanControl.lnk` in your Startup folder, so delete that too.

## Building

Visual Studio Build Tools with the C++ workload, toolset v145. From a
developer prompt:

```
msbuild fancontrol\fancontrol.sln /p:Configuration=Release /p:Platform=x64
msbuild fancontrol\fancontrol.sln /p:Configuration=Release /p:Platform=Win32
```

The x64 build ends up in `fancontrol\x64\Release`, the x86 build in
`fancontrol\Release`.

The icon helper projects under `TPFCIcon` and `TPFCIcon_noballons` still
name the v143 toolset; add `/p:PlatformToolset=v145` when building them
with current tools.

## Tested hardware

ThinkPad X13 Gen 3 (21BN, single fan) runs the service + tray setup as
its daily driver. For models confirmed on earlier versions, see the
[upstream README](https://github.com/Shuzhengz/TPFanCtrl2#readme).

## License

Public domain (Unlicense), inherited from upstream. `LpcACPIEC.bin` and
`LpcThinkpadEC.bin` are PawnIO modules and stay LGPL-2.1, see
`fancontrol/pawnio/COPYING`.
No warranty: this program writes to your embedded controller, use it at
your own risk.


## Research fork: EC transport diagnostic

This fork tracks [local-lab #289](https://github.com/TeaShaman-cyber/local-lab/issues/289)
and [upstream #2](https://github.com/mews-se/TPFanCtrl2/issues/2).
The ordinary EC mailbox transport now propagates PawnIO failures, waits for OBF
and avoids additional port I/O in failure logging. Original upstream commit:
`3acd20ca52c018f30e3a2d376bbe9bd3d1cb52f8`. Ported from the accepted
[local-lab #296](https://github.com/TeaShaman-cyber/local-lab/pull/296).

Offline QA (Python 3.11, pytest 9.2.0, g++):
```
python -m pytest tests -q
python tests/check_transport.py
```
The tests compile selected actual source functions against fake PawnIO and clock;
no EC access, driver or Windows execution. CI runs these tests before the x64
MSBuild and records the exact source commit and file hashes in the artifact.

Diagnostic candidate only: strict OBF compatibility on the ThinkPad LPC window,
layout retry recovery, higher-level acknowledgement, selector writes, legacy
extended-sensor wrappers and physical fan response remain unverified.
TVicPort cannot report per-operation I/O failure. Do not deploy the candidate
before those remaining safety and hardware checks. Original signed modules are
unchanged; no driver signing or firmware changes.

### Inherited-code QA

Our fork follows the Hermes OTel fork's exact-head review practice
([local-lab #289](https://github.com/TeaShaman-cyber/local-lab/issues/289)):
offline regression tests and a Windows build, static discovery over all three
Visual Studio projects, native MSVC analysis of the shipping application, and
a clean exact-head Codex receipt on ready PRs. CI uses read-only permissions and
does not launch the executable. The review gate checks the actual bot identity,
SHA, completion, and explicit absence of unresolved findings, not PR reactions.

```sh
python -m pytest tests -q
python tests/check_transport.py
python tests/mutation_transport.py
python tools/ci/audit_cppcheck.py
```

Mutation testing currently covers a **curated nine-mutant transport pilot**,
not all application logic. Baseline must pass; survivors or failed mutation
execution fail the curated gate. Compile errors and timeouts are not kills.
The initial pilot found two surviving mutations; stale OBF and delayed IBF
tests now detect them. Future mutation expansion must measure coverage rather
than treat this pilot as a whole-code score.

Cppcheck inventories both main Release configurations and the two legacy
icon helpers, plus dormant C++ files not in those projects. Missing SDK includes
and diagnostics remain visible in artifacts. MSVC analysis uses the actual
Windows SDK and verifies compiler /analyze invocation for the shipping app.
Static diagnostics are a discovery baseline, not automatic proof of defects
or a clean bill of health; reports do not suppress existing findings.
Independent whole-code model audit is separate from automated PR diff review.
No live hardware, upstream publication, or deployment is authorized by CI.

### Native C++ tooling

Clang-Format 18 (`.clang-format`) inventories formatting debt on all tracked
C++ source/header files without changing the tree. Use it on touched code
deliberately; existing formatting is a discovery baseline, not a repo-wide
reformat or a zero-debt gate. Keep include order because Windows headers can
depend on it. Actionlint checks GitHub workflow definitions. Clang-Tidy uses
the actual MSBuild/Windows SDK configuration, with analyzer, bugprone and
performance checks (`.clang-tidy`); its inherited findings are reported,
not silently suppressed. MSVC /analyze and Cppcheck remain separate checks.
Heavy tools run on hosted CI, not the developer laptop.

Mull (LLVM-based C++ mutation testing) is a candidate for a separate offline
test target after the hardware boundary is isolated; it is not yet installed
or a required gate. Existing curated transport mutations remain mandatory.
Cloud Codex reviews exact PR heads; optional model audits do not gate CI.

### Experimental Smart observation (fork, no actuator changes)

The Smart thermal policy is under development. The default remains the original
Smart algorithm. An optional single INI line enables counterfactual logging
inside the existing Smart engine, not control. Example syntax (synthetic
parameters, **not** an L14 profile):

```ini
// SmartShadow=100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000 3 4000 4 5000
```

Fields before the first semicolon: RPM hysteresis, rise dwell (ms), fall dwell
(ms), maximum sample gap (ms), urgent temperature (C), recovery temperature
(C), recovery dwell (ms). The next section contains temperature/RPM pairs;
the final section contains consecutive level/RPM pairs. Malformed or duplicate
configuration disables the observer. No default device parameters are supplied.
It starts from the observed level (or firmware if uncalibrated), then updates
only a simulated level. The real fan is always controlled by the original
algorithm. Logs explicitly distinguish actual and projected levels. Read
errors, profile/mode changes and resume reset simulation state. Existing EC
temperatures are not independently verified thermal safety inputs.

Offline replay of the same observer:

```sh
g++ -std=c++11 -I fancontrol tools/research/replay_smart.cpp -o replay-smart
./replay-smart '40 60000 120000 31000 85 70 60000 ; 60 3610 80 4132 ; 4 3610 5 4132' < elapsed-ms-temperature.txt
```

Input is one elapsed nonnegative millisecond value and one Celsius measurement
per line; output is elapsed milliseconds and projected level (128 = firmware).
The example is a coarse research replay using 30-second samples, not a live
configuration. Replayed temperatures are observations of the original
controller, not predictions of another controller's thermal response.
