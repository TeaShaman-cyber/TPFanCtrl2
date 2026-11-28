#include "bounded_tach_gate.h"
#include "smart_shadow.h"
#include <cassert>
#include <initializer_list>
using namespace ec_tach;
using research::BoundedTachGate;
int main(){
    const Assessment dual{2510,3,'B',Quality::Dual};
    const Assessment single{2520,-1,'A',Quality::Single};
    BoundedTachGate g;
    assert(!g.observe(1,1000,1,true,true,single,4));
    assert(g.observe(2,2000,1,true,true,dual,4));
    assert(g.observe(3,3000,1,true,true,single,4));
    assert(!g.observe(4,4000,1,true,true,single,4));
    g.reset();
    assert(g.observe(2,2000,1,true,true,dual,4));
    assert(g.observe(3,2500,1,true,true,single,4));
    assert(!g.observe(3,2600,1,true,true,single,4));

    assert(g.observe(5,5000,1,true,true,dual,4));
    assert(!g.observe(6,6000,1,true,true,single,128));
    assert(g.observe(7,7000,1,true,true,dual,4));
    assert(!g.observe(8,8000,1,true,true,single,1));
    assert(g.observe(9,9000,1,true,true,dual,4));
    assert(!g.observe(10,11001,1,true,true,single,4));
    assert(g.observe(11,12000,1,true,true,dual,4));
    assert(!g.observe(13,13000,1,true,true,single,4));
    assert(g.observe(14,14000,1,true,true,dual,4));
    assert(!g.observe(15,15000,2,true,true,single,4));
    assert(g.observe(16,16000,2,true,true,dual,4));
    assert(!g.observe(17,17000,2,false,true,single,4));
    assert(g.observe(18,18000,2,true,true,dual,4));
    assert(!g.observe(19,19000,2,true,false,single,4));
    for(auto q : {Quality::Unknown, Quality::Disagree, Quality::Stale}){
        g.reset();
        assert(g.observe(1,1000,1,true,true,dual,4));
        assert(!g.observe(2,2000,1,true,true,Assessment{-1,-1,'-',q},4));
        assert(!g.observe(3,3000,1,true,true,single,4));
    }
    g.reset();
    assert(g.observe(1,1000,1,true,true,dual,4));
    assert(!g.observe(2,2000,1,true,true,Assessment{0,-1,'A',Quality::Single},4));
    assert(g.observe(3,3000,1,true,true,dual,4));
    assert(!g.observe(4,4000,1,true,true,Assessment{2711,-1,'A',Quality::Single},4));
    assert(g.observe(5,5000,1,true,true,dual,4));
    assert(g.observe(6,6000,1,true,true,Assessment{2710,-1,'A',Quality::Single},4));
    g.reset();
    assert(g.observe(1,1000,1,true,true,dual,4));
    assert(!g.observe(2,2000,1,true,true,single,3)); // no bridging across command change
    // A single good word may preserve dwell but never authorize a fall command.
    smart_policy::Config c{};
    assert(smart_policy::parse_shadow_config("100 6000 12000 2000 85 70 5000 2000 ; 60 2550 70 2550 80 3650 84 4150 ; 1 2550 2 3050 3 3300 4 3650 5 4150",c));
    smart_policy::Policy p(c);
    for(uint64_t t=1000;t<13000;t+=1000)
        assert(p.evaluate({t,60,4,true,true,true},true,true).kind==smart_policy::Kind::Hold);
    assert(p.evaluate({13000,60,4,true,true,true},true,false).kind==smart_policy::Kind::Hold);
    assert(p.evaluate({14000,60,4,true,true,true},true,true).level==3);
    smart_policy::Policy rise(c);
    for(uint64_t t=1000;t<7000;t+=1000){
        auto a=rise.evaluate({t,83,1,true,true,true},false,false);
        if(a.kind==smart_policy::Kind::Level){assert(a.level==2);break;}
        assert(t<6000);
    }
    assert(rise.evaluate({7000,90,1,true,true,true},false,false).kind==smart_policy::Kind::Firmware);
    smart_policy::Policy loss(c);
    for(uint64_t t=1000;t<13000;t+=1000)
        assert(loss.evaluate({t,60,4,true,true,true},true,true).kind==smart_policy::Kind::Hold);
    assert(loss.evaluate({13000,60,4,true,true,true},true,false).kind==smart_policy::Kind::Hold);
    assert(loss.evaluate({14000,60,4,true,true,true},false,false).kind==smart_policy::Kind::Hold);
    for(uint64_t t=15000;t<27000;t+=1000)
        assert(loss.evaluate({t,60,4,true,true,true},true,true).kind==smart_policy::Kind::Hold);
    assert(loss.evaluate({27000,60,4,true,true,true},true,true).level==3);

}
