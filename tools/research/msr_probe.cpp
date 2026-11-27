#include "cpu_msr_win.h"
#include "smart_shadow.h"
#include <cstdio>
int wmain(int argc,wchar_t** argv){
    if(argc!=2)return 2;
    cpu_msr::Reader reader;
    if(!reader.open(argv[1])){std::puts("OPEN_FAILED");return 3;}
    smart_policy::Shadow shadow;
    // Synthetic replay only, not an L14 deployment profile.
    if(!shadow.configure("100 3000 10000 2000 85 70 5000 ; 40 2000 80 5000 ; 1 2000 2 3000 3 4000 4 5000"))return 4;
    for(int i=0;i<12;++i){
        auto start=GetTickCount64();
        auto frame=reader.sample();
        const int hot=frame.package>frame.hottest?frame.package:frame.hottest;
        auto s=shadow.observe(GetTickCount64(),hot,1,frame.valid);
        std::printf("SAMPLE %d valid=%d package=%d hottest=%d power_valid=%d watts=%.3f projected=%d ms=%llu\n",
            i,frame.valid?1:0,frame.package,frame.hottest,frame.power_valid?1:0,frame.watts,s.projected,
            static_cast<unsigned long long>(GetTickCount64()-start));
        if(!frame.valid)return 5;
        Sleep(1000);
    }
    return 0;
}
