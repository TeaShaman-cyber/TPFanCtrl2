#pragma once
// Counterfactual policy replay. No actuator or physical acknowledgement.
#include "smart_policy.h"
#include <locale>
#include <sstream>
#include <string>

namespace smart_policy {
inline bool parse_shadow_config(const std::string& line, Config& result) {
	std::istringstream input(line.substr(0, line.find("//")));
	input.imbue(std::locale::classic());
	Config c{};
	long long rise, fall, gap, recovery;
	char separator;
	if (!(input >> c.hysteresis >> rise >> fall >> gap >> c.urgent >> c.recover >> recovery) || rise <= 0 || fall <= 0 || gap <= 0 || recovery <= 0)
		return false;
	input >> std::ws;
	if (input.peek() != ';') {
		long long hot;
		if (!(input >> hot) || hot <= 0 || hot > rise) return false;
		c.hot_rise_ms=static_cast<unsigned long long>(hot);
	}
	if (!(input >> separator) || separator != ';') return false;
	c.rise_ms = static_cast<unsigned long long>(rise);
	c.fall_ms = static_cast<unsigned long long>(fall);
	c.max_gap_ms = static_cast<unsigned long long>(gap);
	c.recovery_ms = static_cast<unsigned long long>(recovery);
	for (;;) {
		input >> std::ws;
		if (input.peek() == ';') {
			input.get();
			break;
		}
		Point point{};
		if (c.curve.size() >= 32 || !(input >> point.temperature >> point.rpm))
			return false;
		c.curve.push_back(point);
	}
	for (;;) {
		input >> std::ws;
		if (input.eof())
			break;
		Step step{};
		if (c.calibration.size() >= 8 || !(input >> step.level >> step.rpm))
			return false;
		c.calibration.push_back(step);
	}
	if (!valid_config(c) ||
	    c.curve.front().rpm < c.calibration.front().rpm ||
	    c.curve.back().rpm > c.calibration.back().rpm)
		return false;
	result = c;
	return true;
}

struct ShadowResult {
	Action action;
	int projected;
};

class Shadow {
public:
	bool configure(const std::string& line) {
		if (seen_) {
			enabled_ = false;
			reset();
			return false;
		}
		seen_ = true;
		Config c{};
		if (!parse_shadow_config(line, c))
			return false;
		config_ = c;
		policy_ = Policy(config_);
		enabled_ = true;
		reset();
		return true;
	}
	bool enabled() const { return enabled_; }
	void reset() {
		policy_.reset();
		projected_ = -1;
	}
	ShadowResult observe(unsigned long long time, double temperature, int observed, bool valid) {
		if (!enabled_)
			return {{Kind::Hold, -1}, -1};
		if (projected_ == -1) {
			projected_ = 128;
			for (const auto& step : config_.calibration)
				if (observed == step.level)
					projected_ = observed;
		}
		const Action action = policy_.evaluate({time, temperature, projected_, true, valid, true});
		if (action.kind != Kind::Hold)
			projected_ = action.level;
		// Deliberate simulation: a requested level is applied to the virtual
		// state only, and acknowledged on the next observation. Never use this
		// class for live command acknowledgement.
		return {action, projected_};
	}
private:
	Config config_{};
	Policy policy_{config_};
	bool seen_ = false, enabled_ = false;
	int projected_ = -1;
};
} // namespace smart_policy
