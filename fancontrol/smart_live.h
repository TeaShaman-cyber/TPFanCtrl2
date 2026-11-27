#pragma once
#include "smart_shadow.h"
#include "cpu_msr.h"
namespace smart_policy {
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
                    bool current_epoch,bool acknowledged,bool active) {
        int temperature=0;
        const bool valid=current_epoch && cpu_msr::shadow_temperature(cpu,now,ec,temperature);
        return policy_.evaluate({now,static_cast<double>(temperature),level,acknowledged,
            enabled_ && valid,enabled_ && active});
    }
private:
    Config config_{};
    Policy policy_{config_};
    bool seen_=false,enabled_=false;
};
}
