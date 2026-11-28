"""Exercise the actual pair polling code; no EC access."""
import subprocess
from pathlib import Path


def test_ec_pair_audit(tmp_path):
    root = Path(__file__).resolve().parents[1]
    src = (root / "fancontrol/fanstuff.cpp").read_text(encoding="utf-8-sig")
    start = src.index("bool FANCONTROL::ReadEcStatus(")
    end = src.index("bool FANCONTROL::ReadEcRaw(", start)
    code = r"""
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#define sprintf_s std::snprintf
constexpr int TRUE=1;
unsigned long long tick=1000;
unsigned long long GetTickCount64(){return tick;}
void Sleep(int ms){tick+=ms;}
struct FANCONTROL {
    struct FCSTATE {char FanCtrl, Fan2Ctrl, Fan1SpeedLo, Fan1SpeedHi, Sensors[12];};
    bool SingleFan=true, UseTWR=false, locked=false, ShowBiasedTemps=false;
    int EcTelemetryWaitMs=30, EcAuditWaitMs=-1, EcReadReady[3]={-1,-1,-1};
    unsigned long long LastEcAuditLog=0;
    struct {int offs=0;} SensorOffset[12];
    int reads=0, scenario=0;
    std::vector<int> budgets;
    std::string trace;
    bool LockECAccess(){locked=true;tick+=17;return true;}
    void FreeECAccess(){assert(locked);locked=false;}
    void Trace(const char* p){assert(!locked);assert(strlen(p)<160);trace+=p;}
    bool SampleMatch(FCSTATE* a,FCSTATE* b){return a->FanCtrl==b->FanCtrl;}
    bool ReadEcRaw(FCSTATE* p) {
        assert(locked); ++reads; tick+=100; budgets.push_back(EcAuditWaitMs);
        *p=FCSTATE{}; p->FanCtrl=(scenario==1 && reads==1)?2:1;
        p->Fan2Ctrl=p->FanCtrl;
        p->Fan1SpeedLo=char(0xd4);p->Fan1SpeedHi=char(reads%2?0xd4:9);
        p->Sensors[0]=char(reads%2?9:48);
        if(EcAuditWaitMs>=0){EcReadReady[0]=1;EcReadReady[1]=reads%2?0:1;EcReadReady[2]=reads%2?0:1;}
        if(scenario>=3){
            const bool a=reads%2!=0;
            const int t[][4]={{72,9,1,0},{9,72,0,1},{9,10,0,0},{128,128,1,1},{105,68,1,1},{0,127,1,1},{72,9,-1,0},{72,9,1,0}};
            const auto& row=t[scenario-3];
            p->Sensors[0]=char(row[a?0:1]);
            EcReadReady[2]=row[a?2:3];
        }
        return scenario!=2;
    }
    bool ReadEcStatus(FCSTATE*);
};
""" + src[start:end] + r"""
int main(){
    FANCONTROL::FCSTATE s{};
    FANCONTROL f;
    assert(f.ReadEcStatus(&s) && f.reads==2 && !f.locked && f.EcAuditWaitMs==-1);
    assert((unsigned char)s.Fan1SpeedHi==9 && s.Sensors[0]==48);
    assert(f.trace.find("a=d4d4/9 obf=1,0,0 b=09d4/48 obf=1,1,1")!=std::string::npos);
    assert(f.trace.find("tries=1 lock=17 ms=217")!=std::string::npos);
    assert(f.budgets==std::vector<int>({30,30}));
    assert(f.trace.find("EcTempShadow tick=1217 value=48 source=B quality=single")!=std::string::npos);
    const char* expected[]={
        "value=72 source=A quality=single",
        "value=72 source=B quality=single",
        "value=-1 source=none quality=unknown",
        "value=-1 source=none quality=unknown",
        "value=105 source=A quality=dual",
        "value=127 source=B quality=single",
        "value=-1 source=none quality=unknown",
        ""
    };
    const unsigned legacy[]={9,72,10,128,68,127,9,9};
    for(int i=0;i<8;++i){
        FANCONTROL q; q.scenario=i+3; q.ShowBiasedTemps=(i==7); q.SensorOffset[0].offs=(i==7?20:0);
        assert(q.ReadEcStatus(&s)&&q.reads==2&&!q.locked);
        assert((unsigned char)s.Sensors[0]==legacy[i]); // never change control input
        if(i==7) assert(q.trace.find("EcTempShadow")==std::string::npos);
        else assert(q.trace.find(expected[i])!=std::string::npos);
    }
    FANCONTROL zeroOffset; zeroOffset.ShowBiasedTemps=true;
    assert(zeroOffset.ReadEcStatus(&s));
    assert(zeroOffset.trace.find("value=48 source=B quality=single")!=std::string::npos);
    FANCONTROL retry;retry.scenario=1;
    assert(retry.ReadEcStatus(&s) && retry.reads==4 && !retry.locked);
    assert(retry.budgets==std::vector<int>({30,30,0,0}));
    assert(retry.trace.find("tries=2")!=std::string::npos);
    assert(retry.trace.find("EcTempShadow")!=std::string::npos);
    FANCONTROL disabled;disabled.EcTelemetryWaitMs=-1;
    assert(disabled.ReadEcStatus(&s)&&disabled.trace.empty()&&disabled.budgets==std::vector<int>({-1,-1}));
    FANCONTROL dual;dual.SingleFan=false;
    assert(dual.ReadEcStatus(&s)&&dual.trace.empty()&&dual.budgets==std::vector<int>({-1,-1}));
    FANCONTROL fail;fail.scenario=2;
    assert(!fail.ReadEcStatus(&s)&&fail.reads==20&&!fail.locked&&fail.EcAuditWaitMs==-1);
    assert(fail.budgets[0]==30&&fail.budgets[1]==30);
    for(unsigned i=2;i<fail.budgets.size();i++)assert(fail.budgets[i]==0);
}
"""
    cpp = tmp_path / "audit.cpp"
    exe = tmp_path / "audit"
    cpp.write_text(code)
    subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
