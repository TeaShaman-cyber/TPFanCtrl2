#pragma once
#include "ec_tach_quality.h"

namespace research {
// Offline candidate: allow only an isolated single-word observation after a
// fresh, agreeing positive pair at the same confirmed commanded level.
// No relaxed recovery from BIOS, no relaxed stop, no credit across a gap.
class BoundedTachGate {
public:
    void reset(){anchor_=false;}
    bool observe(uint64_t seq,uint64_t now,uint64_t epoch,bool thermal,bool acknowledged,
                 const ec_tach::Assessment& r,int level){
        const bool good=thermal && acknowledged && r.value>0;
        const bool dual=good && r.quality==ec_tach::Quality::Dual;
        const bool single=good && r.quality==ec_tach::Quality::Single &&
            level>1 && level<128 && anchor_ && seq>seq_ && seq-seq_==1 &&
            now>time_ && now-time_<=2000 && epoch==epoch_ && level==level_ &&
            (r.value>rpm_?r.value-rpm_:rpm_-r.value)<=200;
        anchor_=dual;
        if(dual){seq_=seq;time_=now;epoch_=epoch;level_=level;rpm_=r.value;}
        return dual||single;
    }
private:
    bool anchor_=false;
    uint64_t seq_=0,time_=0,epoch_=0;
    int level_=0,rpm_=0;
};
}
