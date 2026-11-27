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
    stop = source.index("// Live opt-in", start)
    observer = source[start:stop]
    assert "this->ObserveSmartShadow();" in source
    assert "this->SmartControl();" in source
    # Compile the real observer with no hardware/SetFan interface at all.
    harness = r'''
#include "smart_shadow.h"
#include "cpu_msr.h"
#include <cassert>
#include <cstdio>
#include <string>
bool g_clientMode = false;
unsigned long long tick = 0;
unsigned long long GetTickCount64() { return tick; }
#define sprintf_s std::snprintf
struct FANCONTROL {
    smart_policy::Shadow SmartShadow;
    bool SmartMsrShadow = false;
    cpu_msr::Frame CpuMsrFrame;
    unsigned long long CpuPollEpoch=0, CpuEpoch=0;
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
    f.SmartShadow.reset(); f.message.clear();
    f.SmartMsrShadow=true; f.MaxTemp=40; tick=1000;
    f.CpuMsrFrame.valid=true; f.CpuMsrFrame.time_ms=tick;
    f.CpuMsrFrame.package=85; f.CpuMsrFrame.hottest=85;
    f.ObserveSmartShadow();
    assert(f.message.find("temp=85, valid=1") != std::string::npos);
    f.SmartShadow.reset(); f.message.clear();
    f.MaxTemp=0;
    f.ObserveSmartShadow();
    assert(f.message.find("temp=85, valid=1") != std::string::npos);
    f.SmartShadow.reset(); f.message.clear();
    ++f.CpuEpoch;
    f.ObserveSmartShadow();
    assert(f.message.find("valid=0") != std::string::npos);
    f.SmartShadow.reset(); f.message.clear();
    f.CpuPollEpoch=f.CpuEpoch; tick=1600;
    f.ObserveSmartShadow();
    assert(f.message.find("valid=0") != std::string::npos);
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


def test_cpu_msr(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "cpu-msr"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(root / "tests/cpu_msr_test.cpp"),
         "-o", str(exe)], check=True,
    )
    subprocess.run([str(exe)], check=True)


def test_msr_worker_is_opt_in_and_invalidates_failed_reads(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fancontrol.cpp").read_text(encoding="utf-8-sig")
    start = source.index("int FANCONTROL::WorkThread() {")
    stop = source.index("\n}", start) + 2
    worker = source[start:stop]
    harness = r'''
#include "cpu_msr.h"
#include <cassert>
int posted=0;
constexpr int WM__NEWDATA=1;
void PostMessage(int,int,int,int){++posted;}
struct FANCONTROL {
    bool SmartMsrShadow=false, CpuMsrAttempted=false;
    unsigned long long CpuWorkerEpoch=0, CpuPollEpoch=0;
    int State=0, hwndDialog=0, ec_ok=1;
    cpu_msr::Frame CpuMsrFrame;
    struct Shadow {bool enabled() const{return true;}} SmartShadow;
    struct Live {bool enabled() const{return false;}} SmartLive;
    struct Reader {
        int opens=0, closes=0, samples=0, resets=0;
        bool open(const wchar_t*){++opens;return true;}
        void close(){++closes;}
        void reset_energy(){++resets;}
        cpu_msr::Frame sample(){++samples;cpu_msr::Frame f{}; f.valid=true;return f;}
    } CpuMsr;
    int ReadEcStatus(int*){return ec_ok;}
    int WorkThread();
};
'''
    main = r'''
int main(){
    FANCONTROL f;
    f.WorkThread(); assert(f.CpuMsr.opens==0 && f.CpuMsr.samples==0 && !f.CpuMsrFrame.valid);
    f.SmartMsrShadow=true;
    f.WorkThread(); assert(f.CpuMsr.opens==1 && f.CpuMsr.samples==1 && f.CpuMsrFrame.valid);
    f.WorkThread(); assert(f.CpuMsr.opens==1 && f.CpuMsr.samples==2);
    f.ec_ok=0; f.WorkThread(); assert(!f.CpuMsrFrame.valid && f.CpuMsr.resets==1 && f.CpuMsr.samples==2);
    f.ec_ok=1; ++f.CpuPollEpoch; f.WorkThread();
    assert(f.CpuMsr.closes==1 && f.CpuMsr.opens==2 && f.CpuMsr.samples==3 && f.CpuMsrFrame.valid);
    assert(posted==5);
}
'''
    code = tmp_path / "msr-worker.cpp"
    code.write_text(harness + worker + main)
    exe = tmp_path / "msr-worker"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(code), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)

def test_nvme_observation(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for test in ("nvme_thermal", "nvme_alert"):
        exe = tmp_path / test
        subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-I", str(root / "fancontrol"), str(root / ("tests/" + test + "_test.cpp")),
                        "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)

def test_nvme_ui_is_separate_from_fan_control():
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fancontrol.cpp").read_text(encoding="utf-8-sig")
    observer = source.split("void FANCONTROL::UpdateNvmeMonitor() {", 1)[1].split("void FANCONTROL::RemoveTextIcons", 1)[0]
    assert "NvmeMonitor.poll" in observer
    assert "ProcessIdToSessionId" in observer
    assert "SetBalloon" in observer and "DiShowballon" in observer
    for forbidden in ("MaxTemp", "SetFan(", "SmartControl(", "ModeToDialog(", "State.Sensors"):
        assert forbidden not in observer
    worker = source.split("int FANCONTROL::WorkThread() {", 1)[1].split("\n}", 1)[0]
    assert "NvmeMonitor" not in worker

def test_smart_live(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "smart-live"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(root / "tests/smart_live_test.cpp"),
                    "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_actual_live_actuator_uses_confirmed_state(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = source.index("bool FANCONTROL::SmartLiveControl() {")
    end = source.index("void FANCONTROL::LogCpuMsr()", start)
    assert "if (this->SmartLive.enabled() && this->SingleFan)" in source
    harness = r'''
#include "smart_live.h"
#include <cassert>
bool g_clientMode=false;
uint64_t tick=0;
uint64_t GetTickCount64(){return tick;}
struct FANCONTROL {
    smart_policy::Live SmartLive;
    bool ActiveMode=true, SingleFan=true, isPowerSuspendState=false, restorePending=false;
    bool FanCommandPending=false;
    int MaxTemp=0, writes=0, requested=-1;
    uint64_t CpuPollEpoch=0, CpuEpoch=0;
    cpu_msr::Frame CpuMsrFrame;
    struct {char FanCtrl=1;} State;
    bool SmartLiveControl();
    bool SetFan(const char*,int level){++writes;requested=level;FanCommandPending=true;return true;}
};
'''
    main = r'''
int main(){
    FANCONTROL f;
    assert(f.SmartLive.configure("50 3000 10000 2000 85 70 5000 ; 40 2500 80 4000 ; 1 2500 2 3000 3 3500 4 4000"));
    f.CpuMsrFrame.valid=true; f.CpuMsrFrame.package=70; f.CpuMsrFrame.hottest=75;
    for(tick=1000;tick<=4000;tick+=1000){
        f.CpuMsrFrame.time_ms=tick;
        assert(f.SmartLiveControl());
    }
    assert(f.writes==1&&f.requested==2&&f.State.FanCtrl==1);
    f.CpuMsrFrame.time_ms=tick;
    assert(f.SmartLiveControl()&&f.writes==1);
    f.FanCommandPending=false;f.State.FanCtrl=2;
    ++tick;f.CpuMsrFrame.time_ms=tick;
    assert(f.SmartLiveControl()&&f.writes==1);
    g_clientMode=true;
    assert(f.SmartLiveControl()&&f.writes==1);
    g_clientMode=false;
    f.CpuMsrFrame.package=86;f.CpuMsrFrame.hottest=86;
    assert(f.SmartLiveControl()&&f.requested==128&&f.writes==2);
}
'''
    code = tmp_path / "live-actuator.cpp"
    code.write_text(harness + source[start:end] + main)
    exe = tmp_path / "live-actuator"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(code), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
