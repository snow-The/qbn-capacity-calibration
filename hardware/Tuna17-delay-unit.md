# The `wait(N)` unit problem: why our first hardware ablation measured nothing

This note records a mistake, how it was caught, and what replaced it. It changed what the
hardware section of the paper is able to claim.

## Symptom

We ran a five-arm dephasing ablation on Quantum Inspire's **Tuna-17** (17 transmons,
ninja-star topology). Forty circuits, $8192$ shots each, eight samples per arm:

| Arm | Delay (after encoding, before measurement) |
|---|---|
| A | none |
| B1, B4 | 1, 4 cycles inserted after encoding |
| C1, C4 | 1, 4 cycles inserted before measurement |

After routing (the topology has no 5-cycle, so the 5-qubit ring needs two `SWAP`s), every arm
compiled to an *identical* circuit: $\mathrm{CX} = 10$, $\mathrm{SWAP} = 2$, depth $18$, $42$
gates. Arms A and C differed only by five `wait` instructions. A clean controlled comparison.

**Every arm came back at the shot-noise floor.** Measured deviation from arm A:
B1 $0.00943$, C4 $0.00966$, C1 $0.01057$, B4 $0.01170$, against a null of $0.00910$.

Our first reading was "not enough shots". That reading was wrong, and acting on it alone would
have wasted a great deal of device time.

## Two controls that had to come first

### 1. The null hypothesis has to be built on the same statistic

The observable is the *mean over eight samples* of $\max|\Delta P|$. Our initial null resampled
a *single* pair of $8192$-shot runs from arm A's empirical distribution, which is far too wide:
it understates the power of the test and hides real effects.

Built correctly (mean of eight, $2\times10^4$ trials), the null is
$\max|\Delta P| = 0.00910 \pm 0.00109$, $95\%$ quantile $0.01097$, and the picture sharpens:

| Arm | observed | ratio | $z$ | $p$ |
|---|---|---|---|---|
| B1 | $0.00943$ | $1.04$ | $+0.30$ | $0.366$ |
| B4 | $0.01170$ | $1.29$ | $+2.40$ | $0.014$ |
| C1 | $0.01057$ | $1.16$ | $+1.36$ | $0.093$ |
| C4 | $0.00966$ | $1.06$ | $+0.52$ | $0.295$ |

B4 becomes marginal ($p = 0.014$), but it does not survive a Bonferroni correction across four
arms ($\alpha = 0.05/4 = 0.0125$).

### 2. A drift control with no variable at all

To decide whether even that marginal signal is physics, we need a comparison in which *nothing*
was changed. The $\tau = 0$ block of the later delay sweep is gate-for-gate identical to arm A,
and was submitted about an hour later. Subtracting the two gives
$\max|\Delta P| = 0.00883$ (two samples: $0.00755$, $0.01012$) --- indistinguishable from the
$0.00910$ shot-noise value.

So over one hour, hardware drift sits *below* the noise floor, and all four delayed arms sit in
that same range. The five-arm ablation is a null result.

## Root cause

The ablation never realised a dephasing channel, because we misread the unit of `wait`.
Two independent official sources:

> **cQASM specification, `wait` instruction:** "The delay time is passed along with the
> instruction as a dimensionless parameter, the unit of which represents the duration of a
> single-qubit gate on the backend, i.e. an execution cycle."

> **Quantum Inspire knowledge base:** "idle the qubit it operates on for the given number of
> cycles."

A superconducting transmon has a single-qubit gate time of order $25$ ns, while $T_2$ is
$10$--$100$ microseconds. So:

| `wait(N)` | physical time | fraction of $T_2$ |
|---|---|---|
| 1 | ~25 ns | $10^{-3}$ |
| 4 | ~100 ns | $4\times10^{-3}$ |
| 64 | ~1.6 µs | $\sim3\%$ |
| 65536 | ~1.6 ms | $\gg 1$ (into $T_1$) |

The entire original ablation lived at $10^{-3}$ of $T_2$. It could not have worked.

### The trap: `dt` is not a time

`qiskit_quantuminspire`'s converter emits `qc.delay(n, q, unit="dt")` as `wait(n) q[i]`. The
name `dt` suggests a hardware sample period in seconds, and that is exactly the assumption we
made. For this platform it is the gate cycle instead. The value is dimensionless and
backend-dependent, and the two documents above are the only places it is defined.

## The corrected experiment

**Design.** Same eight samples, same circuit, only the `wait` parameter changes, swept across
five orders of magnitude: $\tau \in \{0, 1, 4, 16, 64, 256, 1024, 4096, 16384, 65536\}$ cycles,
at $65536$ shots per circuit --- eight times the original, so the noise falls by
$1/\sqrt{8} \approx 0.35$.

**Verification that only `wait` changes.** Every compiled circuit in the sweep was compared
instruction by instruction with the `wait` lines removed: the gate sequence is identical at
every $\tau$ ($42$ operations in all), and $\tau = 0$ is gate-for-gate identical to arm A.

**The barrier caveat, handled.** The cQASM specification notes that `wait` *also* acts as a
barrier: instructions may not be reordered across it. So "adding a `wait`" and "adding idle
time" are not the same operation. In this design the `wait` is placed immediately before the
measurement, after which no gates remain to reorder --- the barrier property has nothing to act
on, and the only physical effect is idle time. This is also why the sweep uses the tail position
rather than the front position.

**Null.** Rebuilt at the new shot count: $\max|\Delta P| = 0.00260 \pm 0.00037$ (mean of eight,
$2\times10^4$ trials), $3.5\times$ finer than the $8192$-shot null.

**Result.** The dose response appears, monotonically, and $P(00000)$ tracks it --- exactly the
shape $T_1$ relaxation predicts:

| $\tau$ (cycles) | $\max\|\Delta P\|$ | ratio | $p$ | $P(00000)$ |
|---|---|---|---|---|
| 0 | 0 | --- | --- | $0.01237$ |
| 1 | $0.00263$ | $1.01$ | $0.436$ | $0.01288$ |
| 4 | $0.00453$ | $1.74$ | $0.0001$ | $0.01305$ |
| 16 | $0.00695$ | $2.67$ | $<0.0001$ | $0.01505$ |
| 64 | $0.02040$ | $7.85$ | $<0.0001$ | $0.02376$ |

($\tau = 0$ through $64$; the extension to $65536$ is reported in the paper's Section 6.4.)

## What this changed

1. The hardware section of the paper was rewritten: the five-arm ablation is now presented as a
   *power-limited null*, not as evidence about the dephasing channel.
2. The claim "the delay is too short to matter" was replaced by an explicit measurement of where
   the channel does appear.
3. The paper now states the `wait` unit explicitly, because a reader reproducing this work on
   any backend will hit the same trap.

## Lessons worth keeping

- **A unit is a claim.** `unit="dt"` looked like seconds. It was cycles. Nobody had written it
  down where we were looking; both sources above existed the whole time.
- **Build the null on the statistic you actually report.** A single-sample null turned a
  $1.29\times$ effect into "invisible" and a $7.85\times$ effect into "marginal".
- **A control with no variable is worth more than a tighter error bar.** The same-circuit,
  different-time comparison is what closed the case, and it costs one extra submission.
- **Verify that only the intended thing changed.** Stripping `wait` lines and diffing the rest of
  the circuit took ten lines of Python and is the strongest statement in the hardware section.
