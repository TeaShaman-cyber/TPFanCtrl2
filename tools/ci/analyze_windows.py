"""Native MSVC static analysis of the shipping application, without execution."""
import json
import os
from pathlib import Path
import re
import subprocess

from build_windows import ROOT


def main():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if sha != os.environ["EXPECTED_SHA"]:
        raise RuntimeError("checkout identity mismatch")
    vswhere = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft Visual Studio/Installer/vswhere.exe"
    msbuild = subprocess.check_output([
        str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.Component.MSBuild", "-find", r"MSBuild\Current\Bin\MSBuild.exe",
    ], text=True).strip().splitlines()
    if len(msbuild) != 1 or not Path(msbuild[0]).is_file():
        raise RuntimeError("MSBuild not found unambiguously")
    out = ROOT / "qa-artifacts"
    out.mkdir(exist_ok=True)
    report = {"source_sha": sha, "scope": "shipping fancontrol project, Release x64 and Win32",
              "runs": []}
    for platform in ("x64", "Win32"):
        log = out / f"msvc-analysis-{platform}.log"
        result = subprocess.run([
            msbuild[0], "fancontrol/fancontrol.sln", "/t:Rebuild", "/p:Configuration=Release",
            f"/p:Platform={platform}", "/p:RunCodeAnalysis=true", "/p:EnableMicrosoftCodeAnalysis=true",
            "/p:CodeAnalysisTreatWarningsAsErrors=false", "/m", "/v:normal",
        ], cwd=ROOT, capture_output=True, text=True, errors="replace", timeout=360)
        content = result.stdout + "\n" + result.stderr
        log.write_text(content, encoding="utf-8")
        result.check_returncode()
        commands = [line for line in content.splitlines()
                    if re.search(r"(?i)\bcl\.exe\b", line) and re.search(r"(?i)(?:^|\s)/analyze(?:\s|:|$)", line)]
        if not commands:
            raise RuntimeError(f"{platform}: no evidence compiler ran /analyze")
        codes = sorted(set(re.findall(r"\bwarning (C\d+):", content)))
        report["runs"].append({"platform": platform, "analyze_command_count": len(commands), "warning_codes": codes})
        print(platform, codes, flush=True)
    tidy = subprocess.run([
        msbuild[0], "fancontrol/fancontrol.sln", "/t:Rebuild", "/p:Configuration=Release",
        "/p:Platform=x64", "/p:RunCodeAnalysis=true", "/p:EnableMicrosoftCodeAnalysis=false",
        "/p:EnableClangTidyCodeAnalysis=true", "/m", "/v:normal",
    ], cwd=ROOT, capture_output=True, text=True, errors="replace", timeout=360)
    content = tidy.stdout + "\n" + tidy.stderr
    (out / "clang-tidy-x64.log").write_text(content, encoding="utf-8")
    tidy.check_returncode()
    # MSBuild must actually invoke clang-tidy, not merely accept a property.
    commands = [line for line in content.splitlines()
                if re.search(r"(?i)\bclang-tidy(?:\.exe)?\b", line)
                and re.search(r"(?i)\.cpp(?:[\s\"]|$)", line)]
    if not commands:
        raise RuntimeError("no evidence of clang-tidy processing a C++ translation unit")
    checks = sorted(set(re.findall(r"\[((?:clang-analyzer|bugprone|performance|cert)-[a-zA-Z0-9-]+)\]", content)))
    report["clang_tidy"] = {"platform": "x64", "observed_lines": len(commands), "checks": checks}
    print("clang-tidy", checks, flush=True)
    (out / "msvc-analysis-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
