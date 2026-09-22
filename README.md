# Capacity Cliff and Calibration Ablation in a Hybrid Quantum--Classical Classifier

**Xin Yang, Poyuan Chung, Yuan-Liang Zhong**
Department of Physics, Chung Yuan Christian University, Taoyuan, Taiwan

---

## What this is

This repository contains the source, code and verification artefacts for a study that asks a
question most hybrid quantum--classical classification papers do not ask:

> **Is the quantum layer actually doing anything?**

Existing work in this area reports improvements in accuracy and calibration, but the quantum
layer is never treated as a controlled variable in an ablation --- it is an identical constant
across the compared arms. We supply that missing step with two experiments:

1. **Capacity cliff.** A scan over qubit count (3--10) and circuit depth (1--8) under a fixed
   readout rule, reporting calibration alongside accuracy.
2. **Calibration ablation.** A *dephasing* channel is inserted into the quantum layer, turning
   it classical *within the same model* --- no change of model, data or parameter count.

## Headline results

- **Terminal dephasing is measurably a no-op.** Arm C (dephasing at the very end of the circuit)
  is bit-identical to arm A (no channel) on every predictive metric --- accuracy, ECE, NLL ---
  while the state purity differs by more than a factor of eight ($0.1230$ vs $1.0000$).
  This is not a null result: it is a *zero guaranteed by a theorem* (Theorem 2 below).
- **Front-end dephasing collapses the model.** Arm B produces an uninformative uniform
  distribution (mean max probability $0.1307 \approx 1/8$, KL to uniform $0.0000$).
  Tellingly, its ECE is *lower* than the all-quantum baseline ($0.0993$ vs $0.1079$) ---
  **a single calibration metric is not evidence of better calibration**.
- **No quantum advantage is claimed.** The 5-qubit state vector occupies 512 bytes and is
  fully classically simulable. The contribution is a verifiable pipeline and a falsifiable
  experimental design, not performance.

## Verification

Every quantum-circuit number below is computed by two independent implementations and compared
(acceptance criterion $10^{-10}$):

| Circuit | Agreement |
|---|---|
| Reproduction pipeline | $4.16\times10^{-17}$ |
| Largest capacity-scan circuit (250 gates) | $3.47\times10^{-18}$ |
| Ablation circuit | $8.33\times10^{-17}$ |

The dephasing ablation is additionally checked against an independent $32\times32$ density-matrix
implementation; both routes give *bit-identical* $0.05023467$ and $0.19299447$.

### Formal verification (Lean 4)

Theorems 1 and 2 and the CNOT corollary are formalised in `formal/Dephasing.lean`
(Lean 4.34.0 + mathlib). An audit with `#print axioms` shows:

```
'Qbn.dephase_conj_monomial'   depends on axioms: [propext, Classical.choice, Quot.sound]
'Qbn.dephase_conj_permMatrix' depends on axioms: [propext, Classical.choice, Quot.sound]
'Qbn.measurement_invariance'  depends on axioms: [propext, Classical.choice, Quot.sound]
```

**No `sorryAx`** --- no step in the proofs is skipped or assumed.

## Theory in one paragraph

Computational-basis dephasing is $\mathcal{E}(\rho)=\mathrm{diag}(\rho)$, i.e. it zeroes the
off-diagonal entries and removes the system's capacity to interfere (Tucci's classicalising
operator $\mathrm{cl}$). If $U$ is a **monomial matrix** (exactly one non-zero entry per row and
column, e.g. CNOT, CZ, SWAP, $R_Z$) then $U P_b U^\dagger = P_{\pi(b)}$ and hence
$\mathcal{E}(U\rho U^\dagger) = U\mathcal{E}(\rho)U^\dagger$ (**Theorem 1**). Consequently, if
dephasing is followed only by monomial gates, every computational-basis measurement probability
is unchanged (**Theorem 2**) --- which is why terminal dephasing is invisible. $R_Y$ is *not*
monomial (its first row has two non-zero entries), which is why the ablation must be inserted
*before* a layer containing $R_Y$ to be observable.

Every tool used is covered by the two designated textbooks (Griffiths & Schroeter 3e;
Arfken, Weber & Harris 7e); `paper/` contains a textbook map giving chapter and equation numbers
for each step. This was a deliberate design goal: the theory defence should be possible from the
course textbooks alone.

## Repository layout

```
paper/     Paper source (Typst is the single source of truth; LaTeX is generated)
theory/    Theoretical write-ups and their numerical verification scripts
formal/    Lean 4 formalisation of the core theorems
hardware/  Real-hardware protocol (Quantum Inspire / Tuna-17) and diagnostics
ml/        Training and scan code
c1/        Cross-framework reproduction study
results/   Compact result summaries
docs/      Experimental protocol and design notes
```

## Reproducing

```bash
# 1. Build the paper (Typst -> PDF, and Typst -> LaTeX -> PDF)
cd paper
typst compile --root .. paper.typ          # Chinese
typst compile --root .. paper_en.typ       # English
python make_latex.py && latexmk -xelatex paper.typ   # LaTeX edition

# 2. Verify the theory numerically
python theory/verify/t5_commutator_placement.py      # 25/25 checks

# 3. Verify the theory formally (needs Lean 4 + mathlib)
cd <mathlib4> && lake env lean <this-repo>/formal/Dephasing.lean
```

See `paper/README.md` for the full build instructions (including how the arXiv submission
package is produced and verified offline).

## A note on the real-hardware protocol

`hardware/` documents a real-device protocol for Quantum Inspire's Tuna-17, including a
subtle failure mode we ran into and fully diagnosed: jobs that exceed the backend's
`job_execution_time_limit` (300 s) are reported by the Qiskit provider as a bare
`"No Results"` string rather than as cancellations. That diagnosis, and the recovery of
72 device-executed results, is in `hardware/Tuna17-NoResults-診斷.md`.

We consider documenting this worth as much as the positive results: it cost us a night.

## Citation

```bibtex
@misc{yang2026capacity,
  title  = {Capacity Cliff and Calibration Ablation in a Hybrid Quantum--Classical Classifier},
  author = {Yang, Xin and Chung, Poyuan and Zhong, Yuan-Liang},
  year   = {2026},
  note   = {Department of Physics, Chung Yuan Christian University},
}
```

## 中文摘要

本研究檢驗「用量子電路當分類器輸出層」這條路線：**既有工作從未把量子層當成受控變因**。
我們補上兩項實驗——容量斷崖掃描（qubit 3–10 × 深度 1–8，固定讀出規則並同時報告校準）
與去相位消融（以古典化算子作為同一模型內的唯一變因）。

主要結論：尾端去相位在量測上是**定理保證的零**（臂 C 與臂 A 逐位元相同，但態純度差八倍以上）；
前端去相位把模型壓成無資訊的均勻預測（且它的 ECE 反而更低，證明單一校準指標不足以當證據）。
我們不主張任何量子優勢——5 個 qubit 的狀態向量只有 512 位元組。

理論部分以兩本指定大學用書（Griffiths 3e、Arfken 7e）的工具寫成，並經 **Lean 4 形式化驗證**
（無 `sorry`，僅依賴三個標準公理）。

## License

See `LICENSE`. **Text and code are intended to carry different licences**; the file is a
placeholder pending a decision and the repository is not ready for public release until it is
replaced.
