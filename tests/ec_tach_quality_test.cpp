#include "ec_tach_quality.h"
#include <cassert>
#include <initializer_list>
using namespace ec_tach;
int main(){
    Frame f{1000,1700,{2510,1,1},{12496,1,0}};
    auto q=assess(f,2000,true,true,2000);
    assert(q.value==2510 && q.source=='A' && q.quality==Quality::Single);
    f.a={2510,1,0};f.b={2520,0,1};
    assert(assess(f,2000,true,true,2000).quality==Quality::Unknown);
    f.a={0,1,1};f.b={0,1,1};
    q=assess(f,2000,true,true,2000);
    assert(q.value==0 && q.source=='B' && q.quality==Quality::Dual);
    f.b={100,1,1};
    q=assess(f,2000,true,true,2000);
    assert(q.value==-1 && q.quality==Quality::Disagree && q.delta==100);
    f.a={4000,1,1};f.b={4200,1,1};
    assert(assess(f,2000,true,true,2000).value==4200);
    f.b.rpm=4201;
    assert(assess(f,2000,true,true,2000).quality==Quality::Disagree);
    f.b={8191,1,1};f.a={8192,1,1};
    assert(assess(f,2000,true,true,2000).value==8191);
    f.b.rpm=65535;
    assert(assess(f,2000,true,true,2000).value==-1);
    f.a={2510,1,1};f.b={2520,1,1};
    assert(assess(f,3000,true,true,2000).value==2520);
    for(auto r:{assess(f,3001,true,true,2000),assess(f,1699,true,true,2000),
                assess(f,2000,false,true,2000),assess(f,2000,true,false,2000),
                assess(f,2000,true,true,0)}) {
        assert(r.value==-1 && r.quality==Quality::Stale);
    }
    for(unsigned word=0;word<=65535;++word)
      for(int lo=-1;lo<=1;++lo) for(int hi=-1;hi<=1;++hi){
        const bool usable=word<=8191 && lo==1 && hi==1;
        const Word w{word,lo,hi};
        assert(valid(w)==usable);
        auto a=assess(Frame{1000,1700,w,{65535,0,0}},2000,true,true,2000);
        auto b=assess(Frame{1000,1700,{65535,0,0},w},2000,true,true,2000);
        assert(a.value==(usable?int(word):-1));
        assert(b.value==a.value);
        assert(a.source==(usable?'A':'-') && b.source==(usable?'B':'-'));
      }
}
