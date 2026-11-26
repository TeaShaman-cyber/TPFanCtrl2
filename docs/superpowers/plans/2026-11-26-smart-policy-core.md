# Smart policy core Implementation Plan

> **For agentic workers:** Use the repository TDD and exact-head QA gates.

**Goal:** Implement the first offline decision component of the approved design.
**Architecture:** Pure C++11 header with explicit configuration and observations.
No hardware calls; legacy Smart is not changed. Later integration is separate.
**Spec:** docs/superpowers/specs/2026-11-26-smart-thermal-policy-design.md

- [x] RED: pytest compiles tests/smart_policy_test.cpp with g++ -std=c++11,
  checks monotone interpolation, adjacent demand, short spike cancellation,
  sustained rise, longer fall, pending acknowledgment, urgent/invalid input,
  stale time, manual reset, and latched firmware handback/reacquisition.
- [x] GREEN: fancontrol/smart_policy.h implements Policy::evaluate(Sample),
  returning Hold, Firmware or a calibrated Level; no default device policy.
  All durations, thermal bounds and RPM calibration are explicit.
- [x] Run the new test and existing offline pytest, transport and mutation gates.
- [ ] Commit/push to feature/smart-thermal-policy; open draft PR for hosted
  exact-head QA. No merge or deployment until relevant acceptance.
- [ ] Follow-up: integrate with Smart engine and validated sensors; replay
  measured traces and do controlled live trials before proposing upstream.

Review focus: malformed curves, missing levels, equal timestamps, gaps,
pending command superseded by emergency, recovery after sensor failure,
manual mode not overridden, no timer accumulation across direction change.
