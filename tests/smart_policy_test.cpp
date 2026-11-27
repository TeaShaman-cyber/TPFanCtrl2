#include "smart_policy.h"
#include <cassert>
#include <limits>
using namespace smart_policy;

static Config config() {
    // Synthetic policy inputs, deliberately not an L14 deployment profile.
    return Config{{{40, 2000}, {80, 5000}}, {{1, 2000}, {2, 3000}, {3, 4000}, {4, 5000}},
                  100, 3000, 10000, 2000, 85, 70, 5000, 0};
}
static Sample sample(unsigned long long t, double temp, int level = 1,
                     bool ack = true, bool valid = true, bool smart = true) {
    return Sample{t, temp, level, ack, valid, smart};
}
int main() {
    const Config cfg = config();
    assert(target_rpm(cfg, 60) == 3500);
    assert(target_rpm(cfg, 20) == 2000);
    assert(target_rpm(cfg, 90) == 5000);
    Policy p(cfg);
    assert(p.evaluate(sample(0, 40)).kind == Kind::Hold);
    assert(p.evaluate(sample(1000, 79)).kind == Kind::Hold);
    assert(p.evaluate(sample(2000, 40)).kind == Kind::Hold);
    assert(p.evaluate(sample(3000, 79)).kind == Kind::Hold);
    assert(p.evaluate(sample(4000, 79)).kind == Kind::Hold);
    assert(p.evaluate(sample(5000, 79)).kind == Kind::Hold);
    auto a = p.evaluate(sample(6000, 79));
    assert(a.kind == Kind::Level && a.level == 2);
    assert(p.evaluate(sample(7000, 79, 1, false)).kind == Kind::Hold);
    assert(p.evaluate(sample(8000, 79, 2)).kind == Kind::Hold);
    assert(p.evaluate(sample(9000, 79, 2)).kind == Kind::Hold);
    assert(p.evaluate(sample(10000, 79, 2)).kind == Kind::Hold);
    a = p.evaluate(sample(11000, 79, 2));
    assert(a.kind == Kind::Level && a.level == 3);
    assert(p.evaluate(sample(12000, 85, 2, false)).kind == Kind::Firmware);
    assert(p.evaluate(sample(13000, 72, 128)).kind == Kind::Hold);
    assert(p.evaluate(sample(14000, 60, 128)).kind == Kind::Hold);
    assert(p.evaluate(sample(15000, 60, 128)).kind == Kind::Hold);
    assert(p.evaluate(sample(16000, 60, 128)).kind == Kind::Hold);
    assert(p.evaluate(sample(17000, 60, 128)).kind == Kind::Hold);
    assert(p.evaluate(sample(18000, 60, 128)).kind == Kind::Hold);
    a = p.evaluate(sample(19000, 60, 128));
    assert(a.kind == Kind::Level && a.level == 3);
    Policy down(cfg);
    assert(down.evaluate(sample(0, 40, 4)).kind == Kind::Hold);
    for (unsigned t=1000;t<10000;t+=1000)
        assert(down.evaluate(sample(t, 40, 4)).kind == Kind::Hold);
    a=down.evaluate(sample(10000,40,4));
    assert(a.kind==Kind::Level && a.level==3);
    Policy fail(cfg);
    assert(fail.evaluate(sample(0,60)).kind==Kind::Hold);
    assert(fail.evaluate(sample(1000,60,1,true,false)).kind==Kind::Firmware);
    assert(fail.evaluate(sample(2000,60,128,true,true,false)).kind==Kind::Hold);
    assert(fail.evaluate(sample(3000,60,1)).kind==Kind::Hold);
    assert(fail.evaluate(sample(3000,60,1)).kind==Kind::Firmware);
    Policy gap(cfg);
    gap.evaluate(sample(0,60));
    // Isolated bounded late poll with confirmed running fan: reanchor, no command.
    a=gap.evaluate(sample(2640,69));
    assert(a.kind==Kind::Hold && a.reason==Reason::PollGapReanchor);
    assert(gap.evaluate(sample(3640,69)).kind==Kind::Hold);
    assert(gap.evaluate(sample(6468,77)).kind==Kind::Firmware); // repeated gap before healthy window
    Policy drift(cfg);
    drift.evaluate(sample(0,60));
    assert(drift.evaluate(sample(2640,60,2)).kind==Kind::Firmware);
    Policy boundary(cfg);
    boundary.evaluate(sample(0,40));
    assert(boundary.evaluate(sample(4000,40)).reason==Reason::PollGapReanchor);
    Policy huge_gap(cfg);
    huge_gap.evaluate(sample(0,60));
    assert(huge_gap.evaluate(sample(4001,60)).kind==Kind::Firmware);
    Policy later(cfg);
    later.evaluate(sample(0,60));
    assert(later.evaluate(sample(2828,77)).kind==Kind::Hold);
    for(unsigned t=3828;t<=7828;t+=1000)
        assert(later.evaluate(sample(t,40)).kind==Kind::Hold);
    assert(later.evaluate(sample(10468,69)).kind==Kind::Hold);
    Policy no_credit(cfg);
    no_credit.evaluate(sample(0,79));
    no_credit.evaluate(sample(1000,79));
    assert(no_credit.evaluate(sample(3640,79)).kind==Kind::Hold);
    assert(no_credit.evaluate(sample(4640,79)).kind==Kind::Hold);
    assert(no_credit.evaluate(sample(5640,79)).kind==Kind::Hold);
    assert(no_credit.evaluate(sample(6640,79)).kind==Kind::Hold);
    assert(no_credit.evaluate(sample(7640,79)).kind==Kind::Level);
    Policy down_gap(cfg);
    for(unsigned t=0;t<=8000;t+=1000)
        assert(down_gap.evaluate(sample(t,40,4)).kind==Kind::Hold);
    assert(down_gap.evaluate(sample(10640,40,4)).reason==Reason::PollGapReanchor);
    for(unsigned t=11640;t<21640;t+=1000)
        assert(down_gap.evaluate(sample(t,40,4)).kind==Kind::Hold);
    assert(down_gap.evaluate(sample(21640,40,4)).kind==Kind::Level);
    Policy gap_hot(cfg);
    gap_hot.evaluate(sample(0,60));
    assert(gap_hot.evaluate(sample(2640,85)).reason==Reason::UrgentTemperature);
    Policy gap_invalid(cfg);
    gap_invalid.evaluate(sample(0,60));
    assert(gap_invalid.evaluate(sample(2640,60,1,true,false)).reason==Reason::InvalidInput);
    Policy gap_unconfirmed(cfg);
    gap_unconfirmed.evaluate(sample(0,60));
    assert(gap_unconfirmed.evaluate(sample(2640,60,1,false)).kind==Kind::Firmware);
    Policy gap_pending(cfg);
    for(unsigned t=0;t<3000;t+=1000)gap_pending.evaluate(sample(t,79));
    assert(gap_pending.evaluate(sample(3000,79)).kind==Kind::Level);
    assert(gap_pending.evaluate(sample(5640,79,1,false)).kind==Kind::Firmware);
    Policy gap_bios(cfg);
    gap_bios.evaluate(sample(0,60,128));
    gap_bios.evaluate(sample(1000,60,128));
    assert(gap_bios.evaluate(sample(3640,60,128)).kind==Kind::Hold);
    for(unsigned t=4640;t<9640;t+=1000)
        assert(gap_bios.evaluate(sample(t,60,128)).kind==Kind::Hold);
    assert(gap_bios.evaluate(sample(9640,60,128)).kind==Kind::Level);
    Policy nan(cfg);
    assert(nan.evaluate(sample(0,std::numeric_limits<double>::quiet_NaN())).kind==Kind::Firmware);
    Config bad=cfg; bad.calibration[1].level=3;
    Policy invalid(bad);
    assert(invalid.evaluate(sample(0,60)).kind==Kind::Firmware);
    bad=cfg;bad.calibration[1].rpm=2100;
    Policy overlap(bad);
    assert(overlap.evaluate(sample(0,60)).kind==Kind::Firmware);
    Policy invalid_level(cfg);
    assert(invalid_level.evaluate(sample(0,60,std::numeric_limits<int>::min())).kind==Kind::Firmware);
    Policy timeout(cfg);
    timeout.evaluate(sample(0,79));
    timeout.evaluate(sample(1000,79));
    timeout.evaluate(sample(2000,79));
    assert(timeout.evaluate(sample(3000,79)).kind==Kind::Level);
    assert(timeout.evaluate(sample(4000,79,1,false)).kind==Kind::Hold);
    assert(timeout.evaluate(sample(5000,79,1,false)).kind==Kind::Firmware);
    Policy wrong_ack(cfg);
    wrong_ack.evaluate(sample(0,79));
    wrong_ack.evaluate(sample(1000,79));
    wrong_ack.evaluate(sample(2000,79));
    assert(wrong_ack.evaluate(sample(3000,79)).kind==Kind::Level);
    assert(wrong_ack.evaluate(sample(4000,79,1)).kind==Kind::Firmware);
    Policy interrupt(cfg);
    assert(interrupt.evaluate(sample(0,85)).kind==Kind::Firmware);
    interrupt.evaluate(sample(1000,60,128));
    interrupt.evaluate(sample(2000,60,128));
    interrupt.evaluate(sample(3000,71,128));
    for(unsigned t=4000;t<9000;t+=1000)
        assert(interrupt.evaluate(sample(t,60,128)).kind==Kind::Hold);
    assert(interrupt.evaluate(sample(9000,60,128)).kind==Kind::Level);
    Policy manual(cfg);
    manual.evaluate(sample(0,79));
    manual.evaluate(sample(1000,79));
    assert(manual.evaluate(sample(2000,100,1,false,false,false)).kind==Kind::Hold);
    assert(manual.evaluate(sample(3000,79)).kind==Kind::Hold);
    assert(manual.evaluate(sample(4000,79)).kind==Kind::Hold);
    assert(manual.evaluate(sample(5000,79)).kind==Kind::Hold);
    assert(manual.evaluate(sample(6000,79)).kind==Kind::Level);
    // Level zero is a stopped fan, not an extrapolated running RPM.
    Config passive = config();
    passive.calibration.insert(passive.calibration.begin(), Step{0,0});
    passive.curve = {{55,0},{65,2000},{80,5000}};
    assert(valid_config(passive));
    assert(target_rpm(passive,45)==0);
    Policy stop(passive);
    for(unsigned t=0;t<30000;t+=1000)
        assert(stop.evaluate(sample(t,45,1)).kind==Kind::Hold);
    a=stop.evaluate(sample(30000,45,1));
    assert(a.kind==Kind::Level && a.level==0);
    assert(stop.evaluate(sample(31000,45,0)).kind==Kind::Hold);
    // At the recovery threshold, restart immediately, not after a dwell.
    a=stop.evaluate(sample(32000,70,0));
    assert(a.kind==Kind::Level && a.level==1);
    Policy gap_zero(passive);
    gap_zero.evaluate(sample(0,45,0));
    assert(gap_zero.evaluate(sample(2640,45,0)).kind==Kind::Firmware);
    Policy urgent(passive);
    assert(urgent.evaluate(sample(0,85,0)).kind==Kind::Firmware);
    Config bad_zero=passive;bad_zero.calibration[0].rpm=10;
    assert(!valid_config(bad_zero));
    bad_zero=passive;bad_zero.calibration[1].rpm=0;
    assert(!valid_config(bad_zero));
    bad_zero=passive;bad_zero.curve[0].rpm=-1;
    assert(!valid_config(bad_zero));
    Policy resumed(passive);
    assert(resumed.evaluate(sample(0,45,128)).kind==Kind::Hold);
    for(unsigned t=1000;t<5000;t+=1000)
        assert(resumed.evaluate(sample(t,45,128)).kind==Kind::Hold);
    a=resumed.evaluate(sample(5000,45,128));
    assert(a.kind==Kind::Level && a.level==1);
    Config permissive=passive;
    permissive.curve={{75,0},{80,5000}};
    Policy keep_running(permissive);
    for(unsigned t=0;t<=40000;t+=1000)
        assert(keep_running.evaluate(sample(t,72,1)).kind==Kind::Hold);
    Config adaptive=cfg;
    adaptive.hot_rise_ms=1000;
    adaptive.rise_ms=6000;
    assert(valid_config(adaptive));
    Policy spike(adaptive);
    assert(spike.evaluate(sample(0,70)).kind==Kind::Hold);
    assert(spike.evaluate(sample(1000,84)).kind==Kind::Hold);
    assert(spike.evaluate(sample(2000,40)).kind==Kind::Hold);
    Policy hot(adaptive);
    assert(hot.evaluate(sample(0,84)).kind==Kind::Hold);
    assert(hot.evaluate(sample(1000,84)).kind==Kind::Hold);
    a=hot.evaluate(sample(2000,84));
    assert(a.kind==Kind::Level&&a.level==2);
    assert(hot.evaluate(sample(2500,84,2)).kind==Kind::Hold);
    assert(hot.evaluate(sample(3000,84,2)).kind==Kind::Hold);
    assert(hot.evaluate(sample(3500,85,2)).kind==Kind::Firmware);
    Policy adaptive_gap(adaptive);
    assert(adaptive_gap.evaluate(sample(0,84)).kind==Kind::Hold);
    assert(adaptive_gap.evaluate(sample(1000,84)).kind==Kind::Hold);
    assert(adaptive_gap.evaluate(sample(3640,84)).reason==Reason::PollGapReanchor);
    assert(adaptive_gap.evaluate(sample(4640,84)).kind==Kind::Hold);
    assert(adaptive_gap.evaluate(sample(5640,84)).kind==Kind::Hold);
    assert(adaptive_gap.evaluate(sample(6640,84)).kind==Kind::Level);
    Policy mild(adaptive);
    for(unsigned t=0;t<6000;t+=1000)
        assert(mild.evaluate(sample(t,65)).kind==Kind::Hold);
    assert(mild.evaluate(sample(6000,65)).kind==Kind::Level);
    adaptive.hot_rise_ms=7000;assert(!valid_config(adaptive));
}
