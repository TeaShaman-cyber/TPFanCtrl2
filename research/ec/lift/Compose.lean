-- Appended to the three generated Lean modules by CI.
namespace R17Composition
-- Conditional composition only: the original scheduler must dispatch
-- the recovery update after the decision, and subsequently invoke clamp.
def floorAfterDecision (misses : BitVec 8) (rpm r0 samplePsr lower upper output recoveryPsr : BitVec 16) : BitVec 16 :=
  if 256 ≤ R17Sample.lifted misses rpm r0 samplePsr then
    R17Recovery.lifted lower upper output recoveryPsr
  else lower

theorem ninth_miss_saturates (r0 samplePsr lower recoveryPsr : BitVec 16)
    (h : lower ≤ 500) :
    floorAfterDecision 8 65535 r0 samplePsr lower 500 500 recoveryPsr = 500 := by
  unfold floorAfterDecision
  rw [R17Sample.ninth_miss]
  simp only [if_pos (show (256 : BitVec 16) ≤ 265 by decide)]
  exact R17Recovery.saturation lower recoveryPsr h

theorem ninth_miss_then_clamp_stuck
    (r0 samplePsr lower recoveryPsr request clampPsr : BitVec 16)
    (h : lower ≤ 500) :
    R17Lift.lifted (floorAfterDecision 8 65535 r0 samplePsr lower 500 500 recoveryPsr) 500 request clampPsr = 500 := by
  rw [ninth_miss_saturates r0 samplePsr lower recoveryPsr h]
  exact R17Lift.saturated request clampPsr

theorem valid_sample_preserves_floor (misses : BitVec 8)
    (rpm r0 samplePsr lower upper output recoveryPsr : BitVec 16)
    (h : 300 ≤ rpm) (h2 : rpm ≠ 65535) :
    floorAfterDecision misses rpm r0 samplePsr lower upper output recoveryPsr = lower := by
  unfold floorAfterDecision
  rw [R17Sample.valid_reset misses rpm r0 samplePsr h h2]
  simp only [if_neg (show ¬ ((256 : BitVec 16) ≤ 0) by decide)]

theorem eighth_or_less_preserves_floor (misses : BitVec 8)
    (r0 samplePsr lower upper output recoveryPsr : BitVec 16)
    (h : misses < 8) :
    floorAfterDecision misses 65535 r0 samplePsr lower upper output recoveryPsr = lower := by
  unfold floorAfterDecision
  rw [R17Sample.eighth_or_less misses r0 samplePsr h]
  have hn : ¬ ((256 : BitVec 16) ≤ BitVec.setWidth 16 (misses + 1)) := by bv_decide
  simp only [if_neg hn]

#print axioms ninth_miss_saturates
#print axioms ninth_miss_then_clamp_stuck
#print axioms valid_sample_preserves_floor
#print axioms eighth_or_less_preserves_floor
end R17Composition
