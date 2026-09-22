"""t3_entanglement_barren.py — T3 的數值驗證。

對應文件：``theory/T3_trainability_vs_hardness.md``

要驗的三件事
------------
**(A) 體積律／佩吉值（Page value）**：對 :math:`n` qubit 的**隨機**純態，
子系統 :math:`A`（:math:`d_A=2^k`、:math:`d_B=2^{n-k}`、:math:`d_A\\le d_B`）
的平均糾纏熵是

.. math:: \\langle S\\rangle \\simeq \\log_2 d_A-\\frac{1}{2\\ln 2}\\frac{d_A}{d_B}
          = k-\\frac{1}{2\\ln 2}\\,2^{\\,2k-n}

本檔用 Haar 隨機雙 qubit 閘的磚牆電路（深度 :math:`L\\gtrsim 4n`）逼近 2-design，
驗證量到的熵收斂到上式。**注意：體積律的「上界」不是 :math:`\\min(k,n-k)`，
而是佩吉值**（差一個 :math:`1/(2\\ln2)` 的修正）——這是最容易講錯的地方。

**(B) 面積律 vs 體積律的 :math:`\\chi`  scaling**：結構化的環形 ansatz 在
:math:`L=1` 時只有 2 條跨越切口的邊，故 :math:`S\\le2`、:math:`\\chi=2^S\\le4`
**與 :math:`n` 無關**；而體積律的 :math:`\\chi=2^{\\,k-2^{2k-n}/(2\\ln2)}`
隨 :math:`n` **指數成長**。這才是「古典難不難」的真正分野。

**(C) Barren plateau 的**誠實**量測**：在 :math:`n\\le8`、:math:`L=4` 的環形
ansatz 上，梯度變異數**沒有**明顯的指數衰減。本檔把這個否定結果如實印出，
並說明它為什麼是預期中的（該電路不是 2-design、成本函數是局部的）。

執行：``uv run python projects/qbn-capacity-calibration/theory/verify/t3_entanglement_barren.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dmtools as dm  # noqa: E402

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "dev"))
from dev.qbn_sim import StateVectorSim  # noqa: E402

PASS: list[tuple[str, bool]] = []
INV_LN2 = 1.0 / np.log(2.0)


def check(name: str, ok: bool, detail: str = "") -> None:
    PASS.append((name, bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))


def banner(t: str) -> None:
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


def page_value(k: int, n: int) -> float:
    r"""佩吉值 :math:`k-\frac{1}{2\ln2}2^{\,2k-n}`（僅在 :math:`k\le n/2` 時用）。"""
    return k - (1.0 / (2.0 * np.log(2.0))) * 2.0 ** (2 * k - n)


def ring_edges(n: int, step: int = 1) -> list[tuple[int, int]]:
    r"""環上距離 ``step`` 的邊，去重且去掉退化（``gcd(step,n)>1`` 時會重複）。"""
    out = set()
    for i in range(n):
        j = (i + step) % n
        if i != j:
            out.add((min(i, j), max(i, j)))
    return sorted(out)


def build_ring(n: int, depth: int, params: np.ndarray, enc: np.ndarray) -> StateVectorSim:
    """angle encoding + depth 層 [RY,RZ,CX]（與 dev/qbn5_encoding.py::qbn_layer 同構）。"""
    sim = StateVectorSim(n)
    for i in range(n):
        sim.ry(float(enc[i]), i)
    for d in range(depth):
        for i in range(n):
            sim.ry(float(params[d, i, 0]), i)
            sim.rz(float(params[d, i, 1]), i)
        for (c, t) in ring_edges(n, 1 if d % 2 == 0 else 2):
            sim.cx(c, t)
    return sim


def embed2(U4: np.ndarray, q1: int, q2: int, n: int) -> np.ndarray:
    """把 :math:`4\\times4` 的雙 qubit 閘嵌入 :math:`2^n\\times2^n` 空間。"""
    dim = 2 ** n
    M = np.zeros((dim, dim), dtype=complex)
    mask = (1 << (n - 1 - q1)) | (1 << (n - 1 - q2))
    for i in range(dim):
        rest = i & ~mask
        a = (i >> (n - 1 - q1)) & 1
        b = (i >> (n - 1 - q2)) & 1
        for ap in range(2):
            for bp in range(2):
                v = U4[ap * 2 + bp, a * 2 + b]
                if v != 0.0:
                    M[rest | (ap << (n - 1 - q1)) | (bp << (n - 1 - q2)), i] += v
    return M


def haar_u4(rng: np.random.Generator) -> np.ndarray:
    """QR 分解取 Haar 隨機 U(4)。"""
    A = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    Q, R = np.linalg.qr(A)
    return Q * (np.diag(R) / np.abs(np.diag(R)))[None, :]


def random_brickwork_psi(n: int, depth: int, seed: int) -> np.ndarray:
    """磚牆式隨機雙 qubit 閘電路，回傳態向量。"""
    dim = 2 ** n
    U = np.eye(dim, dtype=complex)
    rng = np.random.default_rng(seed)
    for d in range(depth):
        pairs = ([(i, i + 1) for i in range(0, n - 1, 2)] if d % 2 == 0
                 else [(i, i + 1) for i in range(1, n - 1, 2)])
        for (q1, q2) in pairs:
            U = embed2(haar_u4(rng), q1, q2, n) @ U
    return U @ np.eye(dim, dtype=complex)[:, 0]


def entropy_k(psi: np.ndarray, k: int, n: int) -> float:
    return dm.vn_entropy(dm.partial_trace(dm.pure_dm(psi), list(range(k)), n))


# ======================================================================
banner("【A】體積律的**正確**參考值：佩吉值（Page value）")
N_R = 8
print(f"  n = {N_R}，隨機磚牆電路，深度 L 增加直到熵收斂（2-design）。")
print(f"  佩吉公式 <S> = k - 2^(2k-n)/(2 ln 2)\n")
print(f"  {'k':>3}{'佩吉值':>12}{'L=8':>10}{'L=16':>10}{'L=32':>10}{'L=64':>10}"
      f"{'min(k,n-k)':>13}")
DEPTHS_R = [8, 16, 32, 64]
rand_ent: dict[int, list[float]] = {}
for k in range(1, N_R // 2 + 1):
    row = [entropy_k(random_brickwork_psi(N_R, L, 1000 + L), k, N_R) for L in DEPTHS_R]
    rand_ent[k] = row
    print(f"  {k:>3}{page_value(k, N_R):>12.5f}"
          + "".join(f"{v:>10.5f}" for v in row)
          + f"{min(k, N_R-k):>13}")
print("\n  → 深隨機電路收斂到**佩吉值**，而不是 min(k, n-k)（差約 1/(2 ln 2) = 0.721）。")
for k in range(1, N_R // 2 + 1):
    check(f"k={k}: L=64 的熵收斂到佩吉值（誤差 < 0.05）",
          abs(rand_ent[k][-1] - page_value(k, N_R)) < 0.05,
          f"量到 {rand_ent[k][-1]:.5f} vs 佩吉 {page_value(k, N_R):.5f}")
check("k=n/2 時佩吉值 = 4 - 0.7213 = 3.2787（明顯小於 4）",
      abs(page_value(4, 8) - 3.2787) < 1e-3, f"{page_value(4, 8):.6f}")

# ======================================================================
banner("【B1】環形 ansatz 的面積律：S 飽和、與子系統大小無關")
N_AREA = 12
print(f"  n = {N_AREA}，環形 ansatz，量測前 k 個 qubit 的糾纏熵。")
print(f"  L=1 只有 2 條跨越切口的邊 → 面積律硬上界 S <= 2。\n")
rng = np.random.default_rng(2026)
encA = rng.uniform(0.2, 2.8, size=N_AREA)
pA = {L: rng.normal(0, 0.8, size=(max(L, 1), N_AREA, 2)) for L in (0, 1, 2, 4)}
print(f"  {'k':>3}{'佩吉值':>12}{'L=0':>10}{'L=1':>10}{'L=2':>10}{'L=4':>10}")
area: dict[int, list[float]] = {}
for k in range(1, N_AREA // 2 + 1):
    row = [build_ring(N_AREA, L, pA[L], encA).entanglement_entropy(list(range(k)))
           for L in (0, 1, 2, 4)]
    area[k] = row
    print(f"  {k:>3}{page_value(k, N_AREA):>12.5f}"
          + "".join(f"{v:>10.5f}" for v in row))
check("L=0（乘積態）：所有 k 的熵 = 0",
      all(abs(area[k][0]) < 1e-12 for k in area))
check("L=1：熵在**所有 k** 都不超過面積律上界 2（切口數）",
      all(area[k][1] <= 2.0 + 1e-9 for k in area),
      f"max over k = {max(area[k][1] for k in area):.6f}")
check("L=1：k=1 與 k=6 的熵差距 < 0.7 bit（飽和，不隨 k 成長）",
      abs(area[N_AREA // 2][1] - area[1][1]) < 0.7,
      f"S(k=1) = {area[1][1]:.5f}, S(k=6) = {area[N_AREA//2][1]:.5f}")
check("對照：佩吉值隨 k 線性成長，k=1 與 k=6 差距約 4.3 bit",
      page_value(N_AREA // 2, N_AREA) - page_value(1, N_AREA) > 4.0,
      f"佩吉差 = {page_value(N_AREA//2, N_AREA) - page_value(1, N_AREA):.5f}")

# ======================================================================
banner("【B2】★ 關鍵：chi = 2^S 隨 n 的 scaling")
print("  固定取「最大切口」k = n/2，比較兩種電路的鍵維度 chi = 2^S。")
print("  面積律（L=1，切口數 2）的 chi <= 4 **與 n 無關**；")
print("  體積律（佩吉值）的 chi = 2^(n/2 - 0.7213) **指數成長**。\n")

rngA = np.random.default_rng(11)
print(f"  {'n':>3}{'k=n/2':>7}{'環形 L=1 的 S':>16}{'環形 chi':>11}"
      f"{'佩吉 S':>10}{'佩吉 chi':>12}{'chi 比值':>11}")
chi_rows = []
for n in [4, 6, 8, 10, 12]:
    k = n // 2
    enc_n = rngA.uniform(0.2, 2.8, size=n)
    p_n = rngA.normal(0, 0.8, size=(1, n, 2))
    s_ring = build_ring(n, 1, p_n, enc_n).entanglement_entropy(list(range(k)))
    s_page = page_value(k, n)
    chi_r, chi_p = 2 ** s_ring, 2 ** s_page
    chi_rows.append((n, s_ring, chi_r, s_page, chi_p, chi_p / chi_r))
    print(f"  {n:>3}{k:>7}{s_ring:>16.5f}{chi_r:>11.3f}"
          f"{s_page:>10.5f}{chi_p:>12.3f}{chi_p/chi_r:>11.2f}")
check("環形 L=1 的 chi 在所有 n 都 <= 4（面積律，與 n 無關）",
      all(r[2] <= 4.0 + 1e-9 for r in chi_rows),
      f"max chi = {max(r[2] for r in chi_rows):.3f}")
check("佩吉 chi 隨 n 指數成長（n=12 時已 > 20）",
      chi_rows[-1][4] > 20, f"chi(n=12) = {chi_rows[-1][4]:.3f}")
check("兩者比值隨 n 單調成長（n=12 時超過 5 倍）",
      all(chi_rows[i][5] <= chi_rows[i + 1][5] for i in range(len(chi_rows) - 1))
      and chi_rows[-1][5] > 5,
      f"比值 n=4..12 = {[f'{r[5]:.2f}' for r in chi_rows]}")
print("\n  → 面積律讓張量網路（MPS）的 chi 是**常數**，矩陣乘積態可有效率收縮；")
print("    體積律的 chi 指數成長，古典模擬成本隨 n 爆掉。這是『古典難解』的定量內容。")

# ======================================================================
banner("【C】Barren plateau 的誠實量測（結果是**否定**的）")
print("  設定：n qubit、L=4 層環形 ansatz（隨機 RY/RZ），成本 C = <Z_0>（局部觀測量），")
print("        參數平移法取 dC/dtheta_1，對 150 組隨機參數估變異數。\n")
FIXED_L = 4
N_LIST = [2, 3, 4, 5, 6, 7, 8]
NSAMP = 150
rng2 = np.random.default_rng(7)
vars_by_n: dict[int, float] = {}
print(f"  {'n':>3}{'Var[dC/dtheta_1]':>20}{'log2(Var)':>13}{'2^(-n)':>14}")
for n in N_LIST:
    enc = rng2.uniform(0.2, 2.8, size=n)
    grads = []
    for _ in range(NSAMP):
        p = rng2.normal(0, np.pi, size=(FIXED_L, n, 2))
        th = float(p[0, 0, 0])

        def cost(t: float) -> float:
            q = p.copy()
            q[0, 0, 0] = t
            return build_ring(n, FIXED_L, q, enc).expectation_z(0)

        grads.append(0.5 * (cost(th + np.pi / 2) - cost(th - np.pi / 2)))
    v = float(np.var(grads))
    vars_by_n[n] = v
    print(f"  {n:>3}{v:>20.3e}{np.log2(v):>13.3f}{2.0**(-n):>14.3e}")
xs = np.array(N_LIST, dtype=float)
ys = np.array([np.log2(vars_by_n[n]) for n in N_LIST])
b, a = np.polyfit(xs, ys, 1)
print(f"\n  最小平方擬合 log2 Var = {a:.4f} + ({b:.4f})·n"
      f"   → 每個 qubit 乘上 2^({b:.4f}) = {2**b:.4f}")
print(f"  真正的 barren plateau 應該看到 b ≈ -1（即 2^(-n)）；實測 b = {b:.4f}。")
print("  → **否定結果**：在這個 n 與深度下，梯度變異數幾乎不隨 n 衰減，")
print("     沒有 barren plateau。這與理論預期一致：barren plateau 需要")
print("     電路接近 2-design（深且隨機）**且**成本函數是全域的；")
print("     我們的 ansatz 是淺層、局部、結構化的，兩者都不滿足。")
check("梯度變異數隨 n 遞減（方向正確，但幅度極小）",
      vars_by_n[N_LIST[0]] > vars_by_n[N_LIST[-1]],
      f"Var(n=2) = {vars_by_n[2]:.3e} -> Var(n=8) = {vars_by_n[8]:.3e}")
check("沒有觀測到指數衰減：|b| < 0.5（拒絕 barren plateau 假設）",
      abs(b) < 0.5, f"b = {b:.4f}（barren plateau 需 b ≈ -1）")
check("Var(n=2)/Var(n=8) < 10（不是指數級的落差）",
      vars_by_n[2] / vars_by_n[8] < 10,
      f"比值 = {vars_by_n[2] / vars_by_n[8]:.3f}")

# ======================================================================
banner("【D】權衡表：深度同時影響古典難度與訓練難度")
print(f"  {'L':>3}{'S_max (n=8,k=4)':>18}{'chi':>9}{'Var[dC] (n=5)':>17}"
      f"{'古典模擬':>11}{'可訓練':>10}")
n5 = 5
enc5 = rng2.uniform(0.2, 2.8, size=n5)
enc8b = rng2.uniform(0.2, 2.8, size=8)
for L in [0, 1, 2, 4, 8]:
    p8 = rng2.normal(0, 0.8, size=(max(L, 1), 8, 2))
    smax = build_ring(8, L, p8, enc8b).entanglement_entropy(list(range(4)))
    gs = []
    for _ in range(50):
        pp = rng2.normal(0, np.pi, size=(max(L, 1), n5, 2))
        th = float(pp[0, 0, 0])

        def c5(t: float) -> float:
            q = pp.copy()
            q[0, 0, 0] = t
            return build_ring(n5, max(L, 1), q, enc5).expectation_z(0)

        gs.append(0.5 * (c5(th + np.pi / 2) - c5(th - np.pi / 2)))
    vv = float(np.var(gs))
    print(f"  {L:>3}{smax:>18.5f}{2**smax:>9.3f}{vv:>17.3e}"
          f"{'容易':>11}{'可用' if vv > 1e-5 else '差':>10}")
print("\n  → 對本專案（n=5、L<=2）：chi <= 8（古典容易）且梯度沒有消失（可訓練）。")
print("    兩者都不構成量子優勢，也都不構成訓練病理；")
print("    因此 RQ1 的容量斷崖（若觀察到）必須用『表達力 vs 泛化』解釋，")
print("    而不是『古典難度』或『barren plateau』。")

banner("總結")
n_ok = sum(1 for _, ok in PASS if ok)
print(f"  通過 {n_ok} / {len(PASS)} 項")
for name, ok in PASS:
    if not ok:
        print(f"  !! 未通過：{name}")
sys.exit(0 if n_ok == len(PASS) else 1)
