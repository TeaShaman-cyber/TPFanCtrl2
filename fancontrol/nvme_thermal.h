#pragma once
// Pure decode/classify of NVMe health and Identify Controller responses.
// Caller must provide a fresh successful read from the same physical device.
// No hardware actions; Unknown must not be interpreted as thermal headroom.
#include <cstddef>
#include <cstdint>

namespace smart_policy {
enum class ThermalState { Unknown, Normal, Warning, Critical };
struct NvmeThermal {
	std::uint16_t temperature_k, warning_k, critical_k;
	std::uint8_t critical_warning;
	unsigned long long sampled_ms;
	bool valid;
};

inline std::uint16_t nvme_le16(const std::uint8_t* p) {
	return static_cast<std::uint16_t>(p[0] | (static_cast<unsigned>(p[1]) << 8));
}

inline bool decode_nvme_thermal(const std::uint8_t* health, std::size_t health_size,
    const std::uint8_t* identify, std::size_t identify_size,
    unsigned long long sampled_ms, NvmeThermal& result) {
	result = NvmeThermal{};
	if (!health || health_size < 512 || (identify && identify_size < 4096))
		return false;
	const auto temperature = nvme_le16(health+1);
	const std::uint16_t warning = identify ? nvme_le16(identify+266) : 0;
	const std::uint16_t critical = identify ? nvme_le16(identify+268) : 0;
	// Conservative plausibility bounds, not model-specific safety limits.
	if (temperature < 200 || temperature > 450 ||
	    (warning && (warning < 274 || warning > 450)) ||
	    (critical && (critical < 274 || critical > 450)) ||
	    (warning && critical && critical < warning))
		return false;
	result = {temperature, warning, critical, health[0], sampled_ms, true};
	return true;
}

inline ThermalState nvme_thermal_state(const NvmeThermal& n,
    unsigned long long now_ms, unsigned long long max_age_ms,
    unsigned margin_k) {
	if (!n.valid || !max_age_ms || now_ms < n.sampled_ms ||
	    now_ms-n.sampled_ms > max_age_ms || n.temperature_k < 200 ||
	    n.temperature_k > 450 || (n.warning_k && (n.warning_k < 274 || n.warning_k > 450)) ||
	    (n.critical_k && (n.critical_k < 274 || n.critical_k > 450)) ||
	    (n.warning_k && n.critical_k && n.critical_k < n.warning_k))
		return ThermalState::Unknown;
	if (n.critical_k && n.temperature_k >= n.critical_k)
		return ThermalState::Critical;
	if ((n.critical_warning & 2u) != 0 ||
	    (n.warning_k && margin_k < n.warning_k && n.temperature_k >= n.warning_k-margin_k))
		return ThermalState::Warning;
	return n.warning_k && margin_k < n.warning_k ? ThermalState::Normal : ThermalState::Unknown;
}
// The first two DWORDs are the descriptor header, followed by the
// protocol-specific header. Check offsets against actual returned bytes.
inline bool nvme_payload(const uint32_t* h, size_t returned, uint32_t type,
    size_t minimum, size_t& offset) {
    if (!h || returned < 48 || h[0] < 48 || h[1] < 48 ||
        h[2] != 3 || h[3] != type || h[6] < 40 ||
        h[6] > returned-8 || h[7] < minimum) return false;
    const size_t at = 8 + static_cast<size_t>(h[6]);
    if (h[7] > returned-at) return false;
    offset=at; return true;
}
class NvmeAlert {
public:
    bool observe(ThermalState s) {
        if (s==ThermalState::Normal) {
            if (++normal_>=2) { last_=ThermalState::Normal; normal_=2; }
            return false;
        }
        normal_=0;
        if (s==ThermalState::Unknown || s<=last_) return false;
        last_=s; return true;
    }
private:
    ThermalState last_=ThermalState::Normal;
    unsigned normal_=0;
};
} // namespace smart_policy
