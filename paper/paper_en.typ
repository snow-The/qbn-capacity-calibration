// ===========================================================================
// English edition -- typeset with the local arxiv-style package, a Typst port
// of kourgeorge/arxiv-style. The preamble that used to live here (page metrics,
// text/par settings, heading and caption show rules, the hand-built title and
// author blocks, the abstract block and the keyword line) is now provided by
// the package, so those details live in one place instead of two.
// ===========================================================================
#import "../../../packages/typst-arxiv-style/lib.typ": arxiv-style

// --- math macros (the package deliberately does not provide these) ---------
#let ket(x) = [|#x⟩]
#let bra(x) = [⟨#x|]
#let braket(x, y) = [⟨#x|#y⟩]
#let ketbra(x, y) = [|#x⟩⟨#y|]
#let Tr = $op("Tr")$
#let EE = $bb(E)$
#let Var = $op("Var")$
#let KL = $op(D)_("KL")$
#let RR = $bb(R)$
#let CC = $bb(C)$
#let Hcal = $cal(H)$
#let dd = $dif$

// --- extras the package does not set ---------------------------------------
#set table(stroke: 0.4pt, inset: 5pt)
#show raw.where(block: true): it => block(
  fill: luma(248), inset: 6pt, radius: 2pt, width: 100%,
  text(font: ("DejaVu Sans Mono", "Cascadia Mono"), size: 8.5pt, it),
)

#show: arxiv-style.with(
  title: "Capacity Cliff and Calibration Ablation in a Hybrid Quantum--Classical Classifier",
  authors: (
    (name: "Xin Yang", affiliation-id: 1),
    (name: "Poyuan Chung", affiliation-id: 1),
    (name: "Yuan-Liang Zhong", affiliation-id: 1),
  ),
  affiliations: (
    (id: 1, name: "Department of Physics, Chung Yuan Christian University, Taoyuan, Taiwan. Corresponding author: ylzhong@cycu.edu.tw"),
  ),
  abstract: [
    This work is a controlled examination of using a quantum circuit as the output
    layer of a classifier, not an attempt to demonstrate quantum advantage. Building
    on the hybrid Bayesian quantum--classical classifier of Wang et al. (2026), we
    reproduce its 4-qubit quantum layer with CUDA-Q, a quantum-circuit simulator,
    and extend it with three experiments
    that the original study does not cover: (i) a *capacity cliff* scan over qubit
    count and circuit depth, testing whether performance is monotonic in trainable
    capacity; (ii) a *calibration ablation* in which a dephasing operator makes
    the quantum layer classical, isolating the marginal contribution of quantumness
    to calibration; and (iii) a *hardware verification* on QuTech's Tuna-17
    superconducting processor, sweeping the delay of end-of-circuit dephasing across
    five orders of magnitude to locate the scale at which the channel actually appears
    -- $1$--$4$ execution cycles (about $25$--$100$ ns) are far too short to realise it. Every quantum-circuit result is computed on both CUDA-Q and an
    independently implemented pure-NumPy state-vector simulator, then compared: the
    reproduction pipeline agrees to $4.16 times 10^(-17)$, the largest capacity-scan
    circuit (250 gates) to $3.47 times 10^(-18)$, and the ablation circuit to
    $8.33 times 10^(-17)$. We explicitly do not claim any quantum advantage: the
    state vector of 5 qubits occupies 512 bytes and is fully classically simulable.
    The contribution is a fully verifiable pipeline and a falsifiable experimental
    design.
  ],
  keywords: (
    "quantum Bayesian networks",
    "hybrid quantum--classical learning",
    "calibration",
    "uncertainty quantification",
    "CUDA-Q",
  ),
)

= Introduction

The final layer of a deep-learning classifier usually outputs a *softmax*
distribution---a set of real numbers exponentiated and normalised so that they sum
to $1$, and therefore probability-shaped. But these numbers are *not* calibrated
probabilities: they are frequently and systematically overconfident @guo2017.
By *calibration* we mean whether the confidence a model claims matches how often it
is actually right---a model that claims $90%$ confidence but is right only $70%$ of
the time cannot be trusted even if its accuracy is high.
In domains where trustworthy confidence is required (medicine, finance, education)
this problem cannot be assessed by accuracy alone.

A class of hybrid architectures has appeared in recent years: a classical network
extracts features and a quantum circuit then acts as the decision layer @wang2026.
Such work reports improvements in both accuracy and calibration, but it shares one
structural feature---*the quantum layer is never treated as a controlled variable
in an ablation*. (An *ablation*, in the machine-learning sense, is the practice of
deleting one component of a model so that its contribution can be measured in
isolation.)
Take @wang2026: its state-of-the-art design is a "single-variable" comparison in
which all models share the same preprocessing and classification head (the final
network layer that turns the extracted features into class scores), and only the
first convolutional layer is changed from deterministic to Bayesian.
The quantum layer is an identical constant across both arms.

Consequently that study---and work of the same kind---*cannot answer whether
quantumness itself is necessary*. This work supplies that missing step.

#block(inset: (x: 1em), fill: luma(248), radius: 2pt)[
  *Contributions*
  + We propose a *dephasing ablation*: using Tucci's classicalising operator
    @tucci2012 as the sole variable *within a single model* (no change of model,
    data or parameter count) to examine the marginal contribution of quantumness
    to calibration and capacity.
    Within the scope of our search we found no prior work that uses this operator
    as an ablation tool---the closest efforts either attribute behaviour
    observationally via entanglement measures @nausheen2026, or introduce
    depolarising noise as an external variable @ghosh2026.
  + We extend the *capacity cliff* scan to qubit counts $3$--$10$ $times$ circuit
    depths $1$--$8$. Prior work has established the $(Q, L)$ scaling protocol and
    reported saturation @vyskubov2026, and has observed non-monotonicity
    along a single axis (@le2025 for the qubit axis; @zhang2021suppression
    for the depth axis). What we add is the complete two-dimensional grid under a
    *fixed readout rule*, *with calibration reported alongside accuracy*, and one
    phenomenon that prior work has not reported: *test accuracy decreasing with
    qubit count*---which holds for configurations in which capacity is genuinely
    used (the per-$n$ peak and the deepest slice are monotone from $n = 4$), while
    shallower slices are masked by under-optimisation.
    ($n >= 3$ is a hard requirement: eight class probabilities need at least a
    3-qubit projective readout.)
  + We reproduce the 4-qubit quantum layer of @wang2026 with CUDA-Q (a
    quantum-circuit simulation framework) and cross-validate it---that is, check it
    against a second implementation written independently in NumPy (the standard
    numerical library for Python)---
    ($4.16 times 10^(-17)$); this item is positioned as *reproducibility evidence*,
    not as a methodological contribution. The two experiments of Section 6 are
    endorsed separately on the reference track: the largest capacity-scan circuit
    at $3.47 times 10^(-18)$ and the ablation circuit at $8.33 times 10^(-17)$.
  + We *verify the ablation channel itself on hardware*. On QuTech's Tuna-17 we sweep
    the delay of end-of-circuit dephasing from $1$ to $65536$ execution cycles, covering
    $T_2$ and $T_1$, and measure where the channel actually appears. The measured
    quantity is the deviation of the delayed circuit from the undelayed one, against a
    shot-noise null built by resampling the undelayed distribution, plus a
    same-circuit different-time drift control. This turns a null result into a
    calibrated statement about the delay scale a dephasing ablation needs.
  + We honestly report three negative conclusions (see Section 6).
]

= Related Work

== Hybrid quantum--classical classifiers

The three-stage skeleton of @wang2026 is "classical feature extraction -> quantum
state evolution -> classical decision". Its quantum layer uses a 4-qubit,
depth-2 parameterised quantum circuit (PQC), and the readout measures the
Pauli-$Z$ expectation values of all qubits into a vector that a linear layer---a
single matrix multiplication plus a bias, the simplest learnable
transformation---then classifies. Its gains come explicitly from the *classical Bayesian front end*:
MNIST (a handwritten-digit image dataset) $+2.32$ and Fashion-MNIST (a clothing-image
dataset) $+5.61$ percentage points, with the quantum layer held fixed.

== Known limits of capacity and distillation

@wada2025 reports two related phenomena in the study of *distillation* for static
word embeddings. (Distillation trains a small "student" model to imitate a larger
"teacher" model; an *embedding* represents a piece of text as a fixed-length vector
of real numbers.) First, when the student dimension is reduced to $d = 64$,
knowledge distillation actually degrades performance ($63.8 -> 52.5$). Second,
switching to a stronger teacher (GTE-large, a general-purpose text-embedding model) makes the student worse
($62.9$ against $63.8$ for GTE-base), which the authors attribute to an excessive
teacher--student capacity gap.
This work tests whether the same phenomenon---failure once the capacity gap
becomes too large---also appears in a quantum decision layer.

== Quantum Bayesian networks

@tucci2012 generalises the nodes of a classical Bayesian network from conditional
probability tables to quantum channels, and shows that applying the dephasing
operator $op("cl")$ to a node causes the entire network to degenerate into a
classical Bayesian network.
This operator is the theoretical basis of our ablation experiment: it is an
*exact classicalisation map*, so "quantum versus classical" requires no change of
model, data or parameter count.

== Quantumness as a controlled variable

The three works closest to ours each take a different route, and each leaves the
gap this study fills.

@jafari2026 replaces softmax with a *complex-valued unitary representation* as the
classification head: one shared backbone, only the lightweight head swapped. On
CIFAR-10 (a ten-class colour-image dataset) it lowers the expected calibration
error (ECE) from $0.0355$ to $0.0146$,
yet in the same study replacing the readout with a Born-rule measurement layer
(a readout that takes the squared amplitude of the wave function as the probability)
*degrades* it to $0.0819$. Two things follow: single-variable ablation of this kind
is feasible, and *a quantum-style readout is not by itself a guarantee of
calibration*. Note, however, that their variable is the *form of the
representation* (complex unitary versus real), and their unitary layer is
parameterised by the Cayley map (a way of writing a unitary matrix in terms of an
anti-Hermitian one) and therefore exactly executable on classical
hardware---so what they isolate is still not quantumness.

@nausheen2026 attributes performance *observationally* through the Meyer--Wallach
entanglement measure (a way of quantifying how entangled a many-body state is) on a
paraphrase-detection task---deciding whether two sentences mean the same thing
($r = 0.85$). But correlation
is not intervention: entanglement co-varies with circuit depth and parameter
count, so confounding cannot be excluded.

@ghosh2026 instead uses *depolarising noise* as an external variable, sweeping the
ECE of variational classifiers, finds that ECE does not rise monotonically with
noise, and warns that a less expressive ansatz may look well calibrated merely
because it has collapsed to a degenerate solution.

The shared gap is that quantumness itself has never been the sole variable *within
a single model*. This study fills that position with the classicalising operator of
@tucci2012. Taking up the warning of @ghosh2026, we record a collapse
indicator for every (arm, seed) pair.

= Theoretical Background

This section states, as provable propositions, why the dephasing ablation works and
at which circuit positions it can work at all. The required background is undergraduate
quantum mechanics: density operators, projection operators, unitary transformations and
commutators.

Dephasing is *not* unitary, and describing it needs the language of quantum channels;
Section 3.1 builds that language from scratch. What this section actually *uses*,
however, is the single operation of knocking out the off-diagonal entries of a density
matrix with a set of projection operators, and projection operators with completeness
are standard undergraduate material. Every deduction from Section 3.3 onwards therefore
needs nothing beyond that. Readers already familiar with channels can skip to 3.3;
for the general theory see @nielsen2010.

== Density operators and quantum channels

*Pure and mixed states.* The state of a quantum system is described by a *density
operator* $rho$: a positive semi-definite operator with trace $1$. If
$rho^2 = rho$ (equivalently $op("Tr") rho^2 = 1$) then $rho = ket(psi) bra(psi)$ is a
*pure state*; otherwise it is a *mixed state*. A pure state encodes maximal knowledge
of the system; a mixed state encodes ignorance.

*Why mixed states are unavoidable here.* Two situations in this work require them:
(i) after dephasing is applied to a quantum state the result is no longer pure; and
(ii) noise on real hardware also makes states mixed. Neither can be expressed with a
state vector $ket(psi)$ alone.

*Quantum channels.* Once a system couples to its environment, or is measured, its
evolution is no longer unitary. The general tool for such evolution is a *quantum
channel*: a linear map $cal(E)$ taking density operators to density operators that is
(i) *trace-preserving*: $op("Tr") cal(E)(rho) = op("Tr") rho$; and
(ii) *completely positive*: applying $cal(E)$ to only part of a larger system still
yields a legitimate density operator---no negative probabilities appear.
The second condition is what distinguishes a genuine quantum channel from an
arbitrary positive map, and is why it is physically realisable.
Together the two conditions define a *CPTP map* (completely positive
trace-preserving map), the standard definition of a physically implementable
quantum operation @nielsen2010.

*The Kraus representation theorem.* Every CPTP map can be written as
$ cal(E)(rho) = sum_i K_i rho K_i^dagger, quad sum_i K_i^dagger K_i = I, $
where the $K_i$ are the *Kraus operators* of the channel. The representation is not
unique, but its existence is equivalent to being CPTP. Nothing below uses the
technical details of complete positivity beyond this representation.

== Computational-basis dephasing is classicalisation

*Definition (computational-basis dephasing).* For a system of $n$ qubits let
$P_b = ket(b) bra(b)$ be the rank-one projection onto a computational basis state
($b$ ranges over all $n$-bit strings, and $sum_b P_b = I$). Define
$ cal(E)(rho) = sum_b P_b rho P_b . $

Reading this entrywise: multiplying on the left by $P_b$ keeps only row $b$, and
multiplying on the right by $P_b$ keeps only column $b$; after summing, only the
diagonal survives:
$ cal(E)(rho) = op("diag")(rho), $
that is, *every off-diagonal entry is set to zero*. This is a CPTP map whose Kraus
operators are simply $K_b = P_b$, since $sum_b P_b^dagger P_b = sum_b P_b = I$.

*Physical meaning.* An off-diagonal entry $rho_(i j)$ with $i != j$ encodes the
*phase relation* between basis states $ket(i)$ and $ket(j)$---the source of quantum
interference. Zeroing the off-diagonal entries therefore *removes the system's entire
capacity to interfere*, and its behaviour degenerates to a classical probability
distribution. This is exactly the classicalising operator $op("cl")$ of Tucci
@tucci2012: applying $op("cl")$ to the nodes of a quantum Bayesian network collapses
the whole network to a classical Bayesian network.

*Why this makes an ideal ablation tool.* An ablation can only claim to isolate a
single variable if it changes exactly one thing. $cal(E)$ does precisely that: it
leaves the diagonal untouched, hence leaves every computational-basis measurement
probability untouched, and removes only the quantumness itself. The model, the data
and the parameter count are all unchanged.

== When dephasing is invisible: monomial matrices

The next question is whether inserting $cal(E)$ at a given circuit position changes
the measurement outcome. The answer depends on what gates follow it.

*Definition (monomial matrix).* A square matrix $U$ is *monomial* if every row and
every column contains *exactly* one non-zero entry. If $U$ is also unitary those
non-zero entries must have modulus $1$, so $U$ can be written as
$ U = D_phi Pi, quad D_phi = op("diag")(e^(i phi_1), dots, e^(i phi_d)), $
where $Pi$ is a permutation matrix.

*Lemma 1.* If $U$ is monomial then $U P_b U^dagger = P_(pi(b))$, where $pi$ is the
basis permutation induced by $Pi$.

*Proof.* From $U = D_phi Pi$,
$ U ket(b) = D_phi Pi ket(b) = D_phi ket(pi(b)) = e^(i phi_(pi(b))) ket(pi(b)) . $
Hence
$ U P_b U^dagger = (e^(i phi_(pi(b))) ket(pi(b))) (e^(-i phi_(pi(b))) bra(pi(b))) = P_(pi(b)) . $
Note that the two phases cancel automatically by conjugation. This happens because
the projection is rank one, and it is the crux of the lemma.

*Theorem 1 (commutation).* If $U$ is monomial then for *every* $rho$
$ cal(E)(U rho U^dagger) = U cal(E)(rho) U^dagger . $

*Proof.* By the definition of $cal(E)$ and Lemma 1,
$ cal(E)(U rho U^dagger) = sum_b P_b U rho U^dagger P_b . $
Writing $P_b = U U^dagger P_b U U^dagger$ (valid since $U$ is unitary) gives
$ = sum_b U (U^dagger P_b U) rho (U^dagger P_b U)^dagger U^dagger
  = U [sum_b P_(pi^(-1)(b)) rho P_(pi^(-1)(b))] U^dagger . $
Since $pi$ is a bijection, letting $b$ run over all basis states also lets
$pi^(-1)(b)$ run over all of them, so the bracket is exactly $cal(E)(rho)$.

The proof uses nothing but a re-indexing of a sum: *no assumption whatsoever is made
about $rho$*.

*Corollary ($op("CX")$ commutes).* The controlled-NOT gate $op("CX")$ maps $ket(b)$
to $ket(b')$, where $b'$ is $b$ with bit $t$ flipped---a *permutation*, hence a
monomial matrix with all phases $phi = 0$. By Theorem 1, $op("CX")$ commutes with
$cal(E)$. The same argument holds for $X$, $Z$, $S$, $T$, $op("CZ")$, $op("SWAP")$
and $R_Z$: each is either a permutation or diagonal.

*Counterexample ($R_Y$ does not commute).* By the Euler identity
$exp(-i theta Y / 2) = I cos(theta / 2) - i Y sin(theta / 2)$,
$ R_Y(theta) = mat(cos(theta / 2), -sin(theta / 2); sin(theta / 2), cos(theta / 2)) . $
When $sin(theta / 2) != 0$ *and* $cos(theta / 2) != 0$ the first row contains *two*
non-zero entries, violating the definition of a monomial matrix, so $R_Y$ does not
commute with $cal(E)$; the same holds for $R_X$ and for the Hadamard gate $H$.

*A correction forced by the formalisation.* This section originally stated only the
$sin(theta / 2) != 0$ condition. But at $theta = pi$ we have $R_Y = mat(0, -1; 1, 0)$,
which *is* monomial (a permutation matrix times $-1$) and does commute with dephasing.
The precise statement is that $R_Y(theta)$ is monomial *if and only if* $theta in pi bb(Z)$.
The Lean formalisation (`not_isMonomial_RY` in `formal/Dephasing.lean`) uses exactly the
two-condition form.

*A necessary sharpening.* Earlier project documents state that dephasing must be
inserted "before a layer containing $R_Y / R_Z$". The precise statement is that
*$R_Z$ commutes with dephasing on its own* (it is diagonal, hence monomial), and that
what makes such a layer effective is the $R_Y$ inside it. Numerically, the commutator
is $0.000 times 10^0$ for $R_Z(0.7)$ and $3.221 times 10^(-1)$ for $R_Y(0.7)$.

== Terminal dephasing is invisible to measurement

*Theorem 2.* Split the circuit into a unitary part $U$ followed by a part $V$ built
*only* from monomial gates (for instance only $op("CX")$), and measure in the
computational basis. Then inserting dephasing *between* $U$ and $V$ leaves every
measurement probability unchanged: $P_a (i) = P_b (i)$ for all $i$.

*Proof.* The final states of the two arrangements are
$ rho_a = V cal(E)(U rho_0 U^dagger) V^dagger, quad rho_b = V (U rho_0 U^dagger) V^dagger . $
By Theorem 1, applied to $V$ (which is monomial),
$rho_a = cal(E)(V U rho_0 U^dagger V^dagger) = cal(E)(rho_b)$. A computational-basis
measurement reads the diagonal, $P(i) = rho_(i i)$, and $cal(E)$ *preserves the
diagonal*, so
$ P_a (i) = [cal(E)(rho_b)]_(i i) = [rho_b]_(i i) = P_b (i) . $

*Special case.* Taking $V = I$ (nothing follows) immediately gives: *dephasing placed
at the very end of the circuit leaves the measurement probabilities completely
unchanged.*

#block(inset: (x: 1em), fill: rgb("#fff4e5"), radius: 2pt)[
  *This is the easiest step of the whole experimental design to get wrong, and
  getting it wrong raises no error---it silently yields the wrong conclusion.*
  Placing dephasing at the end of the circuit produces a difference at the level of
  numerical error, which then reads as "quantumness contributes nothing".
  The value measured in this project is $1.4 times 10^(-17)$: a floating-point
  artefact, not a physical quantity.

  *It is a predicted zero, not a failed experiment.* When reporting, one must state
  that both the terminal arrangement and the "middle, followed only by $op("CX")$"
  arrangement differ by a zero guaranteed by Theorem 2, rather than by a quantity too
  small to measure.
]

== A minimal counterexample: why order matters

Consider a single qubit in the initial state
$ket(+) = (ket(0) + ket(1)) / sqrt(2)$, with gate $R_Y(theta)$ and $theta = pi / 4$.

*Path A (apply $R_Y$, then dephase).* The amplitudes are
$ R_Y(theta) ket(+) = 1/sqrt(2) mat(c - s; s + c), quad c = cos(theta / 2), quad s = sin(theta / 2) . $
Dephasing (keeping only squared moduli on the diagonal) gives
$ P^((A)) = ((1 - sin theta) / 2, (1 + sin theta) / 2) . $

*Path B (dephase first, then apply $R_Y$).* The density operator of $ket(+)$ becomes
$cal(E)(rho) = I / 2$, the maximally mixed state, after dephasing. The maximally mixed
state is invariant under every unitary: $R_Y (I / 2) R_Y^dagger = I / 2$. Hence
$ P^((B)) = (1 / 2, 1 / 2) . $

*The difference.*
$ |P^((A))_0 - P^((B))_0| = |(1 - sin theta) / 2 - 1 / 2| = sin theta / 2 . $
At $theta = pi / 4$ this is $1 / (2 sqrt(2)) = 0.353553$.

This is the smallest example in which order matters: path B yields an uninformative
uniform distribution, because dephasing turned $ket(+)$ into the maximally mixed
state, which carries no directional information at all.

*Numerical check.* An independent implementation measures
$P^((A)) = (0.146447, 0.853553)$ and $P^((B)) = (0.500000, 0.500000)$, differing by
$0.353553$, in agreement with the closed form.

== Consequences for the experimental design

The theorems above turn "where should dephasing go?" into a question with a correct
answer. The theoretical expectations are:

#figure(
  table(
    columns: (auto, 1fr, auto),
    table.header([*Insertion point*], [*Theoretical expectation*], [*Misreading if done wrong*]),
    [Very end of the circuit (just before measurement)], [Difference $approx 0$ (guaranteed by Theorem 2)], ["quantumness contributes nothing"],
    [Middle, followed only by $op("CX")$], [Difference $approx 0$ (guaranteed by Theorem 2)], ["quantumness contributes nothing"],
    [Middle, followed by $R_Y$], [Difference of order $0.01$ to $0.1$], [---],
  ),
  caption: [Theoretical expectations for the three insertion points. The first two rows are zeros guaranteed by a theorem, not failed experiments.],
)

The measured values in this project (5 qubits, maximum absolute difference over the
32-dimensional probability vector) are:

#figure(
  table(
    columns: (auto, auto),
    table.header([*Insertion point*], [*Measured maximum difference*]),
    [Very end (just before measurement)], [$1.388 times 10^(-17)$],
    [Middle, followed only by 10 $op("CX")$ gates], [$1.388 times 10^(-17)$],
    [Middle, followed by a full layer (contains $R_Y$)], [$bold(0.05023467)$],
  ),
  caption: [Measurement agrees with the theorems. The first two rows differ from the third by 15 orders of magnitude---exactly the gap between a zero guaranteed by a theorem and a real physical effect.],
)

*Independence of the numerical check.* The third row above was produced by two
independent routes: the channel implementation in `dev/qbn5_encoding.py`, and
`theory/verify/t5_commutator_placement.py`, which builds the $32 times 32$ density
matrix directly. Both give *bit-identical* $0.05023467$ (total variation distance
$0.19299447$). All 25 commutativity checks pass; for the four (control, target)
combinations of $op("CX")$, and for $op("CZ")$ and $op("SWAP")$,
$max |D U - U D|$ is $0.000 times 10^0$.

*A caveat for real-hardware runs.* The theorems of this section assume an *exact*
dephasing channel. On real hardware dephasing is implemented by a delay, and during
that delay $T_1$ amplitude damping acts alongside $T_2$ dephasing. $T_1$ changes the
*diagonal* of the density matrix---that is, it changes measurement probabilities---so
the corollary "terminal dephasing is bit-identical to no dephasing" *fails* on real
hardware. That deviation is itself a measurable hardware property rather than an
experimental error, and it is a tension that simply does not exist in simulation.

== Applying the theorems to our own circuit

Theorems 1 and 2 are abstract. Applied to the quantum layer of this study
(Section 4.2), they immediately fix the expectation for all four ablation arms---
*these four arms are not four arbitrary experimental settings, they are direct
corollaries of the theorems*.

The quantum layer here is: $R_Y(theta_i)$ angle encoding, then ring $op("CX")$
entanglement, then a trainable $[R_Y(phi), R_Z(lambda)]$ layer. That trainable layer
*contains $R_Y$*, and this is precisely what decides whether the ablation can be
observed at all.

#figure(
  table(
    columns: (auto, 1fr, 1fr),
    table.header([*Arm*], [*Where dephasing is inserted*], [*Which theorem fixes the expectation*]),
    [A], [nowhere (all-quantum baseline)], [---],
    [B], [after angle encoding, *before* the trainable layer], [Theorem 1: $R_Y$ follows, so it is *observable*],
    [C], [very end of the circuit, before measurement], [Theorem 2 with $V = I$: *necessarily unobservable*],
    [D], [after encoding, but equal-purity depolarising instead of dephasing], [control: mixes the state but keeps interference],
  ),
  caption: [The four ablation arms and the theorem behind each. The only difference between arms B and C is whether $R_Y$ follows.],
)

So the "arm C is bit-identical to arm A" measured in Section 6.2 is not a surprise;
it is the prediction of Theorem 2. And the flattened predictive distribution of arm B
is the other side of Theorem 1 ($R_Y$ does not commute). *Theory and experiment are
two faces of the same thing in this study*: the theorems first supply falsifiable
expectations, the experiments then supply numbers, and the next subsection reconciles
the two item by item.

== Numerical verification of the theory

Every proposition above has an independent numerical check. The scripts are
`theory/verify/t5_commutator_placement.py` (*25/25 checks pass*) and
`theory/verify/t4_kraus_dephasing.py`.

#figure(
  table(
    columns: (auto, 1fr, auto),
    table.header([*Proposition*], [*How it is checked*], [*Result*]),
    [Lemma 1 (monomial permutation)], [compare both routes on every basis operator $ket(i) bra(j)$], [$0.000 times 10^0$],
    [Theorem 1 (commutation)], [as above, plus the same commutator lifted to the superoperator (the linear map induced on density matrices)], [$0.000 times 10^0$],
    [Corollary ($op("CX")$ commutes)], [4 (control, target) pairs, $op("CZ")$, $op("SWAP")$], [all $0.000 times 10^0$],
    [Converse of Theorem 1 ($R_Y$)], [$H$, $R_Y(0.7)$, $R_X(0.7)$], [$5.0 times 10^(-1)$, $3.221 times 10^(-1)$, $3.221 times 10^(-1)$],
    [$R_Z$ does commute (sharpening)], [$R_Z(0.7)$], [$0.000 times 10^0$],
    [Superoperator commutator], [$16 times 16$ matrix at $n = 2$], [$0$ for $op("CX")$; $1.288435$ for $R_Y$],
    [Theorem 2 (terminal, middle+CX invisible)], [rerun the three insertion points on this circuit], [$0.000 times 10^0$],
    [Third setting of Theorem 2 (observable)], [independent $32 times 32$ density-matrix implementation], [*$0.05023467$*],
    [Total variation distance], [$0.5 sum_i |Delta p_i|$], [$0.19299447$],
  ),
  caption: [Numerical verification of the theory. The last two rows agree bit-for-bit with the output of the project script `dev/qbn5_encoding.py`.],
)

*Independence of the check.* The verification script does *not* use the channel
implementation from `dev/qbn5_encoding.py`; it builds the $32 times 32$ density matrix
directly (`theory/verify/dmtools.py`). Two fully independent routes give bit-identical
values $0.05023467$ and $0.19299447$---the strongest cross-check in this section, and
in the whole dephasing ablation.

*Scope of the verification (stated explicitly).* The table above verifies propositions
on the *simulator* side. Real hardware (Tuna-17 on Quantum Inspire) follows a separate
protocol, described in Section 4.3 and Section 6.2. There, $T_1$ amplitude damping
breaks the corollary "terminal dephasing is bit-identical"; that breakdown is itself a
measurable hardware property rather than a failure of the theorems above (see the
caveat at the end of Section 3.6).

*Machine-checked proof of the theorems (Lean 4).* The table above reconciles the
propositions with the simulator numerically. Because the results of this section are
finite-dimensional matrix identities, a second and stronger check is available: they
can be handed to a *proof assistant*, a program that accepts a mathematical statement
only once every logical step has been supplied and checked mechanically, leaving no
room for a step that is merely plausible. We used Lean 4. Three facts suffice to read
the result. (i) `formal/Dephasing.lean` compiles under Lean 4.34.0 with mathlib, the
standard mathematics library, and contains eleven proved statements. (ii) Lean's
keyword `sorry` marks a step admitted without proof; the file contains none, so no
step is skipped or assumed. (iii) Lean can print, for any proved statement, the
complete list of foundational assumptions its proof rests on (the `#print axioms`
command). For each of the six statements we audited, that list is exactly `propext`,
`Classical.choice` and `Quot.sound`---the three axioms on which ordinary mathematics
already rests---and nothing else: no extra assumption, no borrowed lemma and no
hidden hypothesis entered the argument.

What is checked is the mathematical content of this section, not a numerical shadow
of it. The file fixes the dephasing channel and the monomial matrices as definitions,
proves the re-indexing lemmas for multiplication on either side, and derives Theorem 1,
its permutation-matrix corollary (the CX case) and Theorem 2. The six audited
statements are those three results together with `isMonomial_diagonal`,
`not_isMonomial_RY` and `not_isMonomial_RY_pi_div_four`. The last two are the negative
half of Section 3.3: the formalisation proves that $R_Y(theta)$ is *not* monomial at
generic angles, in exactly the two-condition form $sin(theta / 2) != 0$ and
$cos(theta / 2) != 0$ used in the text, and proves the concrete case
$theta = pi slash 4$ of Section 3.5 separately. The positive theorems and the
counterexample that delimits them are therefore both machine-checked, and
`formal/Dephasing.lean` is commented so that it can be read alongside this section.

= Method

== System architecture

@fig:pipeline shows the complete pipeline.

#figure(
  image("figs/arch.svg", width: 100%),
  caption: [
    System architecture. The classical front end (static embedding, then principal component analysis, PCA)
    emits a $k$-dimensional feature vector to the quantum layer: angle encoding
    $theta_i = 2 arcsin sqrt(x_i)$, a ring $op("CX")$ entangler, and a trainable
    $R_Y times R_Z$ block repeated $L$ times. Measurement reads only the first 3
    qubits ($2^3 = 8$ basis patterns, independent of $n$ and $L$), and a classical
    readout layer maps them to 8 classes. Lower left: the cross-validation
    protocol. The expanded panel marks where the dephasing channel of the
    ablation is inserted---it must precede a layer containing $R_Y$, otherwise
    the effect is unobservable (measured probability change $1.4 times 10^(-17)$).
  ],
) <fig:pipeline>

== Quantum layer

The state space of $n$ qubits has dimension $2^n$. The circuit of this work has
three parts:

+ *Angle encoding*: apply $R_Y(theta_i)$ to each qubit, where
  $theta_i = 2 arcsin sqrt(x_i)$, so that the measurement probability equals the
  input value $x_i$ exactly.
+ *Entangling layer*: a ring of $op("CX")$ gates
  ($q_0 -> q_1 -> dots -> q_(n-1) -> q_0$).
+ *Trainable rotation layers*: one $R_Y$ and one $R_Z$ per qubit.

== Dephasing ablation

The Kraus operators of the dephasing channel @nielsen2010 are
$ K_0 = ket(0) bra(0), quad K_1 = ket(1) bra(1) $,
and its action is
$ cal(E)(rho) = K_0 rho K_0^dagger + K_1 rho K_1^dagger $,
whose effect is to zero the off-diagonal entries of the density matrix.
In the sense of Tucci's classicalising operator $op("cl")$ @tucci2012, this is
exactly the map that projects a quantum node back onto a classical Bayesian network.

#block(inset: (x: 1em), fill: rgb("#fff4e5"), radius: 2pt)[
  *A critical experimental-design trap*: if dephasing is applied at the *very end*
  of the circuit (immediately before measurement) it has no effect whatsoever on
  the measurement outcome, because:
  (a) a computational-basis measurement reads only the diagonal entries;
  (b) $op("CX")$ is a basis permutation and therefore *commutes* with
  computational-basis dephasing.
  The locally measured change in probability is $1.4 times 10^(-17)$ (that is, $0$).
  Dephasing must be inserted *before a layer that contains $R_Y$ (or $R_X$, $H$)*
  for the effect to be observable (measured $0.0502$).
  $R_Z$ is a unitary block-diagonal matrix and *commutes* with dephasing, so
  inserting it alongside leaves the measurement outcome unchanged (see Theorem 5.5)---
  which is also why "the position of dephasing does not matter" turns from a trap
  into a *prediction guaranteed to be zero*.
]

== Cross-validation protocol

*Cross-validation* here means computing every quantum-circuit result twice, on two
independently written simulators, and requiring the two answers to agree---a check on
the implementation, not the statistical resampling scheme that shares the name.
Every quantum-circuit result is computed on both CUDA-Q and an independently
implemented pure-NumPy state-vector simulator.
The maximum absolute error between the two probability vectors is required to be
below $10^(-10)$. The measured value depends on the circuit, so we list it item by item:

#figure(table(
  columns: (auto, 1fr, auto),
  table.header([*Circuit*], [*Comparison*], [*max $abs(Delta P)$*]),
  [Reproduction pipeline], [CUDA-Q vs pure-NumPy reference], [$4.16 times 10^(-17)$],
  [Largest capacity-scan circuit (250 gates)], [CUDA-Q vs torch differentiable simulator], [$3.47 times 10^(-18)$],
  [Ablation circuit (5 qubits)], [CUDA-Q vs density-matrix simulator], [$8.33 times 10^(-17)$],
  [Largest capacity-scan circuit (250 gates)], [CUDA-Q vs q01], [$4.16 times 10^(-16)$],
), caption: [Cross-validation of every quantum-circuit result against an independent implementation. The criterion is $10^(-10)$; the worst of the four circuits is $4.16 times 10^(-16)$, about $1.9$ times the double-precision machine epsilon.])

The q01 row is the worst case ($4.16 times 10^(-16)$, about $1.9$ times the
double-precision machine epsilon); the other three are all of order $10^(-17)$.
*All of them lie more than six orders of magnitude below the criterion.*

#block(inset: (x: 1em), fill: rgb("#eef6ff"), radius: 2pt)[
  *Implementation notes* (all measured, not inferred):
  + CUDA-Q provides no native Windows wheel, so it must run inside WSL2 (Windows
  Subsystem for Linux 2).
  + The measurement bitstrings returned by `cudaq.sample()` are big-endian,
    whereas the state-vector indices of `cudaq.get_state()` are little-endian.
    Converting between them requires a bit-reversal permutation, *not* `array[::-1]`.
  + The syntax for a multi-controlled gate is `ry.ctrl(theta, [c0, c1], target)`,
    with the *angle placed first*.
]

= Experimental Design

== Research questions and decision rules

#figure(table(
  columns: (auto, 1fr, 1fr),
  [*ID*], [*Question*], [*Pre-registered decision rule*],
  [RQ1 (research question 1)], [As the trainable capacity of the quantum circuit grows, does performance rise monotonically or is there a breakdown point?],
        [If performance is non-monotonic in capacity and the peak location depends on circuit depth, then H1 is supported.],
  [RQ2 (research question 2)], [By how much does dephasing (classicalisation) degrade calibration quality?],
        [If the lower bound of the 95\% confidence interval for the increase in ECE exceeds $0$, and exceeds the residual error of temperature scaling, then H2 is supported.],
), caption: [Research questions and the decision rules fixed before the runs. Stating them in advance is what makes a negative outcome a result rather than a reinterpretation.])

== Evaluation metrics

Beyond accuracy we report:
negative log-likelihood (NLL), the Brier score (the mean squared error of the
predicted probabilities against the true labels),
expected calibration error (ECE, $M = 10$ equal-width bins) together with reliability
diagrams (plots of claimed confidence against observed accuracy), and an uncertainty
decomposition into predictive entropy and mutual information.

#block(inset: (x: 1em), fill: rgb("#fff4e5"), radius: 2pt)[
  *The defence point for a fair comparison*: temperature scaling---dividing the
  model's output scores by a single fitted constant, which softens or sharpens the
  predicted distribution---does not change the highest-scoring label, so it is a
  means of improving calibration at zero cost in accuracy.
  Any calibration advantage of the quantum layer *must beat the temperature-scaled
  baseline*, otherwise the conclusion does not hold.
]

== Statistical protocol

Each configuration is repeated with $5$ random seeds, and we report the mean and the
standard deviation.
The capacity scan uses seeds $0$--$4$; the dephasing ablation uses seeds
$7, 21, 42, 84, 168$.
Both seed sets are fixed in code, and the data generator is fixed to seed $12345$,
so results are reproducible bit for bit across processes and across devices.
We state explicitly that $5$ seeds are not sufficient for rigorous statistical
inference, and therefore we do not use $p$ values as primary evidence; we report
effect sizes and confidence intervals instead.

= Results

== Capacity cliff

We scan the $(n, L)$ two-dimensional grid under a *fixed readout rule*: qubit count
$n$ from $3$ to $10$, circuit depth $L$ from $1$ to $8$, with each configuration
repeated across $5$ seeds.
The readout always projects the basis patterns of the first $3$ qubits onto
$8$ classes, independently of $n$ and $L$; increasing the qubit count therefore
increases the *available input dimensionality and state space*, not the resolution
of the readout.

#figure(
  image("figs/grid.svg", width: 100%),
  caption: [Test accuracy and calibration error over the $(n, L)$ grid (means of $5$ seeds).
    Panels (a) and (b) are heat maps; the numbers inside the cells are exact values and
    light-grey cells indicate configurations that have not been run.
    Panel (c) shows fixed-depth slices, directly testing the dependence of accuracy on qubit count.],
) <fig:cliff>

#include "tables/capacity_en.typ"

Three observations:

+ *Depth is the dominant driver, and there is no breakdown within the scanned range.*
   Test accuracy rises with depth for every $n$, and shows no decline even at $L = 8$;
   training accuracy rises as well (up to $0.79$). This contradicts the expectation of a
   "capacity cliff" and equally contradicts the expectation of a barren plateau.
+ *Test accuracy decreases with qubit count---for configurations in which capacity is
  genuinely used.*
   The *peak* of each $n$ (the maximum over depth) decreases monotonically from $n = 4$:
   $0.625 -> 0.622 -> 0.598 -> 0.576 -> 0.565 -> 0.524 -> 0.521$;
   the fixed-$L = 8$ slice gives the same sequence.
   The low value at $n = 3$ is structural---$8$ classes need at least a $3$-qubit
   projective readout, and that point is exactly saturated.
   *Shallower slices ($L$ no greater than $6$) do not show this trend*: there the model
   has not yet made full use of its capacity, and differences between configurations are
   masked by under-optimisation. The trend appears only at depths where capacity is
   genuinely used.
+ *More qubits is not merely worse, it is also less stable.*
   The seed-to-seed standard deviation of $n = 10$ at $L = 4$ is $0.130$,
   whereas $n = 3$ and $n = 4$ have only $0.076$ and $0.061$ respectively.

There is a methodological consequence that we must point out: *this trend would be
misjudged as holding in general on a sparse grid.*
When we earlier scanned only $n$ in $3, 4, 6, 8, 10$, it appeared monotone at both
$L = 6$ and $L = 8$; after adding $n = 5, 7, 9$, several slices with $L$ no greater
than $6$ became non-monotonic (for example, at $L = 6$ the value $0.572$ for $n = 7$
exceeds $0.545$ for $n = 6$). The claim is therefore restricted to the peak and to the
deepest slice.

Within the scope of our search we found no prior work reporting this phenomenon:
a conjunctive search over "quantum classifier", "qubit number" and "accuracy" returns
zero hits. What prior work reports is the $(Q, L)$ scaling protocol and
non-monotonicity along a single axis; what this work adds is the complete
two-dimensional grid under a *fixed readout rule*, together with this downward trend.

== Calibration ablation

The four arms are trained under *the same model, the same data and the same number of
trainable parameters* ($20$ angles) for the same number of steps ($800$), with each arm
repeated across $5$ seeds; the only difference is the inserted channel and its position.
The dephasing and depolarising arms have their *mean purity* matched (purity is
$op("Tr")(rho^2)$: it equals $1$ for a pure state and decreases as the state becomes
mixed; target purity $0.0742$; depolarising rate $p = 0.5657$, agreeing with the
closed-form solution to $10^(-15)$).

#figure(table(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  table.header([*Arm*], [*Accuracy*], [*ECE*], [*NLL*], [*Mean max prob.*], [*KL vs uniform*], [*State purity*]),
  [A no channel (fully quantum)], [0.3207], [0.1079], [1.8510], [0.2357], [0.0652], [1.0000],
  [B dephasing (after encoding)], [0.2300], [0.0993], [2.0558], [0.1307], [0.0000], [0.0449],
  [C dephasing (end of circuit)], [0.3207], [0.1079], [1.8510], [0.2357], [0.0652], [0.1230],
  [D depolarising (after encoding)], [0.2633], [0.1123], [2.0199], [0.1511], [0.0065], [0.0742],
), caption: [Calibration ablation. Arm C is bit-for-bit identical to arm A on every predictive metric, yet its state purity is $0.1230$ against $1.0000$: a computational-basis measurement reads only the diagonal entries, so dephasing at the end of the circuit changes the state but no observable outcome.])

Three points are worth making:

+ *Dephasing at the end has no effect at all on the measurement statistics.*
  Every predictive metric of arm C is bit-for-bit identical to arm A
  ($max abs(Delta P) = 0.000 times 10^0$), yet the state purities of the two differ by
  more than a factor of eight ($0.1230$ against $1.0000$). This is the direct consequence
  of "a computational-basis measurement reads only the diagonal entries" together with
  "$op("CX")$ is a basis permutation and commutes with computational-basis dephasing":
  dephasing changes the state, but changes no observable measurement outcome.
+ *Front-end dephasing crushes the model into an uninformative predictor.*
  The mean maximum probability of arm B is $0.1307$, which for $8$ classes is
  $1 slash 8$; the KL divergence (Kullback--Leibler divergence, a measure of how much two
  distributions differ) of its mean predictive distribution from the uniform
  distribution is $0.0000$; and the per-qubit $Z$ variance falls from $0.0226$ to
  $0.0001$ (roughly one part in $226$).
  Its ECE is in fact *lower* ($0.0993$ against $0.1079$), but this is an artefact of
  uniform predictions: for the same arm the NLL degrades from $1.8510$ to $2.0558$ and
  the Brier score from $0.8104$ to $0.8690$.
  *ECE alone cannot be taken as evidence of improved calibration.*
+ *The paired difference is not significant.* The ECE difference of $B - A$ is
  $-0.0086$ with a $95%$ confidence interval of $plus.minus 0.0340$, which covers $0$;
  the accuracy difference is $-0.0907$ ($plus.minus 0.0600$).
  Hence *H2 does not hold*: dephasing did not improve calibration, it destroyed information.

== Hardware verification

Everything on the simulation side rests on the assumption that dephasing is an
*exact* channel. Section 3.6 already noted that this assumption fails on real hardware,
and that *the size of the failure is itself a measurable hardware property*.
This subsection measures it -- and the first thing it measures is the scale.

*Protocol.* The hardware is QuTech's *Tuna-17*: $17$ transmons in a ninja-star topology,
with a native gate set that contains $op("CZ")$ but not $op("CX")$.
The $5$-qubit ring circuit of this study has *no* one-to-one mapping onto that topology
(the graph contains no $5$-cycle), so it is routed with $op("SWAP")$ gates before submission.
After routing, the compiled circuits of all five arms are *identical*
($op("CX") = 10$, $op("SWAP") = 2$, depth $18$, $42$ gates);
the only difference between arms A and C is five `wait` instructions -- a clean controlled comparison.
Each arm contributes $8$ samples, $40$ circuits in total, at $8192$ shots each.
The bit order is measured rather than assumed: applying an $X$ gate to $q_0$, $q_2$ and $q_4$
returns `00001`, `00100` and `10000` respectively, so the platform's classical bit order
is reversed into the $q_0$-leftmost convention used here.

One point about the statistical protocol has to be stated. The comparison is made in
*the classifier's $8$-class readout space* (the readout is taken over the first $3$ logical
qubits), and the observable is the *mean* $max abs(Delta P)$ over $8$ samples,
so the null hypothesis must be the distribution
of that same $8$-sample mean. Using a single-sample null systematically understates the
power of the test and turns a real effect into an insignificant one.
Every $p$ value below therefore uses the former: arm A's measured distribution is treated as
the population, two independent $8192$-shot draws are taken from it, and the procedure is
repeated $2 times 10^4$ times with $8$ samples averaged each time.
The null is thus $max abs(Delta P) = 0.00910 plus.minus 0.00109$ (95th percentile $0.01097$).

#figure(table(
  columns: (auto, auto, auto, auto, auto, auto),
  table.header([*Arm*], [*Delay (cycles)*], [*$max abs(Delta P)$*], [*TVD*], [*Ratio*], [*$p$*]),
  [A no delay], [$(0, 0)$], [---], [---], [---], [---],
  [B1 dephasing (after encoding)], [$(1, 0)$], [0.00943], [0.01620], [1.04], [0.366],
  [B4 dephasing (after encoding)], [$(4, 0)$], [0.01170], [0.01945], [1.29], [0.014],
  [C1 dephasing (end of circuit)], [$(0, 1)$], [0.01057], [0.01718], [1.16], [0.093],
  [C4 dephasing (end of circuit)], [$(0, 4)$], [0.00966], [0.01807], [1.06], [0.295],
), caption: [The four delayed arms against the undelayed arm A on Tuna-17, $8$ samples and
  $8192$ shots per arm. The ratio is with respect to the pure shot-noise null ($0.00910$).
  The largest value, $1.29$, is also the only marginal entry under a Bonferroni correction
  across four arms ($alpha = 0.05 slash 4 = 0.0125$), and it does not survive that correction.],) <fig:hw-ablation>

*A same-circuit, different-time drift control.* The easiest entry in that table to
over-read is B4 at $1.29$. Deciding whether it is physics needs a control with no variable
at all: the circuit of the $tau = 0$ block is gate-for-gate identical to arm A, and was only
submitted about an hour later at a different shot count. Subtracting the two gives
$max abs(Delta P) = 0.01624$ ($8$ samples, median $0.01683$), and *every one of the four
delayed arms is less than half of that*: B1 is $0.48$ times it, B4 $0.55$, and C1 and C4
$0.49$ each. In other words, *the difference this device produces when it simply runs the
identical circuit again is larger than the entire effect of the four delayed arms*.

*Why $8192$ shots could not see it.* This is a question of statistical *power*, not of the
channel being absent. cQASM, the assembly language in which circuits are submitted
to Quantum Inspire, defines the `wait` parameter as a number whose
unit is "the duration of a single-qubit gate on the backend, i.e. an execution cycle",
and the Quantum Inspire knowledge base likewise says "idle the qubit ... for the given
number of cycles". The Tuna backends have a native single-qubit gate time of $20$ ns and the `wait` argument
is a count of those cycles, so $1$--$4$ cycles cover only a small fraction of $T_2$ and the induced deviation is
correspondingly small; the noise floor at $8192$ shots is $0.00910$, which is $3.5$ times
coarser than the $0.00260$ the next subsection reaches at $65536$ shots.

The meaning of this result is therefore a *qualification*, not a refutation: at $8192$ shots
the resolution of the four-arm protocol is limited by the device's own reproducibility, and
that limit is larger than the effect it is trying to measure. It therefore cannot be used to
test the hardware corollary of Theorem 2.
The next subsection raises the shot count eightfold and sweeps the delay across five orders
of magnitude -- and the signal appears.

== Hardware delay dose response

Pushing the delay from $1$ execution cycle to $65536$ (about $1.6$ ms, spanning both $T_2$ and
$T_1$) yields a logarithmic dose-response curve covering five orders of magnitude.
Each point uses the same batch of samples and the same circuit, changing only the `wait`
parameter, at $65536$ shots per circuit -- eight times the previous subsection, so the noise
falls by a factor $1 slash sqrt(8) approx 0.35$.
A gate-by-gate comparison of the compiled circuits confirms that the gate sequence is identical
at every $tau$ ($42$ operations in all) and that the only difference is the value of `wait`;
$tau = 0$ is gate-for-gate identical to arm A.

*Why delays cannot be batched together.* The idle time of `wait` is paid *once per shot*:
a circuit's execution time is proportional to $"shots" times tau$ ($tau = 65536$ already costs
$1.31$ ms per shot, accumulating to hundreds of seconds over $65536$ shots), while the platform's
`job_execution_time_limit` is a $300$-second budget for the *whole batch*.
Binding large-$tau$ circuits together with small-$tau$ ones makes the entire batch time out and
be cancelled --- which cost the first version of this study $13$ circuits. The correct unit is
one circuit per batch.

One artefact has to be ruled out first. The cQASM specification notes that `wait` *also*
acts as a barrier, telling the scheduler that instructions may not be reordered across it,
so "adding a `wait`" and "adding idle time" are not the same operation.
In this design the `wait` is placed *immediately before the measurement*, after which there
are no gates left to reorder; the barrier property therefore has nothing to act on, and the
only physical effect is idle time. This is also why the dose sweep uses the tail position
rather than the front position.

There are two null hypotheses here, and the second one is the right one.
(a) *A pure shot-noise null*: arm $tau = 0$'s measured distribution is treated as the population
and two independent $65536$-shot draws are taken from it. This answers "how small a deviation is
statistically resolvable", and gives $0.00261$.
(b) *Same-circuit, different-time repeatability*: the $tau = 0$ blocks of the two sweeps are
*gate-for-gate identical* circuits at the same shot count, submitted at different times.
Subtracting them gives the spread this device actually produces when it simply runs the identical
circuit again: $0.01553$ ($8$ samples).
Real hardware is not random only through shots -- drift and calibration move it too -- so (b) is
six times larger than (a).

#include "tables/tau_dose_en.typ"

#figure(
  image("figs/tau_dose.svg", width: 100%),
  caption: [Delay dose response. Panel (a) is the deviation from the undelayed circuit: the blue
    band is the $95%$ interval of the pure shot-noise null and the red dashed line is this
    device's *same-circuit different-time repeatability* of $0.01553$. Panel (b) is the
    probability that the readout returns all zeros. Both curves are governed by $T_1$ relaxation
    and approach their ceiling near $tau = 65536$.],
) <fig:tau-curve>

*No effect smaller than (b) can be attributed to the delay*, and this changes the reading
directly. The points $tau = 1$, $4$ and $16$ are $0.29$, $0.26$ and $0.46$ times the repeatability:
they *pass* the shot-noise test ($1.73$, $1.54$ and $2.72$ times) while sitting entirely inside the
spread of the device's own repeats. Reporting only the shot-noise null would have presented these
three points as the channel already appearing.
The first undeniable signal is $tau = 64$ (about $1.3$ microseconds): $1.55$ times the
repeatability and $9.27$ times the shot noise, reaching $16$ times the repeatability by
$tau = 1024$.

The shape of the curve is the shape of $T_1$ relaxation: $max abs(Delta P)$ rises from $0.644$ at
$tau = 4096$ through $0.735$ at $16384$ to $0.811$ at $65536$, while $P(00000)$ rises from
$0.657$ through $0.748$ to $0.823$. The $0.823$ rather than $1$ is the readout *assignment-fidelity* ceiling
(the probability that a qubit prepared in $ket(0)$ is in fact read out as $0$),
i.e. the state has fully relaxed to $|0 dots 0 angle$.
The rise between $1024$ and $4096$ cycles fixes the $T_1$ scale at about $10^3$ cycles, i.e. tens
of microseconds, consistent with a typical superconducting transmon.

For the corollary in Section 3.6 this is a *direct* observation: the theorem assumes exact
dephasing, whereas the hardware delivers dephasing *plus* relaxation, and the relaxation fully
dominates the measurement distribution at the $T_1$ scale.

= Discussion

== Three honest statements

+ This work *does not claim* quantum advantage. The state vector of $5$ qubits occupies
  only $512$ bytes and is fully classically simulable.
+ This work *does not claim* that the quantum layer retains the semantic information of
  its input. The front end is a $256$-dimensional static embedding that is reduced in
  dimensionality before entering the quantum layer; the information bottleneck is by design.
+ This work *does not claim* to beat large models. The baselines are small models of
  comparable parameter count.

== Why the hybrid architecture has no advantage on this task

What is exponential is the *state space*; what is polynomial is the *number of knobs*.
The density matrix of $5$ qubits has $32^2 - 1 = 1023$ real degrees of freedom, yet the
circuit of this work has only $10$ trainable angles---the dimension of the reachable
subspace is far smaller than that of the ambient space.

More fundamentally, *trainability* and *classical intractability* conflict with each
other @anschuetz2024 @cerezo2025 @gilfuster2024.
Shallow, weakly entangling circuits can be trained, but their low entanglement entropy
makes them efficiently simulable by tensor-network methods; deep, highly entangling
circuits are classically intractable, but they run into barren plateaus and cannot be
trained.

(Note: what is stated here is the general form of that trade-off as found in the
literature, *not* a measurement of this work.
Within the scanned range of this work we did *not* observe a barren plateau---training
accuracy rises with depth up to $0.84$, and an independent check by the theory group
rules it out as well. Our result is that "depth works, width does not", and its
mechanism is closer to the growth of the effective dimension outpacing what the data
and the readout can support @caro2022generalization @abbas2021power @abbas2022effective.)

Consequently, on tasks without provable structure (such as generic semantic
classification), no advantage should be expected from a quantum decision layer.
The hybrid architecture itself is not at fault; the choice of task is.

== Three methodological traps (by-products of this work)

The following three items are not propositions we set out to prove; they are traps we
ran into during the experiments and for which we retained numbers.
We write them down because in this field they are easier to repeat than any single
experimental result of ours.

+ *Pooled correlation and partial correlation can give opposite conclusions.*
  Plotting the effective dimension $bar(d)$ against test accuracy gives a pooled
  correlation coefficient of $+0.678$; after controlling for circuit depth $L$, the
  partial correlation becomes $-0.256$.
  The reason is that $bar(d)$ and $L$ are highly collinear, while accuracy is driven
  mainly by $L$. Looking only at a scatter plot, or only at the pooled coefficient,
  yields the opposite conclusion that "larger dimension is more accurate".
+ *"$5$ seeds" is not the same as "$5$ independent trainings".*
  Across $5$ seeds, arms B and D have a standard deviation of $0.0000$ for test
  accuracy, ECE, NLL and state purity alike;
  arms A and C have a test-accuracy standard deviation of $0.0483$.
  When Adam trains a low-dimensional loss surface of this kind, different initial
  points are absorbed by the same attractor.
  Confidence intervals estimated from seed-to-seed variance therefore *systematically
  underestimate* the true uncertainty---which is also why this work does not treat
  $p$ values as primary evidence.
+ *An ablation matched on an average must be re-checked on the evaluation set.*
  We matched the channel strengths of dephasing and depolarisation by mean purity: on
  the training set, the achieved value agrees with the target to the order of
  $10^(-15)$. But on the *test set*, the mean purity of arm B is $0.0449$ and that of
  arm D is $0.0742$, a difference of $-0.0292$.
  The reason is that the purity of dephasing varies *sample by sample* (it depends on
  the state of that sample), whereas that of depolarisation is approximately fixed;
  a single average purity does not constrain any individual sample.
  Any ablation that claims "the two channels are equally classical" on the strength of
  one purity number must re-check that claim on the evaluation set.

= Conclusion

The contribution of this work is not to demonstrate quantum advantage, but to provide
(i) a fully verifiable hybrid pipeline (cross-validated against an independent
implementation: the reproduction pipeline at $4.16 times 10^(-17)$,
the largest capacity-scan circuit at $3.47 times 10^(-18)$ and the ablation circuit at
$8.33 times 10^(-17)$, and further validated end-to-end through the cloud API of
Quafu (the quantum cloud platform of the Chinese Academy of Sciences; API stands for
application programming interface)
on its official simulator, where the circuit after transpilation (translation into
the device's native gate set) agrees with the golden vector (an independently
computed reference result) to $8.88 times 10^(-16)$), and
(ii) a set of controlled ablation designs that use the dephasing classicalisation
operator as the sole variable *within a single model* and scan the $(Q, L)$
two-dimensional grid under a *fixed readout rule*.
Prior work has established scaling protocols on each individual axis @vyskubov2026,
and parameter-matched, calibration- and noise-aware benchmarks @gillani2026;
what this work adds is the intersection of the two, together with dephasing as a
specific variable.

We argue that at NISQ scale (noisy intermediate-scale quantum), what the field of
quantum machine learning lacks most is
not new circuits, but *rigorous measurement that treats the quantum component itself as
a controlled variable*.

= Acknowledgements

We thank our advisor and the unit that provided computing resources.
The real-hardware experiments were carried out on the *Tuna-17* superconducting
processor of *Quantum Inspire*, the quantum computing platform operated by
*QuTech* (Delft University of Technology and TNO); we thank QuTech for providing
free access to quantum hardware.

= References

#bibliography("refs.bib", style: "ieee")
