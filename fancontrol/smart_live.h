#pragma once
#include "smart_shadow.h"
#include "cpu_msr.h"
namespace smart_policy {
// Snapshot of the exact inputs consumed by the decision, not a second poll.
struct DecisionInput {
    uint64_t now, cpu_time, gap;
    int ec, package, hottest, selected, level;
    bool cpu_valid, epoch, valid, acknowledged;
};
// Worker writes its timestamps before posting WM__NEWDATA; dialog joins
// the worker before reading them. Zero dispatch means no verified poll.
struct PollTiming {
    uint64_t dispatch, worker, ec_done, done, handler;
    bool ordered(uint64_t previous, uint64_t now) const {
        return dispatch && previous <= dispatch && dispatch <= worker &&
            worker <= ec_done && ec_done <= done && done <= handler && handler <= now;
    }
};
// Actual readback, not a simulated acknowledgement. Caller retains EC ownership.
class Live {
public:
    bool configure(const std::string& line) {
        if (seen_) {enabled_=false;reset();return false;}
        seen_=true;
        Config c{};
        if(!parse_shadow_config(line,c))return false;
        config_=c;policy_=Policy(c);enabled_=true;
        return true;
    }
    bool enabled() const {return enabled_;}
    void reset(){policy_.reset();}
    Action evaluate(uint64_t now,const cpu_msr::Frame& cpu,int ec,int level,
                    bool current_epoch,bool acknowledged,bool active, DecisionInput* input=nullptr) {
        int temperature=0;
        const bool valid=current_epoch && cpu_msr::shadow_temperature(cpu,now,ec,temperature);
        const auto action=policy_.evaluate({now,static_cast<double>(temperature),level,acknowledged,
            enabled_ && valid,enabled_ && active});
        if(input) *input={now,cpu.time_ms,policy_.last_gap(),ec,cpu.package,cpu.hottest,
            temperature,level,cpu.valid,current_epoch,enabled_ && valid,acknowledged};
        return action;
    }
private:
    Config config_{};
    Policy policy_{config_};
    bool seen_=false,enabled_=false;
};
}
