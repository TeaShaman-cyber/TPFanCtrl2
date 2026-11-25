"""Inventory formatting debt without rewriting inherited source."""
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def main():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if sha != os.environ["EXPECTED_SHA"]:
        raise RuntimeError("checkout identity mismatch")
    tool = "clang-format-18"
    version = subprocess.check_output([tool, "--version"], text=True).strip()
    paths = subprocess.check_output(
        ["git", "ls-files", "-z", "*.cpp", "*.h"], cwd=ROOT
    ).decode().rstrip("\0").split("\0")
    if not paths or not all(paths):
        raise RuntimeError("empty C++ source inventory")
    rows = []
    for path in paths:
        output = subprocess.check_output(
            [tool, "--style=file", "--fallback-style=none", "--output-replacements-xml", path],
            cwd=ROOT, timeout=30,
        )
        parsed = ET.fromstring(output)
        if parsed.tag != "replacements" or parsed.attrib.get("incomplete_format") == "true":
            raise RuntimeError(f"incomplete format analysis: {path}")
        rows.append({"path": path, "replacements": len(parsed.findall("replacement"))})
    report = {"source_sha": sha, "tool": version, "files": rows}
    destination = ROOT / "qa-artifacts"
    destination.mkdir(exist_ok=True)
    (destination / "clang-format.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} files inspected; {sum(row['replacements'] > 0 for row in rows)} need formatting")
    subprocess.run(["git", "diff", "--exit-code"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
