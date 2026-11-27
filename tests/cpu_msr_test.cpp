#include "cpu_msr.h"
#include <cassert>
#include <cmath>
using namespace cpu_msr;
int main(){
 int t=-1;
 assert(temperature(100u<<16,0x80000000u|(40u<<16),t)&&t==60);
 assert(!temperature(100u<<16,40u<<16,t));
 assert(!temperature(0,0x80000000u,t));
 assert(!temperature(100u<<16,0x80000000u|(127u<<16),t));
 assert(temperature(100u<<16,0x80000000u,t)&&t==100);
 Frame f{};
 int selected=0;
 assert(!shadow_temperature(f,1000,60,selected));
 f.valid=true; f.time_ms=1000; f.package=65; f.hottest=72;
 assert(shadow_temperature(f,1250,60,selected)&&selected==72);
 assert(shadow_temperature(f,1250,80,selected)&&selected==80);
 assert(!shadow_temperature(f,1501,60,selected));
 assert(!shadow_temperature(f,999,60,selected));
 assert(shadow_temperature(f,1250,0,selected)&&selected==72);
 assert(shadow_temperature(f,1250,128,selected)&&selected==72);
 f.hottest=0;
 assert(!shadow_temperature(f,1250,60,selected));
 Energy power;
 double w=-1;
 assert(!power.update(1000,0xfffffff0u,16,w));
 assert(power.update(2000,0x0000fff0u,16,w)&&std::abs(w-1)<1e-9);
 assert(!power.update(2000,0x00010000u,16,w));
 assert(!power.update(5000,0x00010000u,16,w));
 assert(!power.update(6000,0x00010000u,17,w));
 assert(power.update(7000,0x00030000u,17,w)&&std::abs(w-1)<1e-9);
 assert(!power.update(8000,0x00000000u,17,w)); // implausible reset
 power.reset();
 assert(!power.update(9000,123u,16,w));
 assert(power.update(10000,123u,16,w)&&w==0);
}
