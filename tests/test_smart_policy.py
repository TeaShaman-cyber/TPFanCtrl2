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


def test_smart_shadow(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "smart-shadow"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(root / "tests/smart_shadow_test.cpp"),
         "-o", str(exe)],
        check=True,
    )
    subprocess.run([str(exe)], check=True)


def test_production_shadow_observer_has_no_actuator(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = source.index("void FANCONTROL::ObserveSmartShadow() {")
    stop = source.index("void FANCONTROL::SmartControl(void) {", start)
    observer = source[start:stop]
    assert "this->ObserveSmartShadow();\n\t\tthis->SmartControl();" in source
    # Compile the real observer with no hardware/SetFan interface at all.
    harness = r'''
#include "smart_shadow.h"
#include <cassert>
#include <cstdio>
#include <string>
bool g_clientMode = false;
unsigned long long tick = 0;
unsigned long long GetTickCount64() { return tick; }
#define sprintf_s std::snprintf
struct FANCONTROL {
    smart_policy::Shadow SmartShadow;
    bool ActiveMode = true, isPowerSuspendState = false, restorePending = false;
    int MaxTemp = 40;
    struct { char FanCtrl = 1; } State;
    std::string message;
    void Trace(const char* s) { message = s; }
    void ObserveSmartShadow();
};
'''
    main = r'''
int main() {
    FANCONTROL f;
    f.MaxTemp = 85;
    f.ObserveSmartShadow();
    assert(f.message.empty());
    assert(f.SmartShadow.configure("100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000 3 4000 4 5000"));
    g_clientMode = true;
    f.ObserveSmartShadow();
    assert(f.message.empty());
    g_clientMode = false;
    f.isPowerSuspendState = true;
    f.ObserveSmartShadow();
    assert(f.message.empty());
    f.isPowerSuspendState = false;
    f.ObserveSmartShadow();
    assert(f.message.find("actual=1, projected=128") != std::string::npos);
    assert(f.State.FanCtrl == 1);
}
'''
    code = tmp_path / "observer.cpp"
    code.write_text(harness + observer + main)
    exe = tmp_path / "observer"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(code), "-o", str(exe)],
        check=True,
    )
    subprocess.run([str(exe)], check=True)


def test_replay_validates_input_and_starts_with_firmware(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "replay"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(root / "tools/research/replay_smart.cpp"),
         "-o", str(exe)],
        check=True,
    )
    cfg = "100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000 3 4000 4 5000"
    result = subprocess.run([str(exe), cfg], input="0 40\n", text=True, capture_output=True, check=True)
    assert result.stdout == "0 128\n"
    for bad in ("-1 40\n", "0 40 junk\n", "0\n"):
        result = subprocess.run([str(exe), cfg], input=bad, text=True, capture_output=True)
        assert result.returncode == 2
