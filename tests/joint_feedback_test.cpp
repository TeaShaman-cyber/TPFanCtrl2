#include "smart_shadow.h"
#include "ec_temp_quality.h"
#include "ec_tach_quality.h"
#include <cassert>
using namespace smart_policy;

static Config config(){
    Config c{};
    assert(parse_shadow_config("100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150",c));
    return c;
}
static Sample s(uint64_t t, double temp=60, int level=4, bool valid=true){
    return {t,temp,level,true,valid,true};
}
int main(){
    const auto cfg=config();
    Policy base(cfg), guarded(cfg);
    // A gap in permission just before fall dwell must discard accumulated credit.
    for(uint64_t t=1000;t<=12000;t+=1000){
        assert(base.evaluate(s(t)).kind==Kind::Hold);
        assert(guarded.evaluate(s(t),true).kind==Kind::Hold);
    }
    assert(base.evaluate(s(13000)).level==3);
    assert(guarded.evaluate(s(13000),false).kind==Kind::Hold);
    for(uint64_t t=14000;t<26000;t+=1000)
        assert(guarded.evaluate(s(t),true).kind==Kind::Hold);
    assert(guarded.evaluate(s(26000),true).level==3);

    // A quality veto does not suppress legitimate rising demand.
    Policy up(cfg);
    for(uint64_t t=1000;t<7000;t+=1000){
        auto a=up.evaluate(s(t,83,1),false);
        if(a.kind==Kind::Level){assert(a.level==2);break;}
        assert(t<6000);
    }
    assert(up.evaluate(s(7000,85,1),false).kind==Kind::Firmware);
    Policy missing(cfg);
    assert(missing.evaluate(s(1000,0,1,false),false).kind==Kind::Firmware);

    // Recovering from BIOS is not a numerically ordered fan-level decrease.
    // It is a separate ownership transition and must restart its own dwell.
    Policy recovery(cfg);
    for(uint64_t t=1000;t<6000;t+=1000)
        assert(recovery.evaluate(s(t,60,128),true).kind==Kind::Hold);
    assert(recovery.evaluate(s(6000,60,128),false).kind==Kind::Hold);
    for(uint64_t t=7000;t<12000;t+=1000)
        assert(recovery.evaluate(s(t,60,128),true).kind==Kind::Hold);
    assert(recovery.evaluate(s(12000,60,128),true).reason==Reason::Recovery);

    // Recovery from the optional host-fault mode also needs uninterrupted quality.
    Policy fault(cfg,7);
    assert(fault.evaluate(s(1000,85,4),false).level==7);
    for(uint64_t t=2000;t<7000;t+=1000)
        assert(fault.evaluate(s(t,60,7),true).kind==Kind::Hold);
    assert(fault.evaluate(s(7000,60,7),false).kind==Kind::Hold);
    for(uint64_t t=8000;t<13000;t+=1000)
        assert(fault.evaluate(s(t,60,7),true).kind==Kind::Hold);
    assert(fault.evaluate(s(13000,60,7),true).level==5);
    // A valid high temperature is not invalidated by a missing tach sample.
    Policy high(cfg);
    assert(high.evaluate(s(1000,105,3),false).kind==Kind::Firmware);
    // Legacy default is unchanged; the gate is not enabled in live code.
    Policy legacy(cfg), explicit_true(cfg);
    for(uint64_t t=1000;t<14000;t+=1000){
        auto a=legacy.evaluate(s(t)); auto b=explicit_true.evaluate(s(t),true);
        assert(a.kind==b.kind && a.level==b.level && a.reason==b.reason);
    }
}
