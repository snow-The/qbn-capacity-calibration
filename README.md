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
across the compared arms. We supply that missing step with three experiments:

1. **Capacity cliff.** A scan over qubit count (3--10) and circuit depth (1--8) under a fixed
   readout rule, reporting calibration alongside accuracy.
2. **Calibration ablation.** A *dephasing* channel is inserted into the quantum layer, turning
   it classical *within the same model* --- no change of model, data or parameter count.
3. **Hardware verification.** The ablation channel itself is measured on QuTech's **Tuna-17**
   superconducting processor, sweeping the delay across five orders of magnitude to find the
   scale at which the channel actually appears.

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
- **The ablation channel has a scale, and we measured it.** cQASM's `wait(N)` counts
  *execution cycles* (single-qubit-gate durations, ~25 ns each), not nanoseconds. A four-arm
  ablation at 1--4 cycles therefore sits 2--3 orders of magnitude below $T_2$ and cannot
  realise the channel at all. Sweeping the delay from 1 to 65536 cycles on Tuna-17, and
  raising the shot count eightfold, turns that null result into a calibrated dose-response
  curve. See `hardware/Tuna17-delay-unit.md`.

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

Six theorems are formalised in `formal/Dephasing.lean` (Lean 4.34.0 + mathlib):

```
dephase_conj_monomial          Theorem 1 (commutation with monomial gates)
dephase_conj_permMatrix        CNOT corollary
measurement_invariance         Theorem 2 (terminal dephasing is invisible)
isMonomial_diagonal            diagonal matrices are monomial
not_isMonomial_RY              Lemma (the exact condition on R_Y)
not_isMonomial_RY_pi_div_four  R_Y(pi/4) counterexample
```

An audit with `#print axioms` shows every one of them depends only on
`[propext, Classical.choice, Quot.sound]`. **No `sorryAx`** --- no step is skipped or assumed.

### A correction forced by the formalisation

The paper originally said that $R_Y$ fails to be monomial whenever $\sin(\theta/2) \neq 0$.
That is *imprecise*: $R_Y(\pi) = \begin{pmatrix}0 & -1 \\ 1 & 0\end{pmatrix}$ **is** a monomial
matrix. The exact statement is that $R_Y(\theta)$ is monomial **iff** $\theta \in \pi\mathbb{Z}$,
equivalently iff $\sin$ and $\cos$ of $\theta/2$ are *both* non-zero for the failure. Writing the
proof in Lean is what surfaced this, and both language editions are corrected.

## Theory in one paragraph

Computational-basis dephasing is $\mathcal{E}(\rho)=\mathrm{diag}(\rho)$, i.e. it zeroes the
off-diagonal entries and removes the system's capacity to interfere (Tucci's classicalising
operator $\mathrm{cl}$). If $U$ is a **monomial matrix** (exactly one non-zero entry per row and
column, e.g. CNOT, CZ, SWAP, $R_Z$) then $U P_b U^\dagger = P_{\pi(b)}$ and hence
$\mathcal{E}(U\rho U^\dagger) = U\mathcal{E}(\rho)U^\dagger$ (**Theorem 1**). Consequently, if
dephasing is followed only by monomial gates, every computational-basis measurement probability
is unchanged (**Theorem 2**) --- which is why terminal dephasing is invisible. $R_Y(\theta)$ is
monomial only for $\theta \in \pi\mathbb{Z}$, which is why the ablation must be inserted
*before* a layer containing a generic $R_Y$ to be observable.

The theory is written using only tools from undergraduate quantum mechanics (density operators,
projection operators, commutators, unitary similarity). No quantum-channel formalism is
required for any step of the deduction, and none is assumed of the reader.

## Repository layout

```
paper/     Paper source (Typst is the single source of truth; LaTeX is generated).
           Includes submission.zip, the ready-to-upload arXiv package.
           Compiled PDFs are deliberately not tracked -- rebuild them with build_all.bat.
theory/    Theoretical write-ups and their numerical verification scripts
formal/    Lean 4 formalisation of the core theorems
hardware/  Real-hardware protocol (Quantum Inspire / Tuna-17) and diagnostics
ml/        Training and scan code
c1/        Cross-framework reproduction study
results/   Compact result summaries and the raw hardware counts
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

`hardware/` documents the real-device protocol for Quantum Inspire's Tuna-17, and two failure
modes we ran into and fully diagnosed:

1. **`"No Results"` is a lie.** Jobs whose batch exceeds the backend's `job_execution_time_limit`
   (300 s) are reported by the Qiskit provider as a bare `"No Results"` string rather than as
   cancellations. That diagnosis, and the recovery of 72 device-executed results, is in
   `hardware/Tuna17-NoResults-診斷.md`.
2. **`wait(N)` is not nanoseconds.** The cQASM specification defines the delay unit as the
   duration of a single-qubit gate on the backend --- an *execution cycle*. Reading it as a
   time in ns makes a 1--4 cycle ablation look like a real dephasing experiment when it is
   not. That diagnosis, the corrected experiment, and the dose-response curve, are in
   `hardware/Tuna17-delay-unit.md`.

We consider documenting these worth as much as the positive results: they cost us a night, and
the second one changed what the hardware section of the paper is able to claim.

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
我們補上三項實驗——容量斷崖掃描（qubit 3–10 × 深度 1–8，固定讀出規則並同時報告校準）、
去相位消融（以古典化算子作為同一模型內的唯一變因），以及
**真機驗證**（在 QuTech 的 Tuna-17 上把去相位延遲掃過五個數量級，量出通道真正出現的尺度）。

主要結論：尾端去相位在量測上是**定理保證的零**（臂 C 與臂 A 逐位元相同，但態純度差八倍以上）；
前端去相位把模型壓成無資訊的均勻預測（且它的 ECE 反而更低，證明單一校準指標不足以當證據）。
我們不主張任何量子優勢——5 個 qubit 的狀態向量只有 512 位元組。

真機部分的關鍵發現是**尺度**：cQASM 的 `wait(N)` 單位是「執行週期」（單閘時間，約 25 ns）而非 ns，
因此 1–4 個週期的四臂協定比 $T_2$ 短 2–3 個數量級，根本沒有實現去相位通道；
把延遲推到 65536 個週期並把 shots 提高八倍之後，單調的劑量反應才出現。

理論部分只用大學量子力學的工具寫成，並經 **Lean 4 形式化驗證**（6 個定理、無 `sorry`、
僅依賴三個標準公理）。形式化過程中還逼出了一處修正：$R_Y(\pi)$ 其實**是**么模仿塊矩陣，
精確條件是 $R_Y(\theta)$ 為么模仿塊 $iff 	heta in pimathbb{Z}$——論文原本只寫了一個條件，已更正。

## License

The two kinds of content carry different licences (see `LICENSE` for the full texts):

- **Paper text and documentation** (`paper/*.typ`, `theory/`, `docs/`, this README):
  [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0).
- **Code** (`ml/`, `hardware/`, `c1/`, `formal/`, `paper/make_*.py`): MIT.
