#include "nvme_thermal.h"
#include <cassert>
using namespace smart_policy;
int main(){
    NvmeAlert alert;
    assert(!alert.observe(ThermalState::Normal));
    assert(alert.observe(ThermalState::Warning));
    assert(!alert.observe(ThermalState::Warning));
    assert(!alert.observe(ThermalState::Unknown));
    assert(!alert.observe(ThermalState::Warning));
    assert(alert.observe(ThermalState::Critical));
    assert(!alert.observe(ThermalState::Warning));
    assert(!alert.observe(ThermalState::Normal));
    assert(!alert.observe(ThermalState::Normal));
    assert(alert.observe(ThermalState::Warning));
    uint32_t h[12]={48,48,3,2,2,0,40,512,0,0,0,0};
    size_t off=0;
    assert(nvme_payload(h,560,2,512,off)&&off==48);
    assert(!nvme_payload(h,559,2,512,off));
    h[6]=0xffffffffu; assert(!nvme_payload(h,560,2,512,off));
    h[6]=40; h[3]=1; assert(!nvme_payload(h,560,2,512,off));
}
