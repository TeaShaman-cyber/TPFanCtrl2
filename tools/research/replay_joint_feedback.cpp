// Research only. No hardware interface. Same input to two policy instances;
// each hypothetical command is acknowledged only in its virtual trajectory.
#include "smart_shadow.h"
#include "ec_temp_quality.h"
#include "ec_tach_quality.h"
#include <iostream>
#include <sstream>
using namespace smart_policy;
int main(int argc,char** argv){
    if(argc!=3)return 2;
    Config c{};
    if(!parse_shadow_config(argv[1],c))return 2;
    std::istringstream seed(argv[2]);int initial;char extra;
    if(!(seed>>initial) || seed>>extra ||
       (initial!=128 && (initial<c.calibration.front().level || initial>c.calibration.back().level)))return 2;
    Policy baseline(c), guarded(c);
    int baselevel=initial, gatelevel=initial;
    uint64_t previous=0;
    std::string line;
    while(std::getline(std::cin,line)){
        uint64_t begin,end,now; unsigned a,b,ta,tb;
        int al,ah,bl,bh,ra,rb,fresh,epoch;
        std::istringstream row(line);
        if(!(row>>begin>>end>>now>>a>>al>>ah>>ta>>ra>>b>>bl>>bh>>tb>>rb>>fresh>>epoch)
           || row>>extra || now<=previous || (fresh!=0 && fresh!=1) || (epoch!=0 && epoch!=1))return 2;
        previous=now;
        const auto t=ec_temp::assess({begin,end,ta,tb,ra,rb},now,epoch==1,fresh==1,2000);
        const auto r=ec_tach::assess({begin,end,{a,al,ah},{b,bl,bh}},now,epoch==1,fresh==1,2000);
        // Temperature is EC-only in this experiment, not the real MSR+platform
        // input. A zero tach is a measurement, not evidence of running cooling.
        const bool valid=t.fresh && t.value>0;
        const bool permit=t.allow_decrease && r.quality==ec_tach::Quality::Dual && r.value>0;
        const auto x=baseline.evaluate({now,double(t.value),baselevel,true,valid,true});
        const auto y=guarded.evaluate({now,double(t.value),gatelevel,true,valid,true},permit);
        if(!permit && y.kind==Kind::Level && (gatelevel==128 || y.level<gatelevel))return 3;
        std::cout<<end<<' '<<now<<' '<<t.value<<' '<<valid<<' '<<r.value<<' '<<ec_tach::name(r.quality)<<' '<<permit<<' '
                 <<baselevel<<' '<<reason_name(x.reason)<<' '<<x.level<<' '
                 <<gatelevel<<' '<<reason_name(y.reason)<<' '<<y.level<<'\n';
        if(x.kind!=Kind::Hold)baselevel=x.level;
        if(y.kind!=Kind::Hold)gatelevel=y.level;
    }
    return std::cin.bad()?2:0;
}
