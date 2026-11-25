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
    (out / "msvc-analysis-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
