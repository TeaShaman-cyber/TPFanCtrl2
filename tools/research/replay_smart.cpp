// Offline counterfactual. Input: elapsed milliseconds, temperature Celsius.
#include "smart_shadow.h"
#include <iostream>
#include <sstream>
#include <string>

int main(int argc, char** argv) {
	if (argc != 2)
		return 2;
	smart_policy::Shadow shadow;
	if (!shadow.configure(argv[1]))
		return 2;
	std::string line;
	while (std::getline(std::cin, line)) {
		std::istringstream row(line);
		long long elapsed;
		double temperature;
		std::string extra;
		if (!(row >> elapsed >> temperature) || elapsed < 0 || row >> extra)
			return 2;
		const auto result = shadow.observe(static_cast<unsigned long long>(elapsed), temperature, 128,
		    temperature > 0 && temperature <= 110);
		std::cout << elapsed << ' ' << result.projected << '\n';
	}
	return std::cin.bad() ? 2 : 0;
}
