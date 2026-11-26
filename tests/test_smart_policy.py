"""Compile and run actual offline C++ policy, with no Windows or EC access."""
import subprocess
from pathlib import Path


def test_smart_policy(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "smart-policy"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(root / "tests/smart_policy_test.cpp"),
         "-o", str(exe)],
        check=True,
    )
    subprocess.run([str(exe)], check=True)
