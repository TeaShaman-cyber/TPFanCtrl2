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
// Per-slot observations from the existing pair of EC reads. No new EC transaction.
struct Slot { unsigned a,b; int ready_a,ready_b; };
struct SlotPair {
    uint64_t begin,end;
    Slot slots[12];
};
struct SlotAssessment { int confirmed,disputed; };
inline bool plausible(unsigned v) { return v>0 && v<128; }
inline SlotAssessment qualify_slots(const Slot* slots,unsigned mask) {
    SlotAssessment result{0,0};
    for(unsigned i=0;i<12;++i) {
        if(!(mask & (1u<<i))) continue;
        const auto& s=slots[i];
        const bool a=plausible(s.a), b=plausible(s.b);
        const unsigned hi=a && (!b || s.a>s.b)?s.a:b?s.b:0;
        unsigned confirmed=0;
        if(a && b && s.ready_a==1 && s.ready_b==1) {
            const unsigned lo=s.a<s.b?s.a:s.b;
            // A wide disagreement only establishes the lower bound.
            confirmed=hi-lo<=5?hi:lo;
        }
        const int conservative=static_cast<int>(confirmed>110?110:confirmed);
        if(conservative>result.confirmed) result.confirmed=conservative;
        if(hi>confirmed+5 && static_cast<int>(hi)>result.disputed)
            result.disputed=static_cast<int>(hi);
    }
    if(result.disputed<=result.confirmed) result.disputed=0;
    return result;
}
struct HeatDecision { bool fault,allow_decrease; };
class HeatConfirmation {
public:
    void reset(){pending_=false;last_=0;}
    HeatDecision evaluate(uint64_t now, SlotAssessment s, int urgent, uint64_t max_gap,
                          bool fresh, int level) {
        const bool disputed=s.disputed>s.confirmed;
        const bool hot=disputed && s.disputed>=urgent;
        // A single unconfirmed hot byte gets at most one timely running-fan
        // poll to resolve. Repeated uncertainty, a stopped fan or stale
        // acquisition hands back rather than silently hiding possible heat.
        const bool fault=hot && (!fresh || pending_ || level==0);
        const bool discontinuous=pending_ && (now<=last_ || now-last_>max_gap);
        pending_=hot; last_=now;
        return {fault || (hot && discontinuous), fresh && !disputed};
    }
private:
    bool pending_=false;
    uint64_t last_=0;
};
} // namespace ec_temp
