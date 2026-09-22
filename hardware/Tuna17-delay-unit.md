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

## Three controls that had to come first

### 1. The null hypothesis has to be built on the same statistic

The observable is the *mean over eight samples* of $\max|\Delta P|$. Our initial null resampled
a *single* pair of $8192$-shot runs from arm A's empirical distribution, which is far too wide:
it understates the power of the test and hides real effects.

Built correctly (mean of eight, $2\times10^4$ trials), the null is
$\max|\Delta P| = 0.00910 \pm 0.00109$, $95\%$ quantile $0.01097$, and the picture sharpens:

| Arm | observed | ratio to shot-noise null | $z$ | $p$ |
|---|---|---|---|---|
| B1 | $0.00943$ | $1.04$ | $+0.30$ | $0.366$ |
| B4 | $0.01170$ | $1.29$ | $+2.40$ | $0.014$ |
| C1 | $0.01057$ | $1.16$ | $+1.36$ | $0.093$ |
| C4 | $0.00966$ | $1.06$ | $+0.52$ | $0.295$ |

B4 becomes marginal ($p = 0.014$), but it does not survive a Bonferroni correction across four
arms ($\alpha = 0.05/4 = 0.0125$).

### 2. The shot-noise null is not the right null for this device

Even the corrected null answers the wrong question. Two blocks of the later delay sweep are
*gate-for-gate identical to arm A* and were submitted at a different time; running the same
circuit eight times on each side gives the spread the device produces when it simply repeats
itself:

| Comparison | $\max|\Delta P|$ | $n$ |
|---|---|---|
| Two $65536$-shot runs of the same circuit, ~1 h apart | $0.01553$ | $8$ |
| $8192$-shot arm A vs $65536$-shot identical circuit | $0.01624$ | $8$ |
| Pure shot-noise null | $0.00260$ | $8$ |

**Real hardware is six times less repeatable than shot statistics alone predict.** Any effect
smaller than the device's own reproducibility cannot be attributed to the experimental variable.

### 3. Every delayed arm is below that floor

Against the same-circuit different-time value of $0.01624$, the four delayed arms are:
B1 $0.48\times$, B4 $0.55\times$, C1 $0.49\times$, C4 $0.49\times$ --- **all less than half**.
The difference the device produces when it runs the identical circuit again is larger than the
entire effect of the four delayed arms. The five-arm ablation is a null result, and the reason
is not the shot count.

## Root cause

The ablation never realised a dephasing channel, because we misread the unit of `wait`.
Two independent official sources:

> **cQASM specification, `wait` instruction:** "The delay time is passed along with the
> instruction as a dimensionless parameter, the unit of which represents the duration of a
> single-qubit gate on the backend, i.e. an execution cycle."

> **Quantum Inspire, Tuna backends: operational specifics:** "the number of cycles
> (**in steps of 20 ns**) that the target should idle ... Scheduling takes into account the
> duration of operations (20 ns native single-qubit gates, 60 ns for CZ gates, 800 ns for
> measurements, and 500 or 200 µs for initialization)."

So the cycle is $20$ ns, and:

| `wait(N)` | physical time | fraction of $T_2$ |
|---|---|---|
| 1 | 20 ns | $\sim10^{-3}$ |
| 4 | 80 ns | $\sim4\times10^{-3}$ |
| 64 | 1.28 µs | $\sim3\%$ |
| 16384 | 328 µs | into $T_1$ |
| 65536 | 1.31 ms | far into $T_1$ |

The entire original ablation lived at $10^{-3}$ of $T_2$. It could not have worked.

### The trap: `dt` is not a time

`qiskit_quantuminspire`'s converter emits `qc.delay(n, q, unit="dt")` as `wait(n) q[i]`. The
name `dt` suggests a hardware sample period in seconds, and that is exactly the assumption we
made. For this platform it is the gate cycle instead. The value is dimensionless and
backend-dependent, and the documents above are the only places it is defined.

## A second mistake, and the rule it produced

Fixing the delays exposed a separate scheduling error of ours, which cost $13$ circuits to
cancellation before we understood it. **The idle time of `wait` is paid once per shot**, so a
circuit's execution time scales with `shots x delay`, while `job_execution_time_limit` is a
$300$-second budget for the *whole batch*, not per circuit:

| Circuits per batch | Largest delay | Batch execution time | Outcome |
|---|---|---|---|
| 5 | mixed, incl. 65536 | > 300 s | cancelled, and the innocent circuits with it |
| 1 | 16384 | ~107 s | completes |
| 1 | 65536 | ~430 s | cannot fit the budget at all |

Across 17 batches we lost $13$ of $81$ jobs, every one of them to
`BatchJob exceeded maximum execution time limit of 300.0 [s]`, and $9$ of the $17$ batches were
affected. **One circuit per batch** is the correct unit. This also means a delay sweep must be
planned against the execution-time budget, not only against the physics.

## The corrected experiment

**Design.** Same batch of samples, same circuit, only the `wait` parameter changes, swept across
five orders of magnitude: $\tau \in \{0, 1, 4, 16, 64, 256, 1024, 4096, 16384, 65536\}$ cycles,
at $65536$ shots per circuit --- eight times the original, so the shot noise falls by
$1/\sqrt{8} \approx 0.35$. One circuit per batch.

**Verification that only `wait` changes.** Every compiled circuit in the sweep was compared
instruction by instruction with the `wait` lines removed: the gate sequence is identical at
every $\tau$ ($42$ operations in all), and $\tau = 0$ is gate-for-gate identical to arm A.

**The barrier caveat, handled.** The cQASM specification notes that `wait` *also* acts as a
barrier, and that waits on multiple qubits are scheduled independently. So "adding a `wait`" and
"adding idle time" are not the same operation. In this design the `wait` is placed immediately
before the measurement, after which no gates remain to reorder --- the barrier property has
nothing to act on. This is also why the sweep uses the tail position rather than the front
position.

**Nulls.** Shot noise at this shot count is $\max|\Delta P| = 0.00260$ (mean of eight,
$2\times10^4$ trials). The device repeatability is $0.01553$ ($8$ samples).

**Result.** The dose response appears, monotonically, and $P(00000)$ tracks it --- exactly the
shape $T_1$ relaxation predicts. Samples are $8$ per point except $16384$ ($7$) and $65536$ ($1$):

| $\tau$ (cycles) | $\max|\Delta P|$ | vs. shot noise | vs. repeatability | $P(00000)$ |
|---|---|---|---|---|
| 0 | $0$ | --- | --- | $0.01274$ |
| 1 | $0.00450$ | $1.73\times$ | $0.29\times$ | $0.01248$ |
| 4 | $0.00400$ | $1.54\times$ | $0.26\times$ | $0.01338$ |
| 16 | $0.00709$ | $2.72\times$ | $0.46\times$ | $0.01567$ |
| 64 | $0.02413$ | $9.27\times$ | $1.55\times$ | $0.02519$ |
| 256 | $0.05456$ | $20.95\times$ | $3.51\times$ | $0.05874$ |
| 1024 | $0.25476$ | $97.84\times$ | $16.41\times$ | $0.26750$ |
| 4096 | $0.64440$ | $247.48\times$ | $41.50\times$ | $0.65714$ |
| 16384 | $0.73543$ | $282.10\times$ | $47.37\times$ | $0.74809$ |
| 65536 | $0.81120$ | $311.18\times$ | $52.25\times$ | $0.82332$ |

The first three points pass the shot-noise test ($1.73\times$, $1.54\times$, $2.72\times$) yet sit
*below* the device repeatability. Reporting only the shot-noise null would have presented them as
the channel already appearing. The first undeniable signal is $\tau = 64$ (about $1.28$ µs),
$1.55\times$ the repeatability.

The curve keeps rising to the last point: $P(00000)$ reaches $0.823$, which is the readout
assignment-fidelity ceiling rather than $1$, i.e. the state has fully relaxed to $|0\dots0\rangle$.
The rise between $1024$ and $4096$ cycles fixes the $T_1$ scale at about $10^3$ cycles, tens of
microseconds, consistent with a typical superconducting transmon.

## What this changed

1. The hardware section of the paper was rewritten: the five-arm ablation is presented as a null
   limited by device reproducibility, not as evidence about the dephasing channel.
2. The claim "the delay is too short to matter" was replaced by a measurement of where the
   channel does appear, and by an explicit two-null statistical protocol.
3. The paper now states the `wait` unit and its per-shot cost, because a reader reproducing this
   work on any backend will hit both traps.

## Lessons worth keeping

- **A unit is a claim.** `unit="dt"` looked like seconds. It was cycles of 20 ns. Both sources
  above existed the whole time; the operational-specifics page is the one to read first.
- **Build the null on the statistic you actually report.** A single-sample null turned a
  $1.29\times$ effect into "invisible".
- **Then ask what the right null is.** Shot noise is not the noise floor of a real device; ours
  was six times worse than the multinomial prediction. A control with no variable at all ---
  the same circuit, run again later --- is worth more than a tighter error bar.
- **Verify that only the intended thing changed.** Stripping `wait` lines and diffing the rest of
  the circuit took ten lines of Python and is the strongest statement in the hardware section.
- **Check the execution-time budget before the physics.** `shots x delay` against a per-batch
  limit decided which circuits could run at all, and cost us $13$ of them to learn.
