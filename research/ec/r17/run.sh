#!/usr/bin/env bash
set -euo pipefail
# Usage: Ghidra headless launcher, extracted R17 payload, output log, optional scenario (dispatcher|signal).
headless=$(realpath "$1")
payload=$(realpath "$2")
log=$(realpath -m "$3")
scripts=$(cd "$(dirname "$0")" && pwd)
echo "08faaa8146c65e96164a5e73cc21864c7fb7403ea774ad92055ff77f0579ab4e  $payload" | sha256sum -c
case "${4:-dispatcher}" in
  dispatcher) script=R17Machine.java; marker=R17_DISPATCH_PASS ;;
  signal) script=R17SignalRecovery.java; marker=SIGNAL_RECOVERY_PASS ;;
  *) echo "unknown scenario" >&2; exit 2 ;;
esac
project=$(mktemp -d)
trap 'rm -rf "$project"' EXIT
timeout 60s "$headless" "$project" probe -import "$payload" -processor CR16C:LE:16:default -noanalysis -scriptPath "$scripts" -postScript "$script" -deleteProject > "$log" 2>&1
grep -q "$marker" "$log"
! grep -q 'REPORT SCRIPT ERROR' "$log"
grep -E 'TICK |TIMER_|STATE |PASS |R17_DISPATCH_PASS|SIGNAL_RECOVERY_PASS' "$log"
