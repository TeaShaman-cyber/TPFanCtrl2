#include "ec_temp_quality.h"
#include "smart_live.h"
#include <cassert>
using namespace ec_temp;
using namespace smart_policy;
int main() {
    // Exact observed symptom: CPU 65/64, EC0 66, legacy slot 6 spikes 96.
    Slot raw[12]{};
    raw[0]={66,66,1,1}; raw[6]={0,96,1,0};
    auto first=qualify_slots(raw,0xff);
    assert(first.confirmed==66 && first.disputed==96);
    HeatConfirmation gate;
    auto g=gate.evaluate(1000,first,85,2000,true,1);
    assert(!g.fault && !g.allow_decrease);
    Live live;
    assert(live.configure("100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150"));
    cpu_msr::Frame f{}; f.valid=true; f.package=65; f.hottest=64; f.time_ms=1000;
    auto a=live.evaluate(1000,f,first.confirmed,1,true,true,true,nullptr,g.allow_decrease,g.fault);
    assert(a.kind==Kind::Hold);
    // Repeated unresolved heat is not indefinitely suppressed.
    g=gate.evaluate(2000,first,85,2000,true,1);
    assert(g.fault && !g.allow_decrease);
    f.time_ms=2000;
    assert(live.evaluate(2000,f,first.confirmed,1,true,true,true,nullptr,g.allow_decrease,g.fault).kind==Kind::Firmware);
    // Corroborated platform heat must remain immediate.
    raw[6]={96,94,1,1};
    auto hot=qualify_slots(raw,0xff);
    assert(hot.confirmed==96 && hot.disputed==0);
    Live real; assert(real.configure("100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150"));
    assert(real.evaluate(2000,f,hot.confirmed,1,true,true,true).reason==Reason::UrgentTemperature);
    // Real CPU emergency and stale CPU cannot be hidden by EC admission.
    f.package=86; f.hottest=86; f.time_ms=3000;
    assert(real.evaluate(3000,f,66,1,true,true,true,nullptr,false,false).reason==Reason::UrgentTemperature);
    f.package=65; f.hottest=65; f.time_ms=3000;
    assert(real.evaluate(3600,f,66,1,true,true,true,nullptr,false,false).reason==Reason::InvalidInput);
    // A single disputed high cannot permit a cooling decrease, even if the fan is in firmware.
    gate.reset(); assert(gate.evaluate(3000,first,85,2000,true,128).allow_decrease==false);
    gate.reset(); assert(gate.evaluate(3000,first,85,2000,true,0).fault);
    gate.reset(); assert(gate.evaluate(3000,first,85,2000,false,1).fault);
    gate.reset(); assert(!gate.evaluate(3000,first,85,2000,true,1).fault);
    raw[6]={0,0,1,1};
    auto clear=qualify_slots(raw,0xff);
    assert(clear.confirmed==66 && clear.disputed==0);
    assert(gate.evaluate(4000,clear,85,2000,true,1).allow_decrease);
    auto stale=gate.evaluate(4500,clear,85,2000,false,1);
    assert(!stale.fault && !stale.allow_decrease);
    assert(!gate.evaluate(5000,first,85,2000,true,1).fault);
    raw[6]={96,96,1,1};
    assert(qualify_slots(raw,1).confirmed==66); // ignored sensor cannot override configuration
    raw[6]={96,96,0,0};
    assert(qualify_slots(raw,0xff).disputed==96);
    raw[6]={91,105,1,1};
    auto both=qualify_slots(raw,0xff);
    assert(both.confirmed>=91); // independent ready readings both hot
    raw[6]={128,0,1,1};
    assert(qualify_slots(raw,0xff).disputed==0);
}
