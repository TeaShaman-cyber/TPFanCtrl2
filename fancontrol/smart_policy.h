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
	unsigned long long hot_rise_ms; // 0 preserves fixed rise dwell
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
enum class Reason {
    None, InvalidConfig, InvalidInput, UrgentTemperature, PollDiscontinuity, PollGapReanchor, LateRise,
    PendingTimeout, PendingMismatch, FirmwareUnconfirmed, UnconfirmedLevel,
    LevelOutsideCalibration, Recovery, Restart, RiseDwell, FallDwell
};
inline const char* reason_name(Reason reason) {
    switch (reason) {
    case Reason::InvalidConfig: return "invalid_config";
    case Reason::InvalidInput: return "invalid_input";
    case Reason::UrgentTemperature: return "urgent_temperature";
    case Reason::PollDiscontinuity: return "poll_discontinuity";
    case Reason::PollGapReanchor: return "poll_gap_reanchor";
    case Reason::LateRise: return "late_rise";
    case Reason::PendingTimeout: return "pending_timeout";
    case Reason::PendingMismatch: return "pending_mismatch";
    case Reason::FirmwareUnconfirmed: return "firmware_unconfirmed";
    case Reason::UnconfirmedLevel: return "unconfirmed_level";
    case Reason::LevelOutsideCalibration: return "level_outside_calibration";
    case Reason::Recovery: return "recovery";
    case Reason::Restart: return "restart";
    case Reason::RiseDwell: return "rise_dwell";
    case Reason::FallDwell: return "fall_dwell";
    default: return "none";
    }
}
struct Action {
    Kind kind;
    int level;
    Reason reason;
    Action(Kind k, int l, Reason r = Reason::None) : kind(k), level(l), reason(r) {}
};

inline bool valid_config(const Config& c) {
	if (c.curve.size() < 2 || c.calibration.size() < 2 ||
	    !std::isfinite(c.hysteresis) || c.hysteresis < 0 ||
	    !std::isfinite(c.urgent) || !std::isfinite(c.recover) ||
	    c.recover <= 0 || c.urgent > 110 || c.recover >= c.urgent ||
	    !c.rise_ms || c.hot_rise_ms > c.rise_ms || c.fall_ms < c.rise_ms || !c.max_gap_ms || !c.recovery_ms)
		return false;
	for (std::size_t i = 0; i < c.curve.size(); ++i) {
		const auto& p = c.curve[i];
		if (!std::isfinite(p.temperature) || !std::isfinite(p.rpm) || p.rpm < 0 ||
		    p.temperature <= 0 || p.temperature > 110 ||
		    (i && (p.temperature <= c.curve[i-1].temperature || p.rpm < c.curve[i-1].rpm)))
			return false;
	}
	for (std::size_t i = 0; i < c.calibration.size(); ++i) {
		const auto& p = c.calibration[i];
		if (p.level < 0 || p.level > 7 || !std::isfinite(p.rpm) ||
		    (p.level == 0 ? p.rpm != 0 : p.rpm <= 0) ||
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
	// A nonzero emergency level is an offline experimental choice, not
	// a certified hardware setpoint. The existing live adapter uses zero.
	explicit Policy(const Config& c, int emergency_level=0) : config_(c),
	    configured_(valid_config(c) && (emergency_level == 0 ||
	        (emergency_level >= c.calibration.back().level && emergency_level <= 7))),
	    emergency_level_(emergency_level) {}
	void reset() {
		have_time_ = false;
		last_gap_ = 0;
		late_up_ = false;
		fault_ = false;
		fault_lost_ = false;
		last_level_ = -1;
		direction_ = 0;
		pending_ = -1;
		firmware_ = false;
		recovering_ = false;
	}
	unsigned long long last_gap() const { return last_gap_; }
	Action evaluate(const Sample& s, bool allow_decrease = true) {
		if (!s.smart) {
			reset();
			return hold();
		}
		const auto elapsed = have_time_ && s.time_ms > last_time_ ? s.time_ms-last_time_ : 0;
		const bool nonmonotonic = have_time_ && s.time_ms <= last_time_;
		const bool late = have_time_ && elapsed > config_.max_gap_ms;
		last_time_ = s.time_ms;
		last_gap_ = elapsed;
		have_time_ = true;
		if (!configured_) return handback(s, Reason::InvalidConfig);
		const bool thermal_valid = s.valid && std::isfinite(s.temperature) && s.temperature > 0;
		const auto thermal_reason = !thermal_valid ? Reason::InvalidInput :
		    s.temperature >= config_.urgent ? Reason::UrgentTemperature : Reason::None;
		if (emergency_level_ && !fault_lost_ && (fault_ || thermal_reason != Reason::None))
			return host_fault(s, thermal_reason, late, nonmonotonic, allow_decrease);
		if (thermal_reason != Reason::None) return handback(s, thermal_reason);
		if (nonmonotonic) return handback(s, Reason::PollDiscontinuity);
		if (pending_ != -1) {
			if (!s.acknowledged) {
				if (s.time_ms-pending_since_ >= config_.max_gap_ms)
					return handback(s, Reason::PendingTimeout);
				return hold();
			}
			if (s.level != pending_)
				return handback(s, Reason::PendingMismatch);
			pending_ = -1;
			direction_ = 0;
			last_level_ = s.level;
			firmware_ = false;
			fault_lost_ = false;
			late_up_ = false;
			if (late) return {Kind::Hold, -1, Reason::PollGapReanchor};
		}
		if (firmware_ || s.level == 128) {
			firmware_ = true;
			if (s.level != 128 || !s.acknowledged)
				return handback(s, Reason::FirmwareUnconfirmed);
			if (late) {
				recovering_ = false;
				return {Kind::Hold, -1, Reason::PollGapReanchor};
			}
			if (!allow_decrease || s.temperature > config_.recover) {
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
			// Recover to a running step first; stopping needs its own dwell.
			if (level == 0) level = 1;
			recovering_ = false;
			return request(level, s.time_ms, Reason::Recovery);
		}
		if (!s.acknowledged)
			return handback(s, Reason::UnconfirmedLevel);
		if (s.level < config_.calibration.front().level || s.level > config_.calibration.back().level)
			return handback(s, Reason::LevelOutsideCalibration);
		// A stopped fan takes time to spin up. Restart at the recovery
		// threshold without waiting for the ordinary rise dwell.
		if (s.level == 0 && (late || s.temperature >= config_.recover))
			return request(1, s.time_ms, Reason::Restart);
		const int index = s.level-config_.calibration.front().level;
		if (s.level != last_level_) {
			if (late && last_level_ != -1)
				return handback(s, Reason::PollDiscontinuity);
			late_up_ = false;
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
		if (direction < 0 && s.level == 1 && steps.front().level == 0 &&
		    s.temperature >= config_.recover)
			direction = 0;
		// A late but valid observation is not a transport or thermal failure.
		// Do not credit unobserved time in either direction. Two late
		// observations of upward demand, without an intervening reversal or
		// level change, may advance one confirmed adjacent step. This prevents
		// frequent timing gaps from indefinitely starving cooling.
		// Do not carry fall dwell through a feedback-quality veto.
		if (direction < 0 && !allow_decrease) direction = 0;
		if (direction <= 0) late_up_ = false;
		if (late) {
			direction_ = 0;
			rise_credit_ = 0;
			since_ = s.time_ms;
			if (direction > 0) {
				if (late_up_) return request(s.level+1,s.time_ms,Reason::LateRise);
				late_up_ = true;
			}
			return {Kind::Hold, -1, Reason::PollGapReanchor};
		}
		// Accumulate only consecutive intervals of upward demand. Use the
		// slower endpoint rate so a single hot reading cannot credit the past.
		double rate = 1.0 / static_cast<double>(config_.rise_ms);
		if (config_.hot_rise_ms && s.temperature > config_.recover) {
			const double fraction = (s.temperature-config_.recover)/(config_.urgent-config_.recover);
			rate += fraction*(1.0/static_cast<double>(config_.hot_rise_ms)-rate);
		}
		if (!direction || direction != direction_) {
			direction_ = direction;
			rise_credit_=0;
			last_rate_=rate;
			since_ = s.time_ms;
			return hold();
		}
		if (direction > 0 && config_.hot_rise_ms) {
			rise_credit_ += static_cast<double>(elapsed)*(rate < last_rate_ ? rate : last_rate_);
			last_rate_=rate;
			if (rise_credit_ < 1.0-1e-9) return hold();
			return request(s.level+1,s.time_ms, Reason::RiseDwell);
		}
		// Stopping is more expensive than ordinary downward steps.
		const auto dwell = direction < 0 && s.level == 1 && steps.front().level == 0 && config_.fall_ms < 30000
		    ? 30000ULL : (direction > 0 ? config_.rise_ms : config_.fall_ms);
		if (s.time_ms-since_ < dwell)
			return hold();
		return request(s.level+direction, s.time_ms, direction > 0 ? Reason::RiseDwell : Reason::FallDwell);
	}
private:
	static Action hold() { return {Kind::Hold, -1}; }
	Action host_fault(const Sample& s, Reason thermal_reason, bool late, bool nonmonotonic, bool allow_decrease) {
		if (!fault_) {
			fault_ = true;
			firmware_ = false;
			recovering_ = false;
			pending_ = -1;
			direction_ = 0;
			late_up_ = false;
			rise_credit_ = 0;
		}
		if (nonmonotonic) return handback(s, Reason::PollDiscontinuity);
		if (pending_ != -1) {
			if (!s.acknowledged) {
				recovering_ = false;
				if (s.time_ms-pending_since_ >= config_.max_gap_ms)
					return handback(s, Reason::PendingTimeout);
				return hold();
			}
			if (s.level != pending_) return handback(s, Reason::PendingMismatch);
			pending_ = -1;
		}
		// Never intentionally reduce cooling in the fault state, even if a
		// higher regulated level was already selected. A control-byte
		// acknowledgement is not proof of physical cooling effectiveness.
		if (!s.acknowledged || s.level < emergency_level_ || s.level > 7) {
			recovering_ = false;
			return request(emergency_level_,s.time_ms,
			    thermal_reason == Reason::None ? Reason::UnconfirmedLevel : thermal_reason);
		}
		if (!allow_decrease || thermal_reason != Reason::None || s.temperature > config_.recover || late) {
			recovering_ = false;
			return hold();
		}
		if (!recovering_) {
			recovering_ = true;
			since_ = s.time_ms;
			return hold();
		}
		if (s.time_ms-since_ < config_.recovery_ms) return hold();
		fault_ = false;
		recovering_ = false;
		direction_ = 0;
		last_level_ = s.level;
		// Return to the calibrated domain only after guarded recovery.
		if (s.level > config_.calibration.back().level)
			return request(config_.calibration.back().level,s.time_ms,Reason::Recovery);
		return hold();
	}
	Action handback(const Sample& s, Reason reason) {
		if (fault_) fault_lost_ = true;
		fault_ = false;
		firmware_ = true;
		late_up_ = false;
		recovering_ = false;
		direction_ = 0;
		pending_ = -1;
		last_level_ = -1;
		return s.level == 128 && s.acknowledged ? hold() : Action{Kind::Firmware, 128, reason};
	}
	Action request(int level, unsigned long long time, Reason reason) {
		pending_ = level;
		late_up_ = false;
		pending_since_ = time;
		direction_ = 0;
		return {Kind::Level, level, reason};
	}
	Config config_;
	bool configured_;
	int emergency_level_;
	bool fault_ = false, fault_lost_ = false;
	bool have_time_ = false, firmware_ = false, recovering_ = false, late_up_ = false;
	double rise_credit_=0, last_rate_=0;
	int last_level_ = -1, direction_ = 0, pending_ = -1;
	unsigned long long last_gap_ = 0, last_time_ = 0, since_ = 0, pending_since_ = 0;
};
} // namespace smart_policy
