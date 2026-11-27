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

#### Direct Intel CPU telemetry (experimental observer only)

On the tested single-package Intel laptop, the optional line
`SmartMsrShadow=1` supplements an enabled SmartShadow with direct DTS and
RAPL readings. It does not select a control mode or change fan commands.
It is disabled by default. Keep the official signed `IntelMSR.bin` next
to the program; the research module is from PawnIO.Modules release
[0.2.11](https://github.com/namazso/PawnIO.Modules/releases/tag/0.2.11),
SHA-256 `d6ed85d65ab17a22f813ef98207d6d537155ee2ded5976a21cb48413c9b92e5f`.
It is LGPL-2.1-or-later and is not redistributed by this change.
No LHM, WMI, HTTP or additional service is needed.

Only five fixed MSR reads are exposed by the adapter. The CPU scan
runs on the existing EC worker after the EC read, not inside the EC
transaction. A failed or old frame is invalid; a suspend/resume epoch
invalidates earlier observations. The observer uses the maximum of valid
CPU and existing EC temperatures and rejects invalid EC input. Power is
diagnostic only, not part of the decision rule. The 250 ms scan limit and
500 ms observation-age limit are provisional research thresholds, not
hard driver deadlines. A native standalone probe and offline tests do not
establish the full Windows engine's shutdown/resume or service behavior.
Do not enable this in a live engine before that verification.

#### Optional NVMe temperature warning

Set `NvmeMonitor=1` in TPFanControl.ini to show the NVMe temperature
and status in the interactive window title and tray tooltip. This is an
independent informational feature, not a fan-control sensor. It works
in the tray/client without an extra monitoring service. It uses Windows
storage property queries only, with no Samsung Magician, LHM or WMI.
The option is off by default during testing.

The monitor checks detected NVMe disks about every 15 seconds, shows the
highest severity and then the hottest disk in that severity, and labels
incomplete data. A warning is raised within 5 K of the controller's
reported warning limit, or on its SMART thermal warning bit; critical
uses the reported critical limit. Missing limits are not invented.
Notifications are raised on severity escalation, rearmed after two
normal scans, and respect NoBallons. No threshold changes, storage
writes, fan commands or CPU throttling are performed. The background
read owns only its result; one stalled disk read cannot stall the
fan engine, and stale observations become unavailable. No guarantee
of every controller/USB/RAID transport being supported is made.
Monitoring requires the interactive instance to be running.

#### Experimental active Smart policy

`SmartLive=` accepts the same explicit calibration/curve format as
`SmartShadow=`. It is opt-in and currently only supports a single fan.
In Smart mode it replaces (not supplements) the legacy table controller.
It uses fresh CPU MSR readings even if the EC temperature is quarantined,
and never discards a hotter valid EC observation. This is CPU/platform
observation, not proof that every platform sensor is covered. Manual mode
continues to work normally. The observer logs CPU temperature and package
power about every 15 seconds, including in manual mode. Power is not yet
an actuator input. Invalid/stale CPU data, command failure or the urgent
temperature still use the existing firmware fail-safe. Firmware is not
the ordinary target of a healthy temperature curve. Do not activate an
unvalidated calibration on a live system.

A zero-RPM calibration point `0 0` is optional. When present, the
policy can stop the fan after at least 30 seconds of sustained downward
demand (or the configured longer fall dwell). Below the recovery temperature the normal rise dwell applies. At the
recovery temperature a stopped fan restarts immediately, and a running
fan is not stopped at or above that threshold. Thermal fail-safe retains
priority.
Recovery from firmware starts with a running step even if the curve
requests zero. These timings are provisional, not a validated
machine-specific temperature curve.

For experimental adaptive rise timing, append an optional eighth number
(hot rise dwell in milliseconds) before the first semicolon in the
SmartLive or SmartShadow configuration. Omission preserves the fixed
rise dwell. The new number must be positive and no greater than the
ordinary rise dwell. Between recovery and urgent temperature, the
upward demand accumulates faster, using the slower of the two adjacent
temperature-based rates for each measured interval. A new step still
requires contiguous upward demand and a confirmed previous command.
Falling dwell, stopped-fan restart, and urgent/invalid-input fail-safe
are unchanged. This is not a prediction model and does not use power as
a control input. For example, 6000 ms ordinary and 1000 ms hot rise
are experimental timing values, not validated hardware defaults.
