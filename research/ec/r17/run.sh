#!/usr/bin/env bash
set -euo pipefail
# Usage: Ghidra headless launcher, extracted R17 payload, output log.
headless=$(realpath "$1")
payload=$(realpath "$2")
log=$(realpath -m "$3")
scripts=$(cd "$(dirname "$0")" && pwd)
echo "08faaa8146c65e96164a5e73cc21864c7fb7403ea774ad92055ff77f0579ab4e  $payload" | sha256sum -c
project=$(mktemp -d)
trap 'rm -rf "$project"' EXIT
timeout 60s "$headless" "$project" probe -import "$payload" -processor CR16C:LE:16:default -noanalysis -scriptPath "$scripts" -postScript R17Machine.java -deleteProject > "$log" 2>&1
grep -q 'R17_DISPATCH_PASS' "$log"
! grep -q 'REPORT SCRIPT ERROR' "$log"
grep -E 'TICK |TIMER_|R17_DISPATCH_PASS' "$log"
