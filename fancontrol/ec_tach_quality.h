#pragma once
#include <cstdint>

namespace ec_tach {
struct Word { unsigned rpm; int low_ready, high_ready; };
struct Frame { uint64_t begin, end; Word a,b; };
enum class Quality { Unknown, Single, Dual, Disagree, Stale };
struct Assessment { int value, delta; char source; Quality quality; };
inline bool valid(const Word& w) {
    return w.rpm <= 8191 && w.low_ready == 1 && w.high_ready == 1;
}
inline const char* name(Quality q) {
    switch(q) {
    case Quality::Single: return "single";
    case Quality::Dual: return "dual";
    case Quality::Disagree: return "disagree";
    case Quality::Stale: return "stale";
    default: return "unknown";
    }
}
inline Assessment assess(const Frame& f, uint64_t now, bool epoch, bool poll_ok, uint64_t budget) {
    const bool a=valid(f.a), b=valid(f.b);
    const int delta=a && b ? int(f.a.rpm>f.b.rpm ? f.a.rpm-f.b.rpm : f.b.rpm-f.a.rpm) : -1;
    // Aged acquisition is not a fresh measurement even if both bytes were ready.
    if (!poll_ok || !epoch || !budget || !f.begin || f.begin>f.end ||
        f.end>now || now-f.begin>budget)
        return {-1,delta,'-',Quality::Stale};
    if (!a && !b) return {-1,-1,'-',Quality::Unknown};
    // Zero vs running is a state conflict, even inside the RPM tolerance.
    if (a && b && (delta>200 || (f.a.rpm==0)!=(f.b.rpm==0)))
        return {-1,delta,'-',Quality::Disagree};
    // Select an entire observed word, never splice bytes from different reads.
    return {int(b?f.b.rpm:f.a.rpm),delta,b?'B':'A',a&&b?Quality::Dual:Quality::Single};
}
} // namespace ec_tach
