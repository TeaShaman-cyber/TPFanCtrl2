import Lean

set_option warningAsError true

/- R17HT34W: local state abstraction, not a CR16 ISA equivalence proof.
   199a6: stage 11 sample check; 199ea: stage 12 first action;
   19afa: clamp. Addresses are payload offsets.
   Bounds/output within 0..500 and decrement <= output when modeling
   hardware unsigned arithmetic. Full scheduler reachability is unknown.
-/
namespace FanAuthority

structure State where
  stage : Nat
  misses : Nat
  lower : Nat
  upper : Nat
  output : Nat
  deriving Repr, DecidableEq

def sampleCheck (s : State) (rpm : Nat) : State :=
  let misses := if rpm == 65535 then (s.misses + 1) % 256 else 0
  let enterRecovery := if rpm == 65535 then misses > 8 else rpm <= 299
  { s with misses := misses, stage := if enterRecovery then 12 else 11 }

def raiseFloor (s : State) : State :=
  { s with lower := min s.upper (max s.lower s.output + 1) }

def clamp (s : State) (request : Nat) : Nat :=
  min s.upper (max s.lower request)

def correctDown (s : State) (decrement : Nat) : State :=
  { s with output := clamp s (s.output - decrement) }

def seed : State := ⟨11, 0, 25, 500, 400⟩

-- Direct emulation observations, with stage 11 and valid ordered bounds.
example : (sampleCheck seed 5100).stage = 11 := by decide
example : (sampleCheck seed 300).stage = 11 := by decide
example : (sampleCheck seed 299).stage = 12 := by decide
example : (sampleCheck seed 0).stage = 12 := by decide
example : sampleCheck {seed with misses := 7} 65535 = {seed with misses := 8} := by decide
example : sampleCheck {seed with misses := 8} 65535 = {seed with misses := 9, stage := 12} := by decide
example : (raiseFloor seed).lower = 401 := by decide
example : (raiseFloor {seed with lower := 410}).lower = 411 := by decide
example : (raiseFloor {seed with lower := 500, output := 500}).lower = 500 := by decide
example : (correctDown seed 20).output = 380 := by decide
example : (correctDown {seed with lower := 350} 20).output = 380 := by decide
example : (correctDown {seed with lower := 380} 20).output = 380 := by decide
example : (correctDown {seed with lower := 390} 20).output = 390 := by decide
example : (correctDown {seed with lower := 400} 20).output = 400 := by decide

theorem clamp_bounded (s : State) (request : Nat) (h : s.lower <= s.upper) :
    s.lower <= clamp s request ∧ clamp s request <= s.upper := by
  unfold clamp
  exact ⟨Nat.le_min.mpr ⟨h, Nat.le_max_left ..⟩, Nat.min_le_left ..⟩

theorem floor_nondecreasing (s : State) (h : s.lower <= s.upper) :
    s.lower <= (raiseFloor s).lower := by
  change s.lower <= min s.upper (max s.lower s.output + 1)
  exact Nat.le_min.mpr ⟨h, Nat.le_trans (Nat.le_max_left ..) (Nat.le_succ _)⟩

theorem correction_blocked_or_reversed (s : State) (d : Nat)
    (h : s.output <= s.lower) (ordered : s.lower <= s.upper) :
    s.output <= (correctDown s d).output := by
  exact Nat.le_trans h (clamp_bounded s (s.output - d) ordered).1

-- Concrete conditional composition: the actual scheduler's return to stage
-- 11 has not been established. This tests the two actions in isolation.
def afterFault := sampleCheck {seed with misses := 8} 65535
def raised := raiseFloor afterFault

theorem conditional_conflict :
    afterFault.stage = 12 ∧ raised.lower = 401 ∧
      (correctDown raised 20).output = 401 := by decide

theorem no_unconditional_progress :
    ¬ (∀ s : State, s.lower <= s.output → s.output <= s.upper →
      0 < s.output → (correctDown s 20).output < s.output) := by
  intro h
  have bad := h {seed with lower := 400} (by decide) (by decide) (by decide)
  exact (by decide : ¬ ((correctDown {seed with lower := 400} 20).output < 400)) bad

#print axioms clamp_bounded
#print axioms floor_nondecreasing
#print axioms correction_blocked_or_reversed
#print axioms conditional_conflict
#print axioms no_unconditional_progress

end FanAuthority
