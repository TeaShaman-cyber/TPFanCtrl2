#include "nvme_thermal.h"
#include <cassert>
#include <cstdint>
#include <vector>
using namespace smart_policy;

static void set16(std::vector<std::uint8_t>& b, unsigned off, unsigned value) {
    b.at(off) = static_cast<std::uint8_t>(value);
    b.at(off+1) = static_cast<std::uint8_t>(value >> 8);
}
int main() {
    std::vector<std::uint8_t> health(512), identify(4096);
    // Reconstruct the relevant fields from the observed Samsung receipt.
    health[0] = 2; set16(health,1,359); set16(identify,266,355); set16(identify,268,358);
    NvmeThermal n{};
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(n.temperature_k==359 && n.warning_k==355 && n.critical_k==358);
    assert(nvme_thermal_state(n,1001,3000,5)==ThermalState::Critical);
    assert(nvme_thermal_state(n,4001,3000,5)==ThermalState::Unknown);
    assert(nvme_thermal_state(n,999,3000,5)==ThermalState::Unknown);
    health[0]=0;set16(health,1,350);
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Warning);
    set16(health,1,349);
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Normal);
    health[0]=2;
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Warning);
    // Optional thresholds must not hide a real thermal warning.
    set16(identify,266,0);set16(identify,268,0);
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Warning);
    health[0]=0;
    assert(decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Unknown);
    set16(identify,266,355);set16(identify,268,358);
    set16(health,1,0);
    assert(!decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(nvme_thermal_state(n,1000,3000,5)==ThermalState::Unknown);
    set16(health,1,350);set16(identify,268,354);
    assert(!decode_nvme_thermal(health.data(),health.size(),identify.data(),identify.size(),1000,n));
    assert(!decode_nvme_thermal(health.data(),511,identify.data(),identify.size(),1000,n));
    assert(!decode_nvme_thermal(nullptr,512,identify.data(),identify.size(),1000,n));
}
