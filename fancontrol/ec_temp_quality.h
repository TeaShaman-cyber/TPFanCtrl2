#pragma once
#include <cstdint>

namespace ec_temp {
// Times bound acquisition, not the physical sensor's conversion time.
struct Frame {
    uint64_t begin, end;
    unsigned a, b;
    int ready_a, ready_b;
};
struct Assessment {
    int value, delta; // -1: no usable value / no comparable pair
    bool fresh, allow_decrease;
};
inline Assessment assess(const Frame& f, uint64_t now, bool current_epoch,
                         bool poll_ok, uint64_t max_age) {
    const bool a = f.ready_a == 1 && f.a > 0 && f.a < 128;
    const bool b = f.ready_b == 1 && f.b > 0 && f.b < 128;
    const int value = a && (!b || f.a > f.b) ? int(f.a) : b ? int(f.b) : -1;
    const int delta = a && b ? (f.a > f.b ? int(f.a-f.b) : int(f.b-f.a)) : -1;
    const bool fresh = poll_ok && current_epoch && max_age > 0 &&
        f.begin > 0 && f.begin <= f.end && f.end <= now &&
        now-f.begin <= max_age;
    return {value, delta, fresh, fresh && a && b && delta <= 5};
}
} // namespace ec_temp
