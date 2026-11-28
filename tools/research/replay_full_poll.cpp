// Offline comparison, not a live-controller trace or physical feedback model.
// The recorded MSR/platform input is shared; only the joint veto differs.
// Hypothetical command acknowledgements are virtual, not real EC readbacks.
#include "smart_shadow.h"
#include "cpu_msr.h"
#include "ec_temp_quality.h"
#include "ec_tach_quality.h"
#include <iostream>
#include <sstream>
#include <algorithm>
using namespace smart_policy;
int main(int argc,char** argv){
    if(argc!=3)return 2;
    Config cfg{};
    if(!parse_shadow_config(argv[1],cfg))return 2;
    int seed; char extra;
    std::istringstream initial(argv[2]);
    if(!(initial>>seed)||initial>>extra||
       (seed!=128&&(seed<cfg.calibration.front().level||seed>cfg.calibration.back().level)))return 2;
    Policy base(cfg), gated(cfg);
    int bl=seed,gl=seed;
    uint64_t previous=0,prev_seq=0,prev_epoch=0;
    std::string line;
    while(std::getline(std::cin,line)){
        std::replace(line.begin(),line.end(),',',' ');
        std::istringstream s(line);
        uint64_t seq,dispatch,begin,end,handler,now,epoch,poll_epoch,cpu_time;
        int ok,ordered,mode,level,ack,ec,ra,rb,alo,ahi,blo,bhi,cpu_valid,pkg,hot,cmd,post,pending;
        unsigned ta,tb,a,b;
        if(!(s>>seq>>ok>>dispatch>>begin>>end>>handler>>now>>epoch>>poll_epoch
             >>ordered>>mode>>level>>ack>>ec>>ta>>ra>>tb>>rb>>a>>alo>>ahi>>b>>blo>>bhi
             >>cpu_valid>>cpu_time>>pkg>>hot>>cmd>>post>>pending)||s>>extra||
             seq<=prev_seq||now<=previous)return 2;
        const bool discontinuity=prev_seq&&(seq!=prev_seq+1||epoch!=prev_epoch);
        if(discontinuity){base.reset();gated.reset();}
        previous=now;prev_seq=seq;prev_epoch=epoch;
        const bool current=epoch==poll_epoch;
        const bool timing=ok==1&&ordered==1&&dispatch<=begin&&end<=handler&&handler<=now;
        const auto t=ec_temp::assess({begin,end,ta,tb,ra,rb},now,current,timing,2000);
        const auto r=ec_tach::assess({begin,end,{a,alo,ahi},{b,blo,bhi}},now,current,timing,2000);
        cpu_msr::Frame c{};c.valid=cpu_valid==1;c.time_ms=cpu_time;c.package=pkg;c.hottest=hot;
        int temp=0;
        const bool valid=ok==1&&current&&cpu_msr::shadow_temperature(c,now,ec,temp);
        const bool permit=valid&&t.allow_decrease&&r.quality==ec_tach::Quality::Dual&&r.value>0;
        const auto x=base.evaluate({now,double(temp),bl,true,valid,true});
        const auto y=gated.evaluate({now,double(temp),gl,true,valid,true},permit);
        if(!permit&&y.kind==Kind::Level&&(gl==128||y.level<gl))return 3;
        std::cout<<seq<<','<<now<<','<<temp<<','<<valid<<','<<ec_tach::name(r.quality)<<','<<permit
                 <<','<<bl<<','<<reason_name(x.reason)<<','<<x.level
                 <<','<<gl<<','<<reason_name(y.reason)<<','<<y.level<<'\n';
        if(x.kind!=Kind::Hold)bl=x.level;
        if(y.kind!=Kind::Hold)gl=y.level;
    }
    return std::cin.bad()?2:0;
}
