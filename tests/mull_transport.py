"""Automatic mutation discovery of real EC transport functions, not test stubs."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile

from check_transport import PREAMBLE, MAIN, build_program

ROOT = Path(__file__).resolve().parents[1]


def main():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if sha != os.environ["EXPECTED_SHA"]:
        raise RuntimeError("checkout identity mismatch")
    sources = [(ROOT / "fancontrol" / name).read_text(encoding="utf-8-sig")
               for name in ("portio.cpp", "portaccess.cpp")]
    program = build_program(*sources)
    prefix, suffix = PREAMBLE + "\n", "\n" + MAIN
    if not program.startswith(prefix) or not program.endswith(suffix):
        raise RuntimeError("unexpected transport program composition")
    actual = program[len(prefix):-len(suffix)]
    out = ROOT / "qa-artifacts"
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "ec_under_test.hpp").write_text(actual)
        (work / "test.cpp").write_text(PREAMBLE + '\n#include "ec_under_test.hpp"\n' + MAIN)
        (work / "mull.yml").write_text(
            "includePaths:\n  - '.*ec_under_test[.]hpp$'\n"
            "mutators:\n  - cxx_comparison\n  - cxx_boundary\n  - cxx_arithmetic\n  - cxx_logical\n"
            "parallelization:\n  workers: 2\n  executionWorkers: 2\n"
        )
        subprocess.run([
            "clang++-18", "-std=c++17", "-O0", "-g", "-grecord-command-line",
            "-fpass-plugin=/usr/lib/mull-ir-frontend-18", "test.cpp", "-o", "transport",
        ], cwd=work, check=True, timeout=120)
        subprocess.run(["./transport"], cwd=work, check=True, timeout=10)
        result = subprocess.run([
            "mull-runner", "--no-cache", "--allow-surviving", "--workers", "2",
            "--timeout", "1000", "--reporters", "SQLite", "--reporters", "IDE",
            "--report-dir", str(out), "--report-name", "mull-transport", "./transport",
        ], cwd=work, capture_output=True, text=True, timeout=240)
        log = result.stdout + "\n" + result.stderr
        (out / "mull.log").write_text(log)
        print(log[-6000:], flush=True)
        result.check_returncode()
        with sqlite3.connect(out / "mull-transport.sqlite") as db:
            rows = db.execute("SELECT filename, line_number, column_number, mutator, status FROM mutant").fetchall()
        if not rows or any(Path(row[0]).name != "ec_under_test.hpp" for row in rows):
            raise RuntimeError("empty or out-of-scope mutation inventory")
        counts = {str(status): sum(row[4] == status for row in rows) for status in sorted({row[4] for row in rows})}
        if not counts.get("1"):
            raise RuntimeError("no test-detected mutant failures")
        # Keep source and coordinates after temporary build cleanup; no stubs are mutated.
        (out / "ec_under_test.hpp").write_text(actual)
        report = {"source_sha": sha, "scope": "extracted EC transport functions only",
                  "extracted_sha256": hashlib.sha256(actual.encode()).hexdigest(),
                  "mutant_count": len(rows), "raw_status_counts": counts,
                  "status_key": {"1": "test_failed", "2": "test_passed", "3": "timeout",
                                 "4": "crash", "5": "abnormal_exit", "6": "dry_run", "7": "fail_fast"},
                  "mutants": rows}
        (out / "mull-summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k:v for k,v in report.items() if k != "mutants"}))


if __name__ == "__main__":
    main()
