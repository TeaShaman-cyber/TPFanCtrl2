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
#include "smart_live.h"
#include <cassert>
int posted=0;
uint64_t tick=1000;
uint64_t GetTickCount64(){return tick++;}
constexpr int WM__NEWDATA=1;
void PostMessage(int,int,int,int){++posted;}
struct FANCONTROL {
    bool SmartMsrShadow=false, CpuMsrAttempted=false;
    unsigned long long CpuWorkerEpoch=0, CpuPollEpoch=0;
    int State=0, hwndDialog=0, ec_ok=1;
    cpu_msr::Frame CpuMsrFrame;
    smart_policy::PollTiming SmartPoll;
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
    assert(f.SmartPoll.worker < f.SmartPoll.ec_done && f.SmartPoll.ec_done < f.SmartPoll.done);
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
#include <cstdio>
#include <string>
#define sprintf_s std::snprintf
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
    smart_policy::PollTiming SmartPoll;
    struct {char FanCtrl=1; char Sensors[12]={42};} State;
    std::string message;
    void Trace(const char* s){assert(std::string(s).size()<128);message+=s;message+="\n";}
    bool success=true;
    bool SmartLiveControl();
    bool SetFan(const char*,int level){++writes;requested=level;FanCommandPending=true; return success;}
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
    assert(f.message.find("reason=rise_dwell")!=std::string::npos);
    assert(f.message.find("level=1 request=2")!=std::string::npos);
    assert(f.message.find("selected=75")!=std::string::npos);
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
    assert(f.message.find("reason=urgent_temperature")!=std::string::npos);
    assert(f.message.find("sensor0=42")!=std::string::npos);
    assert(f.message.find("selected=86")!=std::string::npos);
    f.SmartLive.reset(); f.success=false; f.message.clear();
    f.CpuMsrFrame.valid=false;
    assert(!f.SmartLiveControl() && f.writes==3);
    assert(f.message.find("reason=invalid_input")!=std::string::npos);
    assert(f.message.find("cpu_valid=0")!=std::string::npos);
    assert(f.message.find("set_ok=0")!=std::string::npos);
    assert(f.message.find("age_ms=0 future=0")!=std::string::npos);
    f.SmartLive.reset(); f.success=true; f.message.clear();
    f.FanCommandPending=false; f.State.FanCtrl=1; f.CpuMsrFrame.valid=true;
    f.CpuMsrFrame.package=66; f.CpuMsrFrame.hottest=69;
    tick=10000; f.CpuMsrFrame.time_ms=tick;
    assert(f.SmartLiveControl() && f.writes==3);
    tick=12640; f.CpuMsrFrame.time_ms=tick-15;
    f.SmartPoll={11000,11010,12625,12630,12635};
    assert(f.SmartLiveControl() && f.writes==3);
    assert(f.message.find("reason=poll_gap_reanchor")!=std::string::npos);
    assert(f.message.find("set_ok=-1")!=std::string::npos);
    assert(f.message.find("gap_ms=2640")!=std::string::npos);
    assert(f.message.find("idle=1000 start=10 ec=1615 msr=5 queue=5 handler=5")!=std::string::npos);
    // Repeated valid gaps cause no BIOS write, including with rising demand.
    f.SmartLive.reset(); f.message.clear(); f.CpuMsrFrame.package=40; f.CpuMsrFrame.hottest=40;
    for(tick=20000;tick<=48280;tick+=2828){
        f.CpuMsrFrame.time_ms=tick;
        assert(f.SmartLiveControl() && f.writes==3);
    }
    f.CpuMsrFrame.package=77; f.CpuMsrFrame.hottest=77;
    f.CpuMsrFrame.time_ms=tick;
    assert(f.SmartLiveControl() && f.writes==3);
    tick+=2640; f.CpuMsrFrame.time_ms=tick;
    assert(f.SmartLiveControl() && f.writes==4 && f.requested==2);
    assert(f.message.find("reason=late_rise")!=std::string::npos);
    assert(f.message.find("request=128")==std::string::npos);


}
'''
    code = tmp_path / "live-actuator.cpp"
    code.write_text(harness + source[start:end] + main)
    exe = tmp_path / "live-actuator"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(code), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_live_read_failure_attempts_immediate_handback(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fancontrol.cpp").read_text(encoding="utf-8-sig")
    block = source.split("ULONG FANCONTROL::OnNewData(WPARAM mp1)", 1)[1]
    block = block.split("else {\n\t\tthis->SmartShadow.reset();", 1)[1].split("\n\treturn 0;", 1)[0]
    harness = r'''
#include <cassert>
#include <cstdio>
#define sprintf_s std::snprintf
bool g_clientMode=false;
void SharedState_MarkTachStale(){}
void Sleep(int){}
constexpr int WM_ENDSESSION=1;
void SendMessage(int,int,int,int){}
struct Controller {
    bool ActiveMode=true, SingleFan=true, isPowerSuspendState=false, restorePending=false;
    bool FanCommandPending=false, success=true;
    int CurrentMode=2, ReadErrorCount=0, MaxReadErrors=10, hwndDialog=0, writes=0, mode=2;
    struct Policy {bool on=true; bool enabled(){return on;} void reset(){}} SmartLive,SmartShadow;
    void Trace(const char*){}
    void ModeToDialog(int m){mode=m;}
    bool SetFan(const char*,int level){assert(level==128);++writes;FanCommandPending=!success;return success;}
    int records=0;
    struct {unsigned long long handler=123;} SmartPoll;
    void LogJointPoll(bool good,unsigned long long now,int mode,int level,bool ack,int ec,bool cmd){
        assert(!good && now==123 && mode==-1 && level==-1 && !ack && ec==-1 && !cmd);
        ++records;
    }
    void fail(){bool ok=false; bool joined=true; if(false){} else {this->SmartShadow.reset();
'''
    main = r'''
    }
};
int main(){
 Controller a; a.fail(); assert(a.writes==1 && a.mode==1 && a.records==1);
 Controller b; b.success=false; b.fail(); assert(b.writes==1 && b.FanCommandPending);
 b.CurrentMode=1; b.success=true; b.fail(); assert(b.writes==2 && !b.FanCommandPending);
 Controller c; c.CurrentMode=3; c.fail(); assert(c.writes==0);
 Controller d; d.SmartLive.on=false; d.fail(); assert(d.writes==0);
 Controller e; e.isPowerSuspendState=true; e.fail(); assert(e.writes==0);
 Controller f; f.restorePending=true; f.fail(); assert(f.writes==0);
 Controller g; g_clientMode=true; g.fail(); assert(g.writes==0 && g.records==0);
}
'''
    code=tmp_path/"read-failure.cpp"
    code.write_text(harness+block+main)
    exe=tmp_path/"read-failure"
    subprocess.run(["g++","-std=c++11","-Wall","-Wextra","-Werror","-pedantic",str(code),"-o",str(exe)],check=True)
    subprocess.run([str(exe)],check=True)


def test_msr_reader_ages_from_start_and_rejects_multiple_groups():
    root=Path(__file__).resolve().parents[1]
    source=(root/"fancontrol/cpu_msr_win.h").read_text()
    assert 'GetProcAddress(kernel,"GetActiveProcessorGroupCount")' in source
    assert "if(!group_count || group_count()!=1)return false;" in source
    assert "frame.time_ms=start;" in source
    assert "GetTickCount64()-start>250" in source


def test_ec_temperature_gate(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "ec-temp-gate"
    subprocess.run(
        ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
         "-I", str(root / "fancontrol"), str(root / "tests/ec_temp_gate_test.cpp"),
         "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_ec_temperature_gate_observer(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = source.index("void FANCONTROL::ObserveEcTempGate(")
    end = source.index("bool FANCONTROL::ReadEcStatus(", start)
    observer = source[start:end]
    code = r'''
#include "ec_temp_quality.h"
#include "smart_live.h"
#include <cassert>
#include <cstdio>
#include <string>
#define sprintf_s std::snprintf
uint64_t tick=2000;
uint64_t GetTickCount64(){return tick;}
struct FANCONTROL {
    bool EcTempReport=true, isPowerSuspendState=false, restorePending=false;
    ec_temp::Frame EcTempFrame{1000,1700,70,72,1,1};
    smart_policy::PollTiming SmartPoll{900,950,1750,1800,1900};
    uint64_t CpuPollEpoch=1,CpuEpoch=1;
    std::string msg;
    void Trace(const char* s){msg=s;}
    void ObserveEcTempGate(bool);
};
''' + observer + r'''
int main(){
    FANCONTROL a; a.ObserveEcTempGate(true);
    assert(a.msg.find("value=72 delta=2 age=1000 fresh=1 decrease=1 epoch=1")!=std::string::npos);
    assert(!a.EcTempReport);
    a.msg.clear();a.ObserveEcTempGate(true);assert(a.msg.empty());
    FANCONTROL b; ++b.CpuEpoch;b.ObserveEcTempGate(true);
    assert(b.msg.find("fresh=0 decrease=0 epoch=0")!=std::string::npos);
    FANCONTROL c;c.SmartPoll.dispatch=0;c.ObserveEcTempGate(true);
    assert(c.msg.find("fresh=0 decrease=0")!=std::string::npos);
    FANCONTROL d;d.SmartPoll.worker=1001;d.ObserveEcTempGate(true);
    assert(d.msg.find("fresh=0 decrease=0")!=std::string::npos);
    FANCONTROL e;e.ObserveEcTempGate(false);
    assert(e.msg.find("fresh=0 decrease=0")!=std::string::npos);
    FANCONTROL f;f.restorePending=true;f.ObserveEcTempGate(true);
    assert(f.msg.find("fresh=0 decrease=0 epoch=0")!=std::string::npos);
    FANCONTROL g;g.EcTempFrame={};g.ObserveEcTempGate(false);
    assert(g.msg.find("value=-1 delta=-1 age=0 fresh=0 decrease=0")!=std::string::npos);
    FANCONTROL h;tick=3001;h.ObserveEcTempGate(true);
    assert(h.msg.find("age=2001 fresh=0 decrease=0")!=std::string::npos);
}
'''
    cpp = tmp_path / "gate_observer.cpp"
    cpp.write_text(code)
    exe = tmp_path / "gate_observer"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(root / "fancontrol"), str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    dispatch = (root / "fancontrol/fancontrol.cpp").read_text(encoding="utf-8-sig")
    assert "joined = ::WaitForSingleObject(this->hThread, INFINITE) == WAIT_OBJECT_0;" in dispatch
    assert "if (joined && !g_clientMode) this->ObserveEcTempGate(ok != 0);" in dispatch


def test_ec_tach_quality(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "ec-tach-quality"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(root / "tests/ec_tach_quality_test.cpp"),
                    "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_ec_tach_quality_observer(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = source.index("void FANCONTROL::ObserveEcTachQuality(")
    end = source.index("void FANCONTROL::ObserveEcTempGate(", start)
    code = r'''
#include "ec_tach_quality.h"
#include "smart_live.h"
#include <cassert>
#include <cstdio>
#include <string>
#define sprintf_s std::snprintf
uint64_t tick=2000;
uint64_t GetTickCount64(){return tick;}
struct FANCONTROL {
    bool EcTachReport=true, isPowerSuspendState=false, restorePending=false;
    ec_tach::Frame EcTachFrame{1000,1700,{2510,1,1},{12496,1,0}};
    smart_policy::PollTiming SmartPoll{900,950,1750,1800,1900};
    uint64_t CpuPollEpoch=1,CpuEpoch=1;
    std::string msg;
    void Trace(const char* s){msg=s;}
    void ObserveEcTachQuality(bool);
};
''' + source[start:end] + r'''
int main(){
    FANCONTROL a; a.ObserveEcTachQuality(true);
    assert(a.msg.find("rpm=2510 delta=-1 source=A quality=single age=1000 epoch=1")!=std::string::npos);
    assert(!a.EcTachReport);
    a.msg.clear();a.ObserveEcTachQuality(true);assert(a.msg.empty());
    FANCONTROL b; ++b.CpuEpoch;b.ObserveEcTachQuality(true);
    assert(b.msg.find("rpm=-1 delta=-1 source=- quality=stale")!=std::string::npos);
    FANCONTROL c;c.SmartPoll.dispatch=0;c.ObserveEcTachQuality(true);
    assert(c.msg.find("quality=stale")!=std::string::npos);
    FANCONTROL d;d.SmartPoll.worker=1001;d.ObserveEcTachQuality(true);
    assert(d.msg.find("quality=stale")!=std::string::npos);
    FANCONTROL e;e.ObserveEcTachQuality(false);
    assert(e.msg.find("quality=stale")!=std::string::npos);
    FANCONTROL f;f.restorePending=true;f.ObserveEcTachQuality(true);
    assert(f.msg.find("quality=stale")!=std::string::npos);
    FANCONTROL g;g.EcTachFrame={};g.ObserveEcTachQuality(false);
    assert(g.msg.find("rpm=-1 delta=-1 source=- quality=stale age=0")!=std::string::npos);
    FANCONTROL h;tick=3001;h.ObserveEcTachQuality(true);
    assert(h.msg.find("quality=stale age=2001")!=std::string::npos);
}
'''
    cpp = tmp_path / "tach_observer.cpp"
    cpp.write_text(code)
    exe = tmp_path / "tach_observer"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(root / "fancontrol"), str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    dispatch = (root / "fancontrol/fancontrol.cpp").read_text(encoding="utf-8-sig")
    assert "if (joined && !g_clientMode) this->ObserveEcTachQuality(ok != 0);" in dispatch


def test_joint_feedback_research(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "joint-feedback"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(root / "tests/joint_feedback_test.cpp"),
                    "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_joint_feedback_replay_faults(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "joint-replay"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(root / "tools/research/replay_joint_feedback.cpp"),
                    "-o", str(exe)], check=True)
    cfg = "100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150"

    def row(t, a=3650, b=3650, ar=1, br=1, ta=60, tb=60, tr=1, epoch=1, fresh=1):
        return f"{t-700} {t-50} {t} {a} 1 {ar} {ta} 1 {b} 1 {br} {tb} {tr} {fresh} {epoch}\n"

    def run(rows, seed="4"):
        r = subprocess.run([str(exe), cfg, seed], input="".join(rows), text=True,
                           capture_output=True, check=True)
        return [x.split() for x in r.stdout.splitlines()]

    # The same fault immediately before expiry of downward dwell:
    # loss of one tach byte, both tach readings, sensor disagreement,
    # stopped-vs-running conflict, or a single temperature.
    faults = [dict(br=0), dict(ar=0, br=0), dict(b=4000),
              dict(a=0, b=100), dict(tr=0), dict(tb=68)]
    for fault in faults:
        out = run([row(t, **(fault if t==13000 else {}))
                   for t in range(1000, 27000, 1000)])
        assert out[12][6:10] == ["0", "4", "fall_dwell", "3"]
        assert out[12][10:] == ["4", "none", "-1"]
        assert all(x[12]=="-1" for x in out[13:25])
        assert out[25][11:] == ["fall_dwell","3"]
    # Stale acquisition or wrong epoch must not support a thermal decision.
    for fault in [dict(fresh=0),dict(epoch=0)]:
        out=run([row(1000, **fault)])
        assert out[0][8:10] == ["invalid_input","128"]
        assert out[0][11:] == ["invalid_input","128"]
    # Actual high temperature remains an urgent handback even without tach.
    out=run([row(1000, ta=85,tb=85,ar=0,br=0)])
    assert out[0][11:] == ["urgent_temperature","128"]


def test_full_poll_record(tmp_path):
    root = Path(__file__).resolve().parents[1]
    src = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = src.index("void FANCONTROL::LogJointPoll(")
    end = src.index("void FANCONTROL::ObserveEcTachQuality(", start)
    code = r'''
#include "ec_temp_quality.h"
#include "ec_tach_quality.h"
#include "smart_live.h"
#include <cassert>
#include <cstdio>
#include <string>
#define sprintf_s std::snprintf
bool g_clientMode=false;
struct FANCONTROL {
    bool SingleFan=true,UseTWR=false,isPowerSuspendState=false,restorePending=false;
    int EcTelemetryWaitMs=5,Log2File=1;
    uint64_t JointPollSeq=1,CpuEpoch=2,CpuPollEpoch=2;
    ec_temp::Frame EcTempFrame{1000,1700,70,72,1,1};
    ec_tach::Frame EcTachFrame{1000,1700,{2510,1,1},{12496,1,0}};
    smart_policy::PollTiming SmartPoll{900,950,1750,1800,1900};
    cpu_msr::Frame CpuMsrFrame{};
    struct {char FanCtrl=1;} State;
    bool FanCommandPending=false;
    std::string line;
    void WriteJointPoll(const char* s){line=s;}
    void LogJointPoll(bool,uint64_t,int,int,bool,int,bool);
};
''' + src[start:end] + r'''
int main(){
    FANCONTROL f; f.CpuMsrFrame.valid=true;f.CpuMsrFrame.time_ms=1800;
    f.CpuMsrFrame.package=74;f.CpuMsrFrame.hottest=76;
    f.LogJointPoll(true,2000,3,1,true,72,true);
    assert(f.line=="EcPair full 1,1,900,1000,1700,1900,2000,2,2,1,3,1,1,72,70,1,72,1,2510,1,1,12496,1,0,1,1800,74,76,1,1,0");
    f.LogJointPoll(false,2000,-1,-1,false,-1,false);
    assert(f.line.find("EcPair full 1,0,900,0,0,1900,2000,2,2,0,-1,-1,0,-1,0,-1,0,-1,0,-1,-1,0,-1,-1,0,0,0,0,0,1,0")==0);
    f.line.clear();f.EcTelemetryWaitMs=-1;f.LogJointPoll(true,2000,3,1,true,72,true);assert(f.line.empty());
    f.EcTelemetryWaitMs=5;g_clientMode=true;f.LogJointPoll(true,2000,3,1,true,72,true);assert(f.line.empty());
}
'''
    cpp = tmp_path / "full_poll.cpp"
    cpp.write_text(code)
    exe = tmp_path / "full_poll"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(root / "fancontrol"), str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_full_poll_replay(tmp_path):
    root = Path(__file__).resolve().parents[1]
    exe = tmp_path / "full-replay"
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(root / "fancontrol"), str(root / "tools/research/replay_full_poll.cpp"),
                    "-o", str(exe)], check=True)
    cfg = "100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150"

    def row(seq, t, hi=1, package=60, epoch=0, poll_epoch=0, cpu_age=50, ok=1):
        return ",".join(map(str, [seq,ok,t-800,t-700,t-100,t-50,t,
            epoch,poll_epoch,1,3,1,1,60,60,1,60,1,3650,1,1,3650,1,hi,
            1,t-cpu_age,package,60,1,1,0]))+"\n"

    def run(rows):
        p = subprocess.run([str(exe),cfg,"4"],input="".join(rows),
                           text=True,capture_output=True,check=True)
        return [x.split(",") for x in p.stdout.splitlines()]

    out=run([row(i,i*1000,hi=0 if i==13 else 1) for i in range(1,27)])
    assert out[12][5:10]==["0","4","fall_dwell","3","4"]
    assert out[12][10:]==["none","-1"]
    assert out[25][10:]==["fall_dwell","3"]
    # Missing tach cannot suppress an independently valid urgent MSR.
    out=run([row(1,1000,hi=0,package=90)])
    assert out[0][10:]==["urgent_temperature","128"]
    # An old MSR or epoch mismatch cannot be substituted with a cold EC.
    for r in [row(1,1000,cpu_age=501),row(1,1000,epoch=1),row(1,1000,ok=0)]:
        assert run([r])[0][10:]==["invalid_input","128"]
    # Missing sequence breaks the simulated dwell even if timestamps are close.
    out=run([row(i,i*1000) for i in range(1,13)]+[row(14,13000)])
    assert out[-1][10:]==["none","-1"]
