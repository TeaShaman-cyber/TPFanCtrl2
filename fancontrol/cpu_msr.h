#pragma once
#include <cstdint>
#include <cmath>
namespace cpu_msr {
// Intel digital thermal sensor: target minus distance, only if valid.
inline bool temperature(uint64_t target, uint64_t status, int& out) {
    const int tj = static_cast<int>((target >> 16) & 255);
    const int delta = static_cast<int>((status >> 16) & 127);
    if (tj < 70 || tj > 125 || !(status & (uint64_t(1) << 31)) || tj <= delta)
        return false;
    out = tj - delta;
    return true;
}
class Energy {
public:
    void reset() { valid_ = false; }
    bool update(uint64_t ms, uint32_t count, unsigned exponent, double& out) {
        const bool usable = valid_ && exponent == exponent_ && ms > time_ && ms-time_ <= 2500;
        const double watts = usable ? std::ldexp(static_cast<double>(uint32_t(count-count_)), -static_cast<int>(exponent))*1000.0/static_cast<double>(ms-time_) : 0;
        valid_ = exponent <= 31;
        time_ = ms; count_ = count; exponent_ = exponent;
        // Conservative research bound; a reset may still resemble a plausible delta.
        if (!usable || !valid_ || watts > 200.0) return false;
        out = watts;
        return true;
    }
private:
    bool valid_ = false;
    uint64_t time_ = 0;
    uint32_t count_ = 0;
    unsigned exponent_ = 0;
};
struct Frame {
    bool valid = false, power_valid = false;
    int package = 0, hottest = 0;
    double watts = 0;
    uint64_t time_ms = 0;
};
// Never let CPU telemetry hide a hotter valid platform observation.
inline bool shadow_temperature(const Frame& f, uint64_t now, int ec, int& out) {
    if (!f.valid || now < f.time_ms || now-f.time_ms > 500 ||
        ec <= 0 || ec > 110 || f.package <= 0 || f.package > 125 ||
        f.hottest <= 0 || f.hottest > 125) return false;
    out = ec;
    if (f.package > out) out = f.package;
    if (f.hottest > out) out = f.hottest;
    return true;
}
}
