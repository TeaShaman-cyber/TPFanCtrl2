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
    // Each emergency path exposes the actual reason, not a generic thermal label.
    auto check=[&](uint64_t now, uint64_t sampled, int temp, bool valid,
                   bool epoch, bool ack, int level, Reason reason) {
        Live fresh;
        assert(fresh.configure(cfg));
        cpu_msr::Frame frame{};
        frame.valid=valid; frame.time_ms=sampled;
        frame.package=temp; frame.hottest=temp;
        DecisionInput input{};
        auto result=fresh.evaluate(now,frame,0,level,epoch,ack,true,&input);
        assert(result.kind==Kind::Firmware && result.reason==reason);
        assert(input.now==now && input.cpu_time==sampled && input.cpu_valid==valid);
        assert(input.epoch==epoch && input.acknowledged==ack && input.level==level);
        assert(input.selected==(input.valid?temp:0));
    };
    check(1000,1000,85,true,true,true,1,Reason::UrgentTemperature);
    check(1000,1000,60,false,true,true,1,Reason::InvalidInput);
    check(1000,499,60,true,true,true,1,Reason::InvalidInput);
    check(1000,1001,60,true,true,true,1,Reason::InvalidInput);
    check(1000,1000,60,true,false,true,1,Reason::InvalidInput);
    check(1000,1000,60,true,true,false,1,Reason::UnconfirmedLevel);
    check(1000,1000,60,true,true,true,7,Reason::LevelOutsideCalibration);
    Live timed; assert(timed.configure(cfg));
    f.package=60; f.hottest=60; f.time_ms=1000;
    assert(timed.evaluate(1000,f,0,1,true,true,true).kind==Kind::Hold);
    f.time_ms=3100; DecisionInput input{};
    assert(timed.evaluate(3100,f,0,1,true,true,true,&input).reason==Reason::PollGapReanchor);
    assert(input.gap==2100 && input.selected==60 && input.valid);
    timed.reset(); f.time_ms=4000;
    assert(timed.evaluate(4000,f,0,1,true,true,true).kind==Kind::Hold);
    assert(timed.evaluate(4000,f,0,1,true,true,true,&input).reason==Reason::PollDiscontinuity);
    assert(input.gap==0);
    for (int scenario=0; scenario<2; ++scenario) {
        Live laptop;
        assert(laptop.configure("100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150"));
        f.package=66; f.hottest=66; f.time_ms=1000;
        assert(laptop.evaluate(1000,f,69,1,true,true,true).kind==Kind::Hold);
        uint64_t now=scenario?3828:3640;
        f.package=scenario?76:66; f.hottest=scenario?77:66;
        f.time_ms=now-(scenario?63:15);
        auto action=laptop.evaluate(now,f,scenario?64:69,1,true,true,true,&input);
        assert(action.kind==Kind::Hold && action.reason==Reason::PollGapReanchor);
        assert(input.gap==(scenario?2828:2640) && input.selected==(scenario?77:69));
    }
    Live pending; assert(pending.configure(cfg));
    f.package=75; f.hottest=75;
    for(uint64_t t=1000;t<=4000;t+=1000){f.time_ms=t; a=pending.evaluate(t,f,0,1,true,true,true);}
    assert(a.kind==Kind::Level && a.reason==Reason::RiseDwell);
    f.time_ms=5000; assert(pending.evaluate(5000,f,0,1,true,false,true).kind==Kind::Hold);
    f.time_ms=6000; assert(pending.evaluate(6000,f,0,1,true,false,true).reason==Reason::PendingTimeout);
    Live mismatch; assert(mismatch.configure(cfg));
    for(uint64_t t=1000;t<=4000;t+=1000){f.time_ms=t; a=mismatch.evaluate(t,f,0,1,true,true,true);}
    f.time_ms=5000; assert(mismatch.evaluate(5000,f,0,1,true,true,true).reason==Reason::PendingMismatch);
    assert(!live.configure(cfg));
    assert(eval(9000,2,true,true,true).kind==Kind::Hold);
}
