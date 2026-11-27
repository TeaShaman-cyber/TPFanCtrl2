#include "smart_shadow.h"
#include <cassert>
#include <limits>
using namespace smart_policy;

int main() {
    const char* line = "100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000 3 4000 4 5000";
    Shadow s;
    assert(!s.enabled());
    assert(s.configure(line));
    assert(s.enabled());
    assert(!s.configure(line)); // duplicate opt-in is invalid, fail closed
    assert(!s.enabled());
    s = Shadow{};
    assert(!s.configure("100 -3 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000"));
    s = Shadow{};
    assert(!s.configure("100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 3 5000"));
    s = Shadow{};
    assert(!s.configure("100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 5000 junk"));
    s = Shadow{};
    assert(s.configure(line));
    auto r = s.observe(0, 40, 1, true);
    assert(r.projected == 1 && r.action.kind == Kind::Hold);
    for (unsigned t=1000;t<4000;t+=1000)
        assert(s.observe(t,79,1,true).action.kind==Kind::Hold);
    r=s.observe(4000,79,1,true);
    assert(r.action.kind==Kind::Level && r.projected==2);
    // The physical fan stays at 1; only the counterfactual state progresses.
    r=s.observe(5000,79,1,true);
    assert(r.projected==2 && r.action.kind==Kind::Hold);
    assert(s.observe(6000,85,1,true).projected==128);
    assert(s.observe(7000,60,1,false).projected==128);
    s.reset();
    assert(s.observe(8000,40,4,true).projected==4);
    s.reset();
    assert(s.observe(9000,40,7,true).projected==128);
}
