import Std.Tactic.BVDecide
set_option warningAsError true
namespace R17CorrectionDomain
-- Projection of SUBW and signed CMPW at 19d82/19d8a, not of table lookup.
def increaseDirection (target rpm : BitVec 16) : Bool :=
  BitVec.slt 0 (target - rpm)

theorem ordinary_overspeed (rpm : BitVec 16)
    (lo : 2550 < rpm) (hi : rpm ≤ 35318) :
    increaseDirection 2550 rpm = false := by
  unfold increaseDirection
  bv_decide

theorem reversed_overspeed (rpm : BitVec 16)
    (lo : 35319 ≤ rpm) :
    increaseDirection 2550 rpm = true := by
  unfold increaseDirection
  bv_decide

theorem reachable_arithmetic_example : increaseDirection 2550 65502 = true := by decide
theorem adjacent_boundary : increaseDirection 2550 35318 = false ∧
    increaseDirection 2550 35319 = true := by decide

#print axioms ordinary_overspeed
#print axioms reversed_overspeed
#print axioms reachable_arithmetic_example
example : increaseDirection 2550 1141 = true := by decide
example : increaseDirection 2550 2550 = false := by decide
example : increaseDirection 2550 4600 = false := by decide
example : increaseDirection 2550 4816 = false := by decide
example : increaseDirection 2550 32767 = false := by decide
example : increaseDirection 2550 32768 = false := by decide
example : increaseDirection 2550 35318 = false := by decide
example : increaseDirection 2550 35319 = true := by decide
example : increaseDirection 2550 35320 = true := by decide
example : increaseDirection 2550 65502 = true := by decide
example : increaseDirection 2550 65534 = true := by decide
example : increaseDirection 2550 65535 = true := by decide
example : increaseDirection 4600 1141 = true := by decide
example : increaseDirection 4600 2550 = true := by decide
example : increaseDirection 4600 4600 = false := by decide
example : increaseDirection 4600 4816 = false := by decide
example : increaseDirection 4600 32767 = false := by decide
example : increaseDirection 4600 32768 = false := by decide
example : increaseDirection 4600 35318 = false := by decide
example : increaseDirection 4600 35319 = false := by decide
example : increaseDirection 4600 35320 = false := by decide
example : increaseDirection 4600 65502 = true := by decide
example : increaseDirection 4600 65534 = true := by decide
example : increaseDirection 4600 65535 = true := by decide
end R17CorrectionDomain
