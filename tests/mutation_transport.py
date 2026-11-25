"""Bounded, source-level mutation pilot of the real extracted EC functions.

A surviving mutant identifies a possible missing test; it is not proof of a
defect. A compiler failure, timeout or infrastructure failure is never a kill.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from check_transport import build_program, extract

ROOT = Path(__file__).resolve().parents[1]

# name, source, function scope, old text, replacement
MUTANTS = [
    ("no_obf_wait", "io", None, "STRICT_EC_READ_OBF_HANDLING = true",
     "STRICT_EC_READ_OBF_HANDLING = false"),
    ("ignore_command_write", "io", "SendEcCommandAndAddress",
     "!PortAccess_TryWriteByte(ctx.ctrlPort, command)",
     "!PortAccess_TryWriteByte(ctx.ctrlPort, command) && false"),
    ("ignore_address_write", "io", "SendEcCommandAndAddress",
     "!PortAccess_TryWriteByte(ctx.dataPort, ctx.ecOffset)",
     "!PortAccess_TryWriteByte(ctx.dataPort, ctx.ecOffset) && false"),
    ("ignore_payload_write", "io", "ExecuteEcWrite",
     "!PortAccess_TryWriteByte(ctx.dataPort, static_cast<UCHAR>(ctx.ecData))",
     "!PortAccess_TryWriteByte(ctx.dataPort, static_cast<UCHAR>(ctx.ecData)) && false"),
    ("ignore_payload_read", "io", "ExecuteEcRead",
     "UCHAR value;\n\tif (!PortAccess_TryReadByte(ctx.dataPort, value))",
     "UCHAR value = 0xff;\n\tif (!PortAccess_TryReadByte(ctx.dataPort, value) && false)"),
    ("ignore_ibf_status_error", "io", "WaitForAllClear",
     "UCHAR data;\n\t\tif (!PortAccess_TryReadByte(port, data)) return false;",
     "UCHAR data = 0;\n\t\t(void)PortAccess_TryReadByte(port, data);"),
    ("ignore_obf_status_error", "io", "WaitForAnySet",
     "UCHAR data;\n\t\tif (!PortAccess_TryReadByte(port, data)) return false;",
     "UCHAR data = 0;\n\t\t(void)PortAccess_TryReadByte(port, data);"),
    ("discard_stale_read_error", "io", "WaitForControllerReady",
     "if (!PortAccess_TryReadByte(dataPort, discarded)) return false;",
     "(void)PortAccess_TryReadByte(dataPort, discarded);"),
    ("skip_ibf_wait", "io", "WaitForAllClear",
     "if ((data & flags) == 0) return true;",
     "if (true) return true;"),
]


def mutate(source, scope, old, new):
    block = extract(source, scope) if scope else source
    if block.count(old) != 1 or source.count(block) != 1:
        raise ValueError("mutation anchor must be unique")
    return source.replace(block, block.replace(old, new, 1), 1)


def evaluate(code):
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "case.cpp"
        executable = Path(tmp) / "case"
        source.write_text(code, encoding="utf-8")
        try:
            compiled = subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", str(source), "-o", str(executable)],
                capture_output=True, text=True, timeout=30,
            )
            if compiled.returncode:
                return "compile_error", compiled.stderr
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired as exc:
            return "timeout", str(exc)
        if result.returncode == 0 and "PASS " in result.stdout and "FAIL " not in result.stdout:
            return "survived", result.stdout
        if result.returncode == 1 and any(line.startswith("FAIL ") for line in result.stdout.splitlines()):
            return "killed", result.stdout
        return "execution_error", result.stdout + result.stderr


def main():
    sources = {kind: (ROOT / "fancontrol" / filename).read_text(encoding="utf-8-sig")
               for kind, filename in (("io", "portio.cpp"), ("access", "portaccess.cpp"))}
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    baseline, log = evaluate(build_program(**sources))
    if baseline != "survived":
        raise RuntimeError(f"baseline not green: {baseline}\n{log}")
    report = {"source_sha": sha, "source_hashes": {
        kind: hashlib.sha256(source.encode()).hexdigest() for kind, source in sources.items()
    }, "baseline": "passed", "mutants": []}
    for name, kind, scope, old, new in MUTANTS:
        altered = sources.copy()
        altered[kind] = mutate(altered[kind], scope, old, new)
        status, output = evaluate(build_program(**altered))
        print(f"{name}: {status}", flush=True)
        report["mutants"].append({"name": name, "status": status, "output": output})
    report_dir = ROOT / "qa-artifacts"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "mutation-transport.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if any(row["status"] != "killed" for row in report["mutants"]):
        raise SystemExit("curated mutation regression or incomplete experiment")


if __name__ == "__main__":
    main()
