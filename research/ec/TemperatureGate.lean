import Lean

/- Abstract model of ec_temp_quality.h, not a proof of C++ compilation or
   physical cooling. Natural times model the ordered uint64_t domain. -/
namespace TemperatureGate

def usable (t : Nat) (r : Int) : Prop := r = 1 ∧ 0 < t ∧ t < 128
def fresh (start finish now budget : Nat) (epoch pollOk : Bool) : Prop :=
  pollOk = true ∧ epoch = true ∧ 0 < budget ∧ 0 < start ∧
  start ≤ finish ∧ finish ≤ now ∧ now - start ≤ budget

def permit (a b : Nat) (ra rb : Int) (start finish now budget : Nat)
    (epoch pollOk : Bool) : Prop :=
  fresh start finish now budget epoch pollOk ∧ usable a ra ∧ usable b rb ∧
  a ≤ b + 5 ∧ b ≤ a + 5

theorem missing_forbids (a b : Nat) (ra rb : Int)
    (start finish now budget : Nat) (epoch pollOk : Bool)
    (missing : ¬ usable a ra ∨ ¬ usable b rb) :
    ¬ permit a b ra rb start finish now budget epoch pollOk := by
  intro h
  rcases missing with ha | hb
  · exact ha h.2.1
  · exact hb h.2.2.1

theorem wrong_epoch_forbids (a b : Nat) (ra rb : Int)
    (start finish now budget : Nat) (pollOk : Bool) :
    ¬ permit a b ra rb start finish now budget false pollOk := by
  simp [permit, fresh]

theorem stale_forbids (a b : Nat) (ra rb : Int)
    (start finish now budget : Nat) (epoch pollOk : Bool)
    (stale : budget < now - start) :
    ¬ permit a b ra rb start finish now budget epoch pollOk := by
  intro h
  exact (Nat.not_le_of_gt stale) h.1.2.2.2.2.2.2

theorem disagreement_forbids (a b : Nat) (ra rb : Int)
    (start finish now budget : Nat) (epoch pollOk : Bool)
    (disagree : b + 5 < a ∨ a + 5 < b) :
    ¬ permit a b ra rb start finish now budget epoch pollOk := by
  intro h
  rcases disagree with ha | hb
  · exact (Nat.not_le_of_gt ha) h.2.2.2.1
  · exact (Nat.not_le_of_gt hb) h.2.2.2.2

theorem max_preserves_both (a b : Nat) : a ≤ max a b ∧ b ≤ max a b := by
  exact ⟨Nat.le_max_left _ _, Nat.le_max_right _ _⟩

theorem permit_requires_order (a b : Nat) (ra rb : Int)
    (start finish now budget : Nat) (epoch pollOk : Bool)
    (h : permit a b ra rb start finish now budget epoch pollOk) :
    start ≤ finish ∧ finish ≤ now := by
  exact ⟨h.1.2.2.2.2.1, h.1.2.2.2.2.2.1⟩

#print axioms missing_forbids
#print axioms wrong_epoch_forbids
#print axioms stale_forbids
#print axioms disagreement_forbids
#print axioms max_preserves_both
#print axioms permit_requires_order
end TemperatureGate
