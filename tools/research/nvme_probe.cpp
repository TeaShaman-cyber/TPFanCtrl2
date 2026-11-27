#include "nvme_monitor.h"
#include <cstdio>
int main(){
    auto s=nvme_monitor::scan();
    std::printf("NVME count=%u unavailable=%u disk=%u kelvin=%u state=%d\n",
        s.count,s.unavailable,s.disk,s.temperature,static_cast<int>(s.state));
    nvme_monitor::Monitor m;
    for(int i=0;i<100;++i){
        if(m.poll(GetTickCount64())){
            auto n=m.current(GetTickCount64());
            std::printf("ASYNC count=%u unavailable=%u disk=%u kelvin=%u state=%d\n",
                n.count,n.unavailable,n.disk,n.temperature,static_cast<int>(n.state));
            return n.temperature?0:3;
        }
        Sleep(50);
    }
    return 4;
}
