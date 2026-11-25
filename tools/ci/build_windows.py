"""Build and inventory an x64 diagnostic artifact; never start the executable."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]


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
    subprocess.run([msbuild[0], "-version"], check=True)
    subprocess.run([
        msbuild[0], "fancontrol/fancontrol.sln", "/p:Configuration=Release",
        "/p:Platform=x64", "/m", "/v:minimal",
    ], cwd=ROOT, check=True)
    fan = ROOT / "fancontrol"
    binaries = list((fan / "x64/Release").glob("*.exe"))
    if len(binaries) != 1:
        raise RuntimeError(f"expected one x64 executable, got {binaries}")
    data = binaries[0].read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[:2] != b"MZ" or data[pe:pe + 4] != b"PE\0\0" or struct.unpack_from("<H", data, pe + 4)[0] != 0x8664:
        raise RuntimeError("not an AMD64 PE executable")
    destination = ROOT / "build-artifact"
    destination.mkdir()
    files = {
        "TPFanControl.exe": binaries[0],
        "TPFanControl.ini": fan / "TPFanControl.ini",
        "LpcACPIEC.bin": fan / "pawnio/LpcACPIEC.bin",
        "LpcThinkpadEC.bin": fan / "pawnio/LpcThinkpadEC.bin",
        "PawnIO-COPYING": fan / "pawnio/COPYING",
        "LICENSE": ROOT / "LICENSE",
    }
    manifest = {"source_sha": sha, "platform": "x64", "files": {}}
    for name, source in files.items():
        output = destination / name
        shutil.copyfile(source, output)
        manifest["files"][name] = {"sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                                   "size": output.stat().st_size}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
