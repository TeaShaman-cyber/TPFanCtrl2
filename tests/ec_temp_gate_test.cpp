#include "ec_temp_quality.h"
#include <cassert>
#include <cstdint>
using namespace ec_temp;
int main() {
    const Frame f{1000,1700,70,72,1,1};
    auto q=assess(f,2000,true,true,2000);
    assert(q.value==72 && q.delta==2 && q.allow_decrease);
    assert(assess(f,3000,true,true,2000).allow_decrease);
    assert(!assess(f,3001,true,true,2000).allow_decrease);
    assert(!assess(f,1699,true,true,2000).allow_decrease);
    assert(!assess(f,2000,false,true,2000).allow_decrease);
    assert(!assess(f,2000,true,false,2000).allow_decrease);
    assert(!assess(Frame{1701,1700,70,72,1,1},2000,true,true,2000).allow_decrease);
    auto hot=assess(Frame{1000,1700,105,68,1,1},2000,true,true,2000);
    assert(hot.value==105 && hot.delta==37 && !hot.allow_decrease);
    auto one=assess(Frame{1000,1700,95,9,1,0},2000,true,true,2000);
    assert(one.value==95 && !one.allow_decrease);
    auto missing=assess(Frame{1000,1700,128,0,1,1},2000,true,true,2000);
    assert(missing.value==-1 && !missing.allow_decrease);
    assert(!assess(Frame{1000,1700,70,75,1,1},2000,true,true,0).allow_decrease);
    assert(assess(Frame{1000,1700,70,75,1,1},2000,true,true,2000).allow_decrease);
    assert(!assess(Frame{1000,1700,70,76,1,1},2000,true,true,2000).allow_decrease);
    // Exhaust the complete byte/readiness domain, including unknown flags.
    for(unsigned a=0;a<256;++a) for(unsigned b=0;b<256;++b)
      for(int ra=-1;ra<=1;++ra) for(int rb=-1;rb<=1;++rb) {
        const bool va=ra==1 && a>=1 && a<=127;
        const bool vb=rb==1 && b>=1 && b<=127;
        auto r=assess(Frame{1000,1700,a,b,ra,rb},2000,true,true,2000);
        assert(r.value==(va?(vb?(a>b?int(a):int(b)):int(a)):vb?int(b):-1));
        assert(r.allow_decrease==(va && vb && (a>b?a-b:b-a)<=5));
        assert(!assess(Frame{1000,1700,a,b,ra,rb},3001,true,true,2000).allow_decrease);
        assert(!assess(Frame{1000,1700,a,b,ra,rb},2000,false,true,2000).allow_decrease);
        assert(!assess(Frame{1000,1700,a,b,ra,rb},2000,true,false,2000).allow_decrease);
      }
}
