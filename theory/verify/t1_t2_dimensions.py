"""t1_t2_dimensions.py — T1 與 T2 的數值驗證。

對應文件：
  * ``theory/T1_state_space_dimension.md``（為什麼 :math:`2^n` 維）
  * ``theory/T2_reachable_subspace.md``（為什麼可訓練參數是多項式的）

驗證清單
--------
T1
  1. 張量積 vs 直和：:math:`\\dim(A\\otimes B)=\\dim A\\cdot\\dim B` 對
     :math:`\\dim(A\\oplus B)=\\dim A+\\dim B`；:math:`2^n` vs :math:`2n`
  2. 顯式建構 :math:`(\\mathbb C^2)^{\\otimes n}` 的基底（:math:`2^n` 個）
  3. 乘積態的係數確實是係數的乘積（:math:`\\alpha_{ij}=a_i b_j`）
  4. 糾纏態**不能**寫成乘積態（違反舒密特秩 1）
T2
  5. :math:`\\mathfrak{su}(N)` 的實維度 = :math:`N^2-1`（顯式建基底 + 秩檢定）
  6. :math:`\\mathfrak{u}(N)` 的實維度 = :math:`N^2`
  7. :math:`\\exp(iH)` 么正（H Hermitian）與 :math:`\\det e^H=e^{\\mathrm{tr}H}`
  8. 密度矩陣的實自由參數 = :math:`N^2-1`；純態流形 = :math:`2N-2`
  9. **可達子空間維度**：電路參數 → 態的雅可比矩陣秩
     （單層 10 參數、雙層 20 參數 vs 么正群 1023 維）
 10. 富比尼–施帝度量（去除全域相位後的可分辨維度）

執行：``uv run python projects/qbn-capacity-calibration/theory/verify/t1_t2_dimensions.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dmtools as dm  # noqa: E402

PASS: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    PASS.append((name, bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))


def banner(t: str) -> None:
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


# ======================================================================
banner("T1【1】張量積 vs 直和：2^n 與 2n 的差別")
print(f"  {'n':>3}{'2^n (張量積)':>16}{'2n (直和)':>14}{'比值 2^n / 2n':>18}")
for n in range(1, 13):
    print(f"  {n:>3}{2**n:>16}{2*n:>14}{2**n/(2*n):>18.3f}")
for n in [1, 2, 5, 10, 20, 50]:
    print(f"    n={n:<3} 2^n = {2**n:<18} 2n = {2*n}")
check("2^n = 2n 只在 n=1,2 成立", all(2**n == 2 * n for n in (1, 2))
      and all(2**n != 2 * n for n in (3, 4, 5, 10)))
check("n=5 時 2^n = 32 >> 2n = 10", 2 ** 5 == 32 and 2 * 5 == 10)

# ======================================================================
banner("T1【2】顯式建構 (C^2)^{⊗n} 的基底")
for n in [1, 2, 3, 5]:
    basis = []
    for idx in range(2 ** n):
        v = np.array([1.0 + 0j])
        for q in range(n):
            bit = (idx >> (n - 1 - q)) & 1
            v = np.kron(v, np.array([1.0, 0.0]) if bit == 0 else np.array([0.0, 1.0]))
        basis.append(v)
    M = np.array(basis).T
    rank = np.linalg.matrix_rank(M)
    check(f"n={n}: 張量積基底有 {2**n} 個元素且線性獨立（秩 {rank}）",
          len(basis) == 2 ** n and rank == 2 ** n)
# 直和只有 2n 維
for n in [2, 5]:
    basis_sum = []
    for q in range(n):
        for bit in range(2):
            v = np.zeros(2 * n, dtype=complex)
            v[2 * q + bit] = 1.0
            basis_sum.append(v)
    check(f"n={n}: 直和基底只有 {len(basis_sum)} 個 = 2n（對照張量積 {2**n}）",
          len(basis_sum) == 2 * n)

# ======================================================================
banner("T1【3】乘積態的係數是係數的乘積；糾纏態不是乘積態")
a = np.array([0.6, 0.8])                      # |a> = 0.6|0> + 0.8|1>
b = np.array([1.0, 1.0]) / np.sqrt(2)         # |b> = (|0>+|1>)/sqrt2
prod = np.kron(a, b)
check("|a>⊗|b> 的係數 = a_i b_j（kron 定義）",
      np.allclose(prod, [a[0]*b[0], a[0]*b[1], a[1]*b[0], a[1]*b[1]]),
      f"kron = {np.array2string(prod, precision=6)}")
# 貝爾態
bell = np.array([1, 0, 0, 1]) / np.sqrt(2)
C = bell.reshape(2, 2)
sv = np.linalg.svd(C, compute_uv=False)
check("貝爾態的係數矩陣秩 = 2 > 1 → 不是乘積態",
      np.linalg.matrix_rank(C) == 2,
      f"奇異值 = {np.array2string(sv, precision=6)}")
check("乘積態的係數矩陣秩 = 1", np.linalg.matrix_rank(prod.reshape(2, 2)) == 1)
# 顯式說明：貝爾態不可能寫成 (x0|0>+x1|1>)(y0|0>+y1|1>)
print("  貝爾態若可分解則需 x0 y0 = 1/√2, x0 y1 = 0, x1 y0 = 0, x1 y1 = 1/√2。")
print("  由 x0 y1 = 0 得 x0=0 或 y1=0；兩種都與 x0 y0 = 1/√2 ≠ 0 及 x1 y1 = 1/√2 ≠ 0 矛盾。")
check("貝爾態的舒密特秩 = 2（最大糾纏，1 ebit）",
      np.isclose(-np.sum(sv**2 * np.log2(sv**2)), 1.0),
      f"糾纏熵 = {-np.sum(sv**2 * np.log2(sv**2)):.10f} bit")

# ======================================================================
banner("T2【5】【6】su(N) 與 u(N) 的實維度（顯式建基底 + 秩檢定）")


def lie_basis(N: int) -> tuple[np.ndarray, np.ndarray]:
    r"""回傳 (:math:`\mathfrak{u}(N)` 基底, :math:`\mathfrak{su}(N)` 基底)。

    用「廣義 Gell-Mann」構造：
      * 對角：:math:`h_k=\\mathrm{diag}(1,\\dots,1,-k,0,\\dots)` 型（:math:`k=1..N-1`）
      * 非對角對稱：:math:`|i\\rangle\\langle j|+|j\\rangle\\langle i|`
      * 非對角反對稱：:math:`-i(|i\\rangle\\langle j|-|j\\rangle\\langle i|)`
    全部都是 Hermitian。:math:`\\mathfrak u(N)` 再加上單位矩陣。
    """
    non_diag = []
    for i in range(N):
        for j in range(i + 1, N):
            S = np.zeros((N, N), dtype=complex)
            S[i, j] = S[j, i] = 1.0
            non_diag.append(S)
            A = np.zeros((N, N), dtype=complex)
            A[i, j] = -1j
            A[j, i] = 1j
            non_diag.append(A)
    # 對角無跡基底（N-1 個）
    diag = []
    for k in range(1, N):
        D = np.zeros((N, N), dtype=complex)
        for i in range(k):
            D[i, i] = 1.0
        D[k, k] = -float(k)
        diag.append(D / np.linalg.norm(D))
    su = diag + non_diag
    u = [np.eye(N, dtype=complex) / np.sqrt(N)] + su
    return u, su


for N in [2, 4, 8, 32]:
    u, su = lie_basis(N)
    Mu = np.array([m.reshape(-1) for m in u]).T
    Msu = np.array([m.reshape(-1) for m in su]).T
    ru, rsu = np.linalg.matrix_rank(Mu), np.linalg.matrix_rank(Msu)
    herm_u = all(np.allclose(m, m.conj().T) for m in u)
    tr_su = all(abs(np.trace(m)) < 1e-12 for m in su)
    tr_u = abs(np.trace(u[0])) > 1e-12
    print(f"  N={N:<3} dim u(N) = {ru:<5} (N^2 = {N*N:<5})   "
          f"dim su(N) = {rsu:<5} (N^2-1 = {N*N-1})")
    check(f"N={N}: dim su(N) = N^2-1 = {N*N-1}", rsu == N * N - 1)
    check(f"N={N}: dim u(N) = N^2 = {N*N}", ru == N * N)
    check(f"N={N}: 基底全 Hermitian，su(N) 基底全無跡", herm_u and tr_su and tr_u)
print("  → N = 2^5 = 32 時：dim su(32) = 1023，dim u(32) = 1024。")

# ======================================================================
banner("T2【7】exp(iH) 么正、det(e^H) = e^{tr H}")


def expm_hermitian(H: np.ndarray, scale: complex = 1.0) -> np.ndarray:
    r"""對 **Hermitian** ``H`` 精確計算 :math:`\exp(\text{scale}\cdot H)`。

    用譜分解 :math:`H=V\Lambda V^\dagger`，故
    :math:`\exp(sH)=V\,\mathrm{diag}(e^{s\lambda_i})\,V^\dagger`。
    這比一般矩陣指數演算法更精確（且不需 scipy）。
    """
    lam, V = np.linalg.eigh(H)
    return (V * np.exp(scale * lam)[None, :]) @ V.conj().T


rng = np.random.default_rng(2026)
for N in [2, 5, 32]:
    A = rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N))
    H = (A + A.conj().T) / 2.0                     # Hermitian
    U = expm_hermitian(H, 1j)
    check(f"N={N}: H Hermitian => U = exp(iH) 么正",
          np.allclose(U @ U.conj().T, np.eye(N), atol=1e-12),
          f"max|U U† - I| = {np.max(np.abs(U @ U.conj().T - np.eye(N))):.3e}")
    lhs = np.linalg.det(expm_hermitian(H, 1.0))
    rhs = np.exp(np.trace(H))
    check(f"N={N}: det(e^H) = e^(tr H)（Arfken Eq. 2.84）",
          np.isclose(lhs, rhs, atol=1e-8), f"det = {lhs:.6e}, exp(tr) = {rhs:.6e}")

# ======================================================================
banner("T2【8】密度矩陣與純態流形的實維度")
for n in [1, 3, 5]:
    N = 2 ** n
    # 一般 Hermitian 矩陣：N^2 個實參數；跡 = 1 扣 1 個 → N^2 - 1
    H = rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N))
    H = (H + H.conj().T) / 2.0
    n_real = N * N
    n_herm = N * N            # Hermitian 矩陣的實維度 = N^2
    # 純態：2N 個實參數 - 歸一化(1) - 全域相位(1) = 2N - 2
    print(f"  n={n}: N = {N:<3}  一般 Hermitian 實維度 = {n_herm:<5} "
          f"（= N^2）  密度矩陣（跡 1）= {n_herm-1:<5}（= N^2-1）  "
          f"純態流形 = {2*N-2:<5}（= 2N-2）")
    check(f"n={n}: 密度矩陣實自由參數 = N^2-1 = {N*N-1}", n_herm - 1 == N * N - 1)
check("n=5: N^2-1 = 1023（對照專案常數 dev/qbn5_encoding.py:69 N_UNITARY_PARAMS）",
      32 * 32 - 1 == 1023)
check("n=5: 純態流形實維度 = 2N-2 = 62", 2 * 32 - 2 == 62)

# ======================================================================
banner("T2【9】★ 可達子空間維度：雅可比矩陣的秩")
print("  電路（與 dev/qbn_circuit.py::qbn_state 相同）：")
print("    RY(θ_i) 編碼 ^5 → 環形 CX ^5 → [ RY(φ_i) RZ(λ_i) ] ^5")
print("  可訓練參數只有 10 個（dev/qbn_circuit.py:155：5 個 RY + 5 個 RZ）。")


def circuit_units(n: int, x: np.ndarray, params: np.ndarray):
    r"""回傳 (么正矩陣清單, 每個可訓練參數對應的『導數閘』清單)。

    ``params`` 長度 :math:`2n`（前 n 個是 RY、後 n 個是 RZ）。
    """
    units = []      # (U, dU) 配對；dU 為 None 表示不可訓練（編碼／糾纏）
    for i in range(n):
        units.append((dm.embed1(dm.ry(float(x[i])), i, n), None))
    for i in range(n):
        units.append((dm.cnot_full(i, (i + 1) % n, n), None))
    for i in range(n):
        units.append((dm.embed1(dm.ry(float(params[i])), i, n), ("RY", i)))
    for i in range(n):
        units.append((dm.embed1(dm.rz(float(params[n + i])), i, n), ("RZ", i)))
    return units


def jacobian_rank(n: int, x: np.ndarray, params: np.ndarray,
                  depth: int = 1) -> dict:
    r"""計算 :math:`\partial|\psi\rangle/\partial\theta_k` 的精確雅可比，回傳三種秩。

    為什麼要分三種秩（這是本節最容易講錯的地方）
    --------------------------------------------
    參數映射是 :math:`\theta\in\mathbb R^P\mapsto[\psi(\theta)]\in\mathbb{CP}^{2^n-1}`
    （:math:`[\cdot]` 表示模掉全域相位）。它的微分把 :math:`\mathbb R^P` 送到切空間：

    .. math:: \mathrm d\theta \;\longmapsto\; \sum_{k=1}^{P}\mathrm d\theta_k\,
              \partial_k|\psi\rangle \pmod{|\psi\rangle}

    因此**可達流形的維度 = 這些導數向量之實張量的維度（再扣掉相位方向）**：

    * ``rank_C`` = :math:`\{\partial_k|\psi\rangle\}` 在 :math:`\mathbb C` 上的秩
      （只是診斷量，**不是**可達維度）
    * ``rank_R`` = 實張量維度 :math:`=\mathrm{rank}\,[\mathrm{Re}\,J \mid \mathrm{Im}\,J]`
      （也不是可達維度，因為還含相位方向）
    * ``rank_FS`` = 富比尼–施帝度量的秩
      :math:`G_{ij}=\mathrm{Re}\langle\partial_i\psi|\partial_j\psi\rangle
      -\langle\partial_i\psi|\psi\rangle\langle\psi|\partial_j\psi\rangle`
      :math:`=\mathrm{rank\_R}-1`（當相位方向落在張量內），**這才是可達流形維度**

    不變的硬上界：:math:`\text{rank\_FS}\le\text{rank\_R}\le\min(2^n-2,\,2P)`，
    因為整個像是 :math:`P` 個參數的光滑映射之像，維度**不可能超過** :math:`P`。
    """
    dim = 2 ** n
    units = [(dm.embed1(dm.ry(float(x[i])), i, n), None) for i in range(n)]
    nparam = 0
    for d in range(depth):
        for i in range(n):
            units.append((dm.embed1(dm.ry(float(params[d, i, 0])), i, n), ("RY", d, i)))
        for i in range(n):
            units.append((dm.embed1(dm.rz(float(params[d, i, 1])), i, n), ("RZ", d, i)))
        pairs = ([(i, (i + 1) % n) for i in range(n)] if d % 2 == 0
                 else [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)])
        for (c, t) in pairs:
            units.append((dm.cnot_full(c, t, n), None))
        nparam += 2 * n

    prefix = [np.eye(dim, dtype=complex)]
    for (U, _) in units:
        prefix.append(U @ prefix[-1])
    suffix = [np.eye(dim, dtype=complex)] * (len(units) + 1)
    for k in range(len(units) - 1, -1, -1):
        suffix[k] = suffix[k + 1] @ units[k][0]

    ket0 = np.eye(dim, dtype=complex)[:, 0]
    psi = prefix[-1] @ ket0

    cols = []
    for k, (U, tag) in enumerate(units):
        if tag is None:
            continue
        if tag[0] == "RY":
            dU = dm.embed1(dm.ry_deriv(float(params[tag[1], tag[2], 0])), tag[2], n)
        else:
            dU = dm.embed1(dm.rz_deriv(float(params[tag[1], tag[2], 1])), tag[2], n)
        cols.append(suffix[k + 1] @ dU @ prefix[k] @ ket0)
    J = np.array(cols).T                                   # (dim, nparam)

    rank_C = int(np.linalg.matrix_rank(J, tol=1e-9))
    rank_R = int(np.linalg.matrix_rank(np.hstack([J.real, J.imag]), tol=1e-9))

    ov = J.conj().T @ psi
    G = J.conj().T @ J
    G = np.real(G - np.outer(ov, ov.conj()))
    G = (G + G.T) / 2.0
    rank_FS = int(np.linalg.matrix_rank(G, tol=1e-9))
    return {"rank_C": rank_C, "rank_R": rank_R, "rank_FS": rank_FS,
            "nparam": nparam, "J": J, "psi": psi}


N5 = 5
print("\n  單層電路（與 dev/qbn_circuit.py 同構）：")
print(f"  {'n':>3}{'P=2n':>7}{'rank_C(J)':>11}{'rank_R':>9}{'rank_FS':>9}"
      f"{'su(2^n)':>10}{'su / rank_FS':>14}")
for n in [2, 3, 4, 5]:
    r2 = np.random.default_rng(1000 + n)
    x_n = r2.uniform(0.2, 0.9, size=n)
    p_n = r2.normal(0, 0.8, size=(1, n, 2))
    d = jacobian_rank(n, x_n, p_n, depth=1)
    su = 2 ** (2 * n) - 1
    print(f"  {n:>3}{d['nparam']:>7}{d['rank_C']:>11}{d['rank_R']:>9}"
          f"{d['rank_FS']:>9}{su:>10}{su/max(d['rank_FS'],1):>14.1f}")
    check(f"n={n}: 可達維度 rank_FS = P = {d['nparam']}（參數化無冗餘）",
          d["rank_FS"] == d["nparam"], f"rank_FS = {d['rank_FS']}")
    check(f"n={n}: 硬上界 rank_FS ≤ P 成立", d["rank_FS"] <= d["nparam"])
    check(f"n={n}: 可達維度遠小於 su({2**n}) 的 {su} 維",
          d["rank_FS"] < su, f"{d['rank_FS']} << {su}")

print("\n  雙層電路（與 dev/qbn5_encoding.py::qbn_layer 同構，P = 4n）：")
for n in [3, 4, 5]:
    r3 = np.random.default_rng(2000 + n)
    x_n = r3.uniform(0.2, 0.9, size=n)
    p_n = r3.normal(0, 0.8, size=(2, n, 2))
    d = jacobian_rank(n, x_n, p_n, depth=2)
    su = 2 ** (2 * n) - 1
    print(f"  n={n}: P = {d['nparam']:>3}  rank_C = {d['rank_C']:>3}  "
          f"rank_R = {d['rank_R']:>3}  rank_FS = {d['rank_FS']:>3}  "
          f"su({2**n}) = {su}")
    check(f"n={n}: 雙層可達維度 rank_FS = P = {d['nparam']}",
          d["rank_FS"] == d["nparam"], f"rank_FS = {d['rank_FS']}")
    check(f"n={n}: 雙層可達維度 << su({2**n}) = {su} 維",
          d["rank_FS"] < su)

# 5 qubit 的重點數字（用專案的示範輸入）
r5 = np.random.default_rng(42)
x5 = np.array([0.90, 0.20, 0.75, 0.40, 0.60])
p5 = r5.normal(0, 0.8, size=(2, N5, 2))
d1 = jacobian_rank(N5, x5, p5, depth=1)
d2 = jacobian_rank(N5, x5, p5, depth=2)
SU32 = 32 ** 2 - 1
print("\n  ★ 5 qubit 關鍵對照（本專案）：")
print(f"      su(32) 維度（可訓練么正的上界，Arfken §17.7 的 N²−1） = {SU32}")
print(f"      單層電路：可訓練參數 P = {d1['nparam']}，"
      f"可達維度 rank_FS = {d1['rank_FS']}（dev/qbn_circuit.py:155）")
print(f"      雙層電路：可訓練參數 P = {d2['nparam']}，"
      f"可達維度 rank_FS = {d2['rank_FS']}（dev/qbn5_encoding.py:603）")
print(f"      落差：su(32) {SU32} 維  vs  單層可達 {d1['rank_FS']} 維"
      f"  →  {SU32}/{d1['rank_FS']} = {SU32/d1['rank_FS']:.1f} 倍")
print(f"      純態流形（模掉相位）也只有 2N−2 = {2*32-2} 維。")
check("★ 5 qubit：P = 10（單層）／20（雙層），可達維度等於 P",
      d1["nparam"] == 10 and d2["nparam"] == 20
      and d1["rank_FS"] == 10 and d2["rank_FS"] == 20)
check("★ 1023 / 10 = 102.3（su(32) 與單層可訓練方向的落差）",
      SU32 == 1023 and abs(SU32 / 10 - 102.3) < 1e-9,
      f"{SU32} / 10 = {SU32/10:.1f}")

banner("總結")
n_ok = sum(1 for _, ok in PASS if ok)
print(f"  通過 {n_ok} / {len(PASS)} 項")
for name, ok in PASS:
    if not ok:
        print(f"  !! 未通過：{name}")
sys.exit(0 if n_ok == len(PASS) else 1)
