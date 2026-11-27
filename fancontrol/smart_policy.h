#pragma once
// Pure decision logic. The caller owns transport, sensor validation and mode.
#include <cmath>
#include <limits>
#include <vector>

namespace smart_policy {
struct Point {
	double temperature, rpm;
};
struct Step {
	int level;
	double rpm;
};
struct Config {
	std::vector<Point> curve;
	std::vector<Step> calibration;
	double hysteresis;
	unsigned long long rise_ms, fall_ms, max_gap_ms;
	double urgent, recover;
	unsigned long long recovery_ms;
};
struct Sample {
	unsigned long long time_ms;
	double temperature;
	int level; // Observed actual level; 128 denotes firmware.
	bool acknowledged; // Latest requested command is confirmed by readback.
	bool valid; // Independent caller has validated thermal input and freshness.
	bool smart; // False for manual/BIOS mode outside this policy.
};
enum class Kind { Hold, Level, Firmware };
struct Action {
	Kind kind;
	int level;
};

inline bool valid_config(const Config& c) {
	if (c.curve.size() < 2 || c.calibration.size() < 2 ||
	    !std::isfinite(c.hysteresis) || c.hysteresis < 0 ||
	    !std::isfinite(c.urgent) || !std::isfinite(c.recover) ||
	    c.recover <= 0 || c.urgent > 110 || c.recover >= c.urgent ||
	    !c.rise_ms || c.fall_ms < c.rise_ms || !c.max_gap_ms || !c.recovery_ms)
		return false;
	for (std::size_t i = 0; i < c.curve.size(); ++i) {
		const auto& p = c.curve[i];
		if (!std::isfinite(p.temperature) || !std::isfinite(p.rpm) || p.rpm <= 0 ||
		    p.temperature <= 0 || p.temperature > 110 ||
		    (i && (p.temperature <= c.curve[i-1].temperature || p.rpm < c.curve[i-1].rpm)))
			return false;
	}
	for (std::size_t i = 0; i < c.calibration.size(); ++i) {
		const auto& p = c.calibration[i];
		if (p.level < 1 || p.level > 7 || !std::isfinite(p.rpm) || p.rpm <= 0 ||
		    (i && (p.level != c.calibration[i-1].level + 1 ||
		           p.rpm - c.calibration[i-1].rpm <= 2 * c.hysteresis)))
			return false;
	}
	return true;
}

inline double target_rpm(const Config& c, double temperature) {
	if (!valid_config(c) || !std::isfinite(temperature))
		return std::numeric_limits<double>::quiet_NaN();
	if (temperature <= c.curve.front().temperature)
		return c.curve.front().rpm;
	for (std::size_t i = 1; i < c.curve.size(); ++i) {
		const auto& a = c.curve[i-1];
		const auto& b = c.curve[i];
		if (temperature <= b.temperature)
			return a.rpm + (b.rpm-a.rpm) * ((temperature-a.temperature)/(b.temperature-a.temperature));
	}
	return c.curve.back().rpm;
}

class Policy {
public:
	explicit Policy(const Config& c) : config_(c), configured_(valid_config(c)) {}
	void reset() {
		have_time_ = false;
		last_level_ = -1;
		direction_ = 0;
		pending_ = -1;
		firmware_ = false;
		recovering_ = false;
	}
	Action evaluate(const Sample& s) {
		if (!s.smart) {
			reset();
			return hold();
		}
		const bool discontinuity = have_time_ &&
		    (s.time_ms <= last_time_ || s.time_ms-last_time_ > config_.max_gap_ms);
		last_time_ = s.time_ms;
		have_time_ = true;
		if (!configured_ || !s.valid || !std::isfinite(s.temperature) ||
		    s.temperature <= 0 || s.temperature >= config_.urgent || discontinuity)
			return handback(s);
		if (pending_ != -1) {
			if (!s.acknowledged) {
				if (s.time_ms-pending_since_ >= config_.max_gap_ms)
					return handback(s);
				return hold();
			}
			if (s.level != pending_)
				return handback(s);
			pending_ = -1;
			direction_ = 0;
			last_level_ = s.level;
			firmware_ = false;
		}
		if (firmware_ || s.level == 128) {
			firmware_ = true;
			if (s.level != 128 || !s.acknowledged)
				return handback(s);
			if (s.temperature > config_.recover) {
				recovering_ = false;
				return hold();
			}
			if (!recovering_) {
				recovering_ = true;
				since_ = s.time_ms;
				return hold();
			}
			if (s.time_ms-since_ < config_.recovery_ms)
				return hold();
			const double target = target_rpm(config_, s.temperature);
			int level = config_.calibration.back().level;
			for (const auto& step : config_.calibration)
				if (step.rpm >= target) {
					level = step.level;
					break;
				}
			recovering_ = false;
			return request(level, s.time_ms);
		}
		if (!s.acknowledged)
			return handback(s);
		if (s.level < config_.calibration.front().level || s.level > config_.calibration.back().level)
			return handback(s);
		const int index = s.level-config_.calibration.front().level;
		if (s.level != last_level_) {
			direction_ = 0;
			last_level_ = s.level;
		}
		const auto i = static_cast<std::size_t>(index);
		const auto& steps = config_.calibration;
		const double target = target_rpm(config_, s.temperature);
		int direction = 0;
		if (i+1 < steps.size() &&
		    target > steps[i].rpm + (steps[i+1].rpm-steps[i].rpm)/2 + config_.hysteresis)
			direction = 1;
		else if (i && target < steps[i-1].rpm + (steps[i].rpm-steps[i-1].rpm)/2 - config_.hysteresis)
			direction = -1;
		if (!direction || direction != direction_) {
			direction_ = direction;
			since_ = s.time_ms;
			return hold();
		}
		if (s.time_ms-since_ < (direction > 0 ? config_.rise_ms : config_.fall_ms))
			return hold();
		return request(s.level+direction, s.time_ms);
	}
private:
	static Action hold() { return {Kind::Hold, -1}; }
	Action handback(const Sample& s) {
		firmware_ = true;
		recovering_ = false;
		direction_ = 0;
		pending_ = -1;
		last_level_ = -1;
		return s.level == 128 && s.acknowledged ? hold() : Action{Kind::Firmware, 128};
	}
	Action request(int level, unsigned long long time) {
		pending_ = level;
		pending_since_ = time;
		direction_ = 0;
		return {Kind::Level, level};
	}
	Config config_;
	bool configured_, have_time_ = false, firmware_ = false, recovering_ = false;
	int last_level_ = -1, direction_ = 0, pending_ = -1;
	unsigned long long last_time_ = 0, since_ = 0, pending_since_ = 0;
};
} // namespace smart_policy
