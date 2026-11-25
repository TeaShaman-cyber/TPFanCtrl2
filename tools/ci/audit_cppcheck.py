"""Whole-project static discovery, not a claim that all warnings are defects."""
import collections
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = (
    ("fancontrol/fancontrol.vcxproj", "x64", 11),
    ("fancontrol/fancontrol.vcxproj", "Win32", 11),
    ("TPFCIcon/TPFCIcon.vcxproj", "Win32", 7),
    ("TPFCIcon_noballons/TPFCIcon.vcxproj", "Win32", 7),
)


def summarize(xml, log, expected):
    errors = ET.fromstring(xml).findall("./errors/error")
    totals = collections.Counter(e.get("severity", "unknown") for e in errors)
    counts = re.findall(r"(\d+)/(\d+) files checked", log)
    if not counts or tuple(map(int, counts[-1])) != (expected, expected):
        raise ValueError(f"analysis did not report completion of {expected} translation units")
    return dict(sorted(totals.items()))


def main():
    tool = os.environ.get("CPPCHECK", "cppcheck")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    expected = os.environ.get("EXPECTED_SHA")
    if expected and sha != expected:
        raise RuntimeError("checkout identity mismatch")
    version = subprocess.check_output([tool, "--version"], text=True).strip()
    destination = ROOT / "qa-artifacts"
    destination.mkdir(exist_ok=True)
    report = {"source_sha": sha, "tool": version, "scope": "all three tracked VS projects, Release",
              "limitations": "Linux Cppcheck lacks full Windows SDK; diagnostics require triage",
              "projects": []}
    actual = set(subprocess.check_output(["git", "ls-files", "*.vcxproj"], cwd=ROOT, text=True).splitlines())
    if actual != {project for project, _, _ in PROJECTS}:
        raise RuntimeError("project inventory changed; update audit coverage")
    compiled = {
        (Path(project).parent / node.attrib["Include"].replace("\\", "/")).as_posix()
        for project, _, _ in PROJECTS
        for node in ET.parse(ROOT / project).findall(".//{*}ClCompile")
        if "Include" in node.attrib
    }
    tracked_cpp = set(subprocess.check_output(["git", "ls-files", "*.cpp"], cwd=ROOT, text=True).splitlines())
    dormant = sorted(tracked_cpp - compiled)
    if not compiled <= tracked_cpp:
        raise RuntimeError("project references untracked source")
    report["compiled_unique"] = len(compiled)
    report["dormant_sources"] = dormant
    for project, platform, expected_units in PROJECTS:
        name = f"{Path(project).parent.name}-{platform}"
        count = sum("Include" in node.attrib for node in ET.parse(ROOT / project).findall(".//{*}ClCompile"))
        if count != expected_units:
            raise RuntimeError(f"{project}: translation unit inventory changed ({count})")
        result = subprocess.run([
            tool, f"--project={project}", f"--project-configuration=Release|{platform}",
            f"--platform={'win64' if platform == 'x64' else 'win32W'}",
            "--library=windows", "--enable=warning,style,performance,portability,information",
            "--inconclusive", "--xml", "--xml-version=2", "--max-configs=4",
        ], cwd=ROOT, capture_output=True, text=True, timeout=180)
        (destination / f"{name}.xml").write_text(result.stderr, encoding="utf-8")
        (destination / f"{name}.log").write_text(result.stdout, encoding="utf-8")
        result.check_returncode()
        counts = summarize(result.stderr, result.stdout, expected_units)
        report["projects"].append({"project": project, "platform": platform,
                                   "translation_units": expected_units, "diagnostics": counts})
        print(name, counts, flush=True)
    if dormant:
        result = subprocess.run([
            tool, "--platform=win32W", "--library=windows", "-D_WIN32=1", "-D_WINDOWS=1",
            "--enable=warning,style,performance,portability,information", "--inconclusive",
            "--xml", "--xml-version=2", "--max-configs=4", *dormant,
        ], cwd=ROOT, capture_output=True, text=True, timeout=180)
        (destination / "dormant.xml").write_text(result.stderr, encoding="utf-8")
        (destination / "dormant.log").write_text(result.stdout, encoding="utf-8")
        result.check_returncode()
        report["dormant_diagnostics"] = summarize(result.stderr, result.stdout, len(dormant))
    (destination / "cppcheck-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
