#include "smart_policy.h"
#include <cassert>
#include <limits>
using namespace smart_policy;

static Config config() {
    // Synthetic policy inputs, deliberately not an L14 deployment profile.
    return Config{{{40, 2000}, {80, 5000}}, {{1, 2000}, {2, 3000}, {3, 4000}, {4, 5000}},
                  100, 3000, 10000, 2000, 85, 70, 5000};
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
    assert(gap.evaluate(sample(2001,60)).kind==Kind::Firmware);
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
}
