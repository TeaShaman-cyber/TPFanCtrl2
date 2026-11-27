-- Appended after the generated modules and Compose.lean.
-- Directed, possibly nondeterministic walks; local simulations may stutter.
namespace R17Bridge
inductive Walk {α : Type} (r : α → α → Prop) : α → α → Prop
  | refl (a : α) : Walk r a a
  | single {a b : α} : r a b → Walk r a b
  | join {a b c : α} : Walk r a b → Walk r b c → Walk r a c

theorem mapInvariant {α β : Type} {r : α → α → Prop}
    {q : β → β → Prop} (p : α → Prop) (f : α → β)
    (step : ∀ {a b}, r a b → p a → p b ∧ Walk q (f a) (f b))
    {a b : α} (w : Walk r a b) : p a → p b ∧ Walk q (f a) (f b) := by
  induction w with
  | refl a => exact fun ha => ⟨ha, Walk.refl (f a)⟩
  | single h => exact step h
  | join _ _ ih1 ih2 =>
    intro ha
    obtain ⟨hb, w1⟩ := ih1 ha
    obtain ⟨hc, w2⟩ := ih2 hb
    exact ⟨hc, Walk.join w1 w2⟩

theorem closed {α : Type} {r : α → α → Prop}
    (p : α → Prop) (step : ∀ {a b}, r a b → p a → p b)
    {a b : α} (w : Walk r a b) : p a → p b := by
  induction w with
  | refl _ => exact id
  | single h => exact step h
  | join _ _ ih1 ih2 => exact fun ha => ih2 (ih1 ha)

-- Exact lifted slice effects, NOT full instructions outside the lifted slices.
-- The bound is fixed at 500; sample/return abstractions omit other memory.
structure State where
  floor : BitVec 16
  output : BitVec 16
  misses : BitVec 8
  pending : Bool
deriving DecidableEq

def sampleState (s : State) (rpm r0 psr : BitVec 16) : State :=
  let w := R17Sample.lifted s.misses rpm r0 psr
  {s with misses := BitVec.setWidth 8 w, pending := decide (256 ≤ w)}

inductive LocalStep : State → State → Prop
  | sample (s : State) (rpm r0 psr : BitVec 16) (h : s.pending = false) :
      LocalStep s (sampleState s rpm r0 psr)
  | raise (s : State) (psr : BitVec 16) (h : s.pending = true) :
      LocalStep s {s with floor := R17Recovery.lifted s.floor 500 s.output psr}
  | clamp (s : State) (request psr : BitVec 16) :
      LocalStep s {s with output := R17Lift.lifted s.floor 500 request psr}
  -- Explicit abstract return; not a lifted scheduler proof.
  | resume (s : State) (h : s.pending = true) :
      LocalStep s {s with pending := false, misses := 0}

def bounded (s : State) : Prop := s.floor ≤ 500 ∧ s.output ≤ 500

def floorOrder (a b : BitVec 16) : Prop := a ≤ b

theorem local_simulation {a b : State} (h : LocalStep a b) (ha : bounded a) :
    bounded b ∧ Walk floorOrder a.floor b.floor := by
  cases h with
  | sample s rpm r0 psr guard =>
    exact ⟨ha, Walk.refl s.floor⟩
  | raise s psr guard =>
    have hr := R17Recovery.recovery_nondecreasing s.floor 500 s.output psr ha.1 ha.2 (by decide)
    exact ⟨⟨hr.2, ha.2⟩, Walk.single hr.1⟩
  | clamp s request psr =>
    have hc := R17Lift.ordered_clamp s.floor 500 request psr ha.1
    exact ⟨⟨ha.1, hc.2⟩, Walk.refl s.floor⟩
  | resume s guard =>
    exact ⟨ha, Walk.refl s.floor⟩

theorem all_lifted_walks_monotone {a b : State} (h : Walk LocalStep a b)
    (ha : bounded a) : bounded b ∧ a.floor ≤ b.floor := by
  obtain ⟨hb, hw⟩ := mapInvariant bounded State.floor local_simulation h ha
  have hm : a.floor ≤ b.floor := closed (fun x => a.floor ≤ x)
    (fun {x y} hxy hx => by unfold floorOrder at hxy; bv_decide) hw (by bv_decide)
  exact ⟨hb, hm⟩

theorem saturated_closed {a b : State} (h : Walk LocalStep a b)
    (ha : bounded a) (hs : a.floor = 500) : b.floor = 500 := by
  obtain ⟨hb, hm⟩ := all_lifted_walks_monotone h ha
  have hu := hb.1
  bv_decide

theorem saturated_clamp {s : State} (h : s.floor = 500) (request psr : BitVec 16) :
    R17Lift.lifted s.floor 500 request psr = 500 := by
  rw [h]
  exact R17Lift.saturated request psr

-- Concrete witness in the slice model, not an entire firmware dispatch.
def seed : State := ⟨25, 500, 8, false⟩
def faulted : State := sampleState seed 65535 0 0
def raised : State := {faulted with floor := R17Recovery.lifted faulted.floor 500 faulted.output 0}
theorem fault_witness : Walk LocalStep seed raised := by
  exact Walk.join (Walk.single (LocalStep.sample seed 65535 0 0 (by decide)))
    (Walk.single (LocalStep.raise faulted 0 (by decide)))
theorem witness_floor : raised.floor = 500 := by decide

-- A real full initialization is outside LocalStep. Its projection breaks closure.
def reset (_s : State) : State := ⟨25, 0, 0, false⟩
theorem reset_breaks_saturation : (reset raised).floor ≠ 500 := by decide

#print axioms mapInvariant
#print axioms closed
#print axioms local_simulation
#print axioms all_lifted_walks_monotone
#print axioms saturated_closed
#print axioms fault_witness
#print axioms reset_breaks_saturation
end R17Bridge
