#include "smart_live.h"
#include <cassert>
using namespace smart_policy;
int main(){
    Live live;
    const char* cfg="50 3000 10000 2000 85 70 5000 ; 40 2500 80 4000 ; 1 2500 2 3000 3 3500 4 4000";
    assert(live.configure(cfg));
    cpu_msr::Frame f{};
    f.valid=true;f.package=70;f.hottest=75;
    auto eval=[&](uint64_t t,int level,bool epoch,bool ack,bool active){
        f.time_ms=t;return live.evaluate(t,f,0,level,epoch,ack,active);
    };
    for(uint64_t t=1000;t<=3000;t+=1000)assert(eval(t,1,true,true,true).kind==Kind::Hold);
    auto a=eval(4000,1,true,true,true);assert(a.kind==Kind::Level && a.level==2);
    assert(eval(5000,1,true,false,true).kind==Kind::Hold);
    assert(eval(6000,2,true,true,true).kind==Kind::Hold);
    assert(eval(7000,2,true,true,false).kind==Kind::Hold);
    assert(eval(8000,2,false,true,true).kind==Kind::Firmware);
    assert(!live.configure(cfg));
    assert(eval(9000,2,true,true,true).kind==Kind::Hold);
}
