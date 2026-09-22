/-
  QBN 專案 —— 去相位消融的理論：形式化驗證（Lean 4 + mathlib）

  對應論文第 3 節「理論基礎」：
    引理 1  U 是么模仿塊矩陣 ⟹ U P_b U† = P_{π(b)}
    定理 1  U 是么模仿塊矩陣 ⟹ E(U ρ U†) = U E(ρ) U†
    推論    CNOT（置換矩陣）與去相位交換
    定理 2  尾端去相位不改變量測機率

  去相位通道在 mathlib 裡就是 Matrix.diagonal（把非對角元歸零）。
  注意：定理 1 不需要 U 么正 —— 只要 U 是么模仿塊矩陣就成立，
  因為對角元兩側的 d i · star(d i) 因子相同。
-/

import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Matrix.Diagonal
import Mathlib.Basic.Complex.Basic
import Mathlib.LinearAlgebra.Matrix.ConjTranspose

open Matrix
open scoped Matrix

namespace Qbn

variable {n : Type*} [DecidableEq n]

/-- 計算基底去相位（pinching channel）：把所有非對角元歸零。
    論文式 (3.2)：E(ρ) = Σ_b P_b ρ P_b = diag(ρ)。 -/
def dephase (ρ : Matrix n n ℂ) : Matrix n n ℂ :=
  diagonal (fun i => ρ i i)

@[simp]
theorem dephase_apply (ρ : Matrix n n ℂ) (i j : n) :
    dephase ρ i j = if i = j then ρ i i else 0 := by
  simp [dephase, Matrix.diagonal]

/-- 去相位保留對角元 —— 定理 2 的關鍵一步。
    對應論文引用的 Griffiths §12.3.1 Eq. 12.16（量測只讀對角元）。 -/
@[simp]
theorem dephase_apply_self (ρ : Matrix n n ℂ) (i : n) : dephase ρ i i = ρ i i := by
  simp [dephase, Matrix.diagonal]

/-- 么模仿塊矩陣：每一列恰有一個非零元素，U i j = d i 若 j = σ i，否則 0。 -/
def IsMonomial (U : Matrix n n ℂ) : Prop :=
  ∃ (σ : Equiv.Perm n) (d : n → ℂ), ∀ i j, U i j = if σ i = j then d i else 0

/-- 置換矩陣（全部 d i = 1）。CNOT、SWAP、X 都屬於這一類。 -/
def permMatrix (σ : Equiv.Perm n) : Matrix n n ℂ :=
  fun i j => if σ i = j then 1 else 0

theorem isMonomial_permMatrix (σ : Equiv.Perm n) : IsMonomial (permMatrix σ) :=
  ⟨σ, fun _ => 1, fun _ _ => rfl⟩

/-- 對角矩陣是么模仿塊矩陣（σ = id）。R_Z、S、T、Z 都屬於這一類。 -/
theorem isMonomial_diagonal (d : n → ℂ) : IsMonomial (diagonal d) :=
  ⟨Equiv.refl n, d, fun _ _ => rfl⟩

/-! ### 兩個乘法輔助引理（論文的「重新索引」在這一步發生） -/

theorem monomial_mul_apply [Fintype n] {U : Matrix n n ℂ} {σ : Equiv.Perm n} {d : n → ℂ}
    (hU : ∀ i j, U i j = if σ i = j then d i else 0) (ρ : Matrix n n ℂ) (i j : n) :
    (U * ρ) i j = d i * ρ (σ i) j := by
  rw [Matrix.mul_apply]
  simp only [hU, ite_mul, zero_mul]
  rw [Finset.sum_eq_single (σ i)]
  · simp
  · intro b _ hb
    simp [Ne.symm hb]
  · intro h
    exact absurd (Finset.mem_univ (σ i)) h

theorem monomial_mul_conjTranspose_apply [Fintype n] {U : Matrix n n ℂ} {σ : Equiv.Perm n}
    {d : n → ℂ} (hU : ∀ i j, U i j = if σ i = j then d i else 0) (ρ : Matrix n n ℂ) (i j : n) :
    (ρ * Uᴴ) i j = ρ i (σ j) * star (d j) := by
  rw [Matrix.mul_apply]
  rw [Finset.sum_eq_single (σ j)]
  · simp [Matrix.conjTranspose_apply, hU]
  · intro b _ hb
    have hne : σ j ≠ b := Ne.symm hb
    simp [Matrix.conjTranspose_apply, hU, hne]
  · intro h
    exact absurd (Finset.mem_univ (σ j)) h

/-! ### 主定理 -/

/-- **定理 1（交換性）**：U 是么模仿塊矩陣 ⟹ E(U ρ U†) = U E(ρ) U†。
    證明只用到「對一個集合重新索引」，沒有用到 ρ 的任何假設。 -/
theorem dephase_conj_monomial [Fintype n] {U : Matrix n n ℂ} {σ : Equiv.Perm n} {d : n → ℂ}
    (hU : ∀ i j, U i j = if σ i = j then d i else 0) (ρ : Matrix n n ℂ) :
    dephase (U * ρ * Uᴴ) = U * dephase ρ * Uᴴ := by
  have hL : ∀ i j, (U * ρ * Uᴴ) i j = d i * ρ (σ i) (σ j) * star (d j) := by
    intro i j
    rw [Matrix.mul_assoc, monomial_mul_apply hU, monomial_mul_conjTranspose_apply hU]
    ring
  have hR : ∀ i j, (U * dephase ρ * Uᴴ) i j
      = d i * (if σ i = σ j then ρ (σ i) (σ i) else 0) * star (d j) := by
    intro i j
    rw [Matrix.mul_assoc, monomial_mul_apply hU, monomial_mul_conjTranspose_apply hU,
      dephase_apply]
    ring
  ext i j
  rw [dephase_apply, hL, hR]
  by_cases hij : i = j
  · subst hij
    simp
  · have hσ : σ i ≠ σ j := fun h => hij (σ.injective h)
    simp [hij, hσ]

/-- **推論（CNOT 交換）**：置換矩陣與去相位交換。
    CNOT 在計算基底上是置換，故屬此類（論文推論 5.4）。 -/
theorem dephase_conj_permMatrix [Fintype n] (σ : Equiv.Perm n) (ρ : Matrix n n ℂ) :
    dephase (permMatrix σ * ρ * (permMatrix σ)ᴴ)
      = permMatrix σ * dephase ρ * (permMatrix σ)ᴴ :=
  dephase_conj_monomial (fun _ _ => rfl) ρ

/-- **定理 2（尾端去相位不改變量測機率）**：
    若 V 是么模仿塊閘（例如一串 CNOT），則去相位插在 U 與 V 之間時，
    計算基底量測的每一個機率都不變。 -/
theorem measurement_invariance [Fintype n] {U V : Matrix n n ℂ} (hV : IsMonomial V)
    (ρ : Matrix n n ℂ) (i : n) :
    (V * dephase (U * ρ * Uᴴ) * Vᴴ) i i = (V * (U * ρ * Uᴴ) * Vᴴ) i i := by
  obtain ⟨σV, dV, hV⟩ := hV
  rw [← dephase_conj_monomial hV (U * ρ * Uᴴ)]
  simp

/-! ### 公理檢查 —— 確認沒有任何 sorry -/

#print axioms Qbn.dephase_conj_monomial
#print axioms Qbn.dephase_conj_permMatrix
#print axioms Qbn.measurement_invariance
#print axioms Qbn.isMonomial_diagonal

end Qbn
