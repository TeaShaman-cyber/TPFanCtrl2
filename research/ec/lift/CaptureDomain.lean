import Std
set_option warningAsError true
set_option maxRecDepth 8192
set_option maxHeartbeats 8000000
namespace R17CaptureDomain
-- Arithmetic projection of 192fe for channel divisor 5, positive average.
-- Not a machine-code lift of the loop/division helper.
def rpmWord (period : Nat) : Nat := (60000000 / period) % 65536
def periods : List Nat := (List.range 65534).map (· + 1)
def aliases : List Nat :=
  (List.range 915).map (· + 1) |>.filter (fun p => 2000 ≤ rpmWord p && rpmWord p ≤ 6500)
def sampleWord (count a b : Nat) : Nat :=
  if count = 0 then 65535 else rpmWord ((a+b)/count)

-- Finite exhaustive checks over the arithmetic projection, not physical claims.
theorem no_65534 : periods.all (fun p => rpmWord p != 65534) = true := by native_decide
theorem no_missing_collision : periods.all (fun p => rpmWord p != 65535) = true := by native_decide
theorem max_word_bound : periods.all (fun p => rpmWord p ≤ 65502) = true := by native_decide
theorem alias_count : aliases.length = 96 := by native_decide
theorem plausible_alias : rpmWord 48 = 4816 := by decide
theorem same_word : rpmWord 48 = rpmWord 12458 := by decide
theorem short_period_overflow : 65535 < 60000000 / 48 := by decide
theorem mixed_sample : sampleWord 2 48 12000 = 9960 := by decide
theorem zero_mixed_sample : sampleWord 2 0 12000 = 10000 := by decide
#print axioms no_65534
#print axioms no_missing_collision
#print axioms max_word_bound
#print axioms alias_count
#print axioms plausible_alias
#print axioms same_word
example : sampleWord 0 0 0 = 65535 := by decide
example : sampleWord 1 12000 0 = 5000 := by decide
example : sampleWord 2 12000 12000 = 5000 := by decide
example : sampleWord 2 48 48 = 4816 := by decide
example : sampleWord 2 916 916 = 65502 := by decide
example : sampleWord 2 915 915 = 37 := by decide
example : sampleWord 2 1 1 = 34560 := by decide
example : sampleWord 2 15 15 = 2304 := by decide
example : sampleWord 0 0 0 = 65535 := by decide
example : sampleWord 2 0 12000 = 10000 := by decide
example : sampleWord 2 48 12000 = 9960 := by decide
example : sampleWord 2 12000 48 = 9960 := by decide
example : sampleWord 2 12000 23529 = 3377 := by decide
example : sampleWord 2 23529 12000 = 3377 := by decide
example : sampleWord 1 48 0 = 4816 := by decide
example : sampleWord 1 48 0 = 4816 := by decide
example : sampleWord 2 50000 50000 = 1200 := by decide
example : sampleWord 2 7324 7324 = 8192 := by decide
example : sampleWord 2 7325 7325 = 8191 := by decide
example : sampleWord 2 22625 22625 = 2651 := by decide
end R17CaptureDomain
