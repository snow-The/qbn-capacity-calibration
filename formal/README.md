# 去相位消融理論的形式化驗證（Lean 4 + mathlib）

`Dephasing.lean` 把論文第 3 節（理論基礎）的命題寫成機器可檢查的證明。

## 驗證內容

| 論文 | Lean 定理 | 說明 |
|---|---|---|
| 定義（去相位通道） | `Qbn.dephase` | `E(ρ) = diag(ρ)`，即 `Matrix.diagonal` |
| — | `Qbn.dephase_apply_self` | 去相位保留對角元（定理 2 的關鍵） |
| 定義（么模仿塊矩陣） | `Qbn.IsMonomial` | 每列恰一個非零元素 |
| — | `Qbn.monomial_mul_apply` | 左乘只想留一項（重新索引） |
| — | `Qbn.monomial_mul_conjTranspose_apply` | 右乘 U† 只想留一項 |
| **引理 1 / 定理 1** | `Qbn.dephase_conj_monomial` | **E(U ρ U†) = U E(ρ) U†** |
| 推論（CNOT 交換） | `Qbn.dephase_conj_permMatrix` | 置換矩陣與去相位交換 |
| **定理 2** | `Qbn.measurement_invariance` | 尾端去相位不改變量測機率 |
| — | `Qbn.isMonomial_diagonal` | $R_Z$、$S$、$T$、$Z$ 屬么模仿塊 |

## 怎麼跑

```
# 需要 Lean 4.34.0（elan 安裝）與 mathlib（同一 tag）
cd <mathlib4>
lake env lean <此目錄>/Dephasing.lean
```

## 驗證結果（實際輸出）

```
#print axioms Qbn.dephase_conj_monomial
=> 'Qbn.dephase_conj_monomial' depends on axioms: [propext, Classical.choice, Quot.sound]
#print axioms Qbn.dephase_conj_permMatrix
=> 'Qbn.dephase_conj_permMatrix' depends on axioms: [propext, Classical.choice, Quot.sound]
#print axioms Qbn.measurement_invariance
=> 'Qbn.measurement_invariance' depends on axioms: [propext, Classical.choice, Quot.sound]
```

**只依賴 Lean/mathlib 的三個標準公理，沒有 `sorryAx`** ——
代表證明中沒有任何被跳過或假設掉的步驟。

## 環境註記（踩過的坑）

- `mathlib4` 的 `master` 需要 **release candidate** toolchain（`v4.35.0-rc2`）。
  請改用 **tag `v4.34.0`**（附帶的 `lake-manifest.json` 才會釘住正確的依賴版本）。
  切到 tag 之後**不要**跑 `lake update`（會把依賴升級回 master）；直接 `lake exe cache get`。
- 快取裡**沒有 umbrella 模組 `Mathlib.olean`**，所以 `import Mathlib` 會失敗；
  要 import 具體模組（例如 `Mathlib.Data.Matrix.Diagonal`）。
- 複數共軛在 Lean 4 是 `star`，不是 `conj`。
- `releases.lean-lang.org` 與 GitHub 的單線下載在此網路很慢（~60–200 KB/s，工具鏈 588 MB）。
  本專案用 12 段並行 range 下載取得（~1.3 MB/s），再解壓進 elan 的 toolchain 目錄。
