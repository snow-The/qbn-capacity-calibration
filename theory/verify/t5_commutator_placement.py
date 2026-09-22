"""t5_commutator_placement.py — T5 的數值驗證。

對應文件：``projects/qbn-capacity-calibration/theory/T5_dephasing_commutator.md``

核心命題
--------
把去相位通道記為 :math:`\\mathcal D`、么正通道記為
:math:`\\mathcal U(\\rho)=U\\rho U^\\dagger`。本檔驗證：

1. **單閘層級**：若 :math:`U` 在計算基底是「么模仿塊矩陣」（monomial，
   即每列每行恰一個非零元——置換 × 對角相位），則
   :math:`[\\mathcal D,\\mathcal U]=0`。CNOT、CZ、SWAP、X、Z、S、T、:math:`R_Z`
   全部屬於此類。
2. **反例**：:math:`R_Y`、:math:`R_X`、:math:`H` **不**屬於此類，
   :math:`[\\mathcal D,\\mathcal U]\\neq0`。
3. **推論**：若去相位之後只接么模仿塊閘，量測分布**完全不變**
   （因為 :math:`\\mathcal D` 不改變對角元，而么模仿塊閘只是置換對角元）。
   → 這就是「去相位接在電路尾端量不到效果」的定理。
4. **明確實作的超算符交換子**（:math:`n=2` 時 :math:`16\\times16` 矩陣，
   可直接看到 :math:`[\\hat{\\mathcal D},\\hat{\\mathcal U}]` 的元素）。
5. **重現本地實測**（5 qubit QBN 電路，三種插入位置）：
   尾端、中間後接 CX、中間後接完整層。
6. 變分距離、受影響基底態個數、純度。

執行：``uv run python projects/qbn-capacity-calibration/theory/verify/t5_commutator_placement.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dmtools as dm  # noqa: E402

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "dev"))   # 讓 qbn5_encoding 的 `import qbn_sim` 成功
try:
    from dev.qbn_sim import StateVectorSim  # noqa: E402
    _HAS_SIM = True
except Exception as exc:  # pragma: no cover
    print(f"[warn] 無法載入 dev/qbn_sim.py：{exc}")
    _HAS_SIM = False

N = 5
PASS: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    PASS.append((name, bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))


def banner(t: str) -> None:
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


def is_monomial(U: np.ndarray, tol: float = 1e-12) -> bool:
    """么模仿塊矩陣：每列與每行恰有一個非零元（置換 × 對角相位）。"""
    return bool(np.all(np.sum(np.abs(U) > tol, axis=0) == 1)
                and np.all(np.sum(np.abs(U) > tol, axis=1) == 1))


def channel_commutator_norm(U: np.ndarray, rho0: np.ndarray, n: int) -> float:
    r"""用「對所有基底態取樣」的方式量 :math:`\|\mathcal D\mathcal U-\mathcal U\mathcal D\|`。

    做法：對一組探測密度矩陣 :math:`\rho`，比較
    :math:`\mathcal D(U\rho U^\dagger)` 與 :math:`U\mathcal D(\rho)U^\dagger`。
    因為兩者都是線性映射，若在基底 :math:`|i\rangle\langle j|` 上全部相等，
    則兩者作為超算符完全相等。此處對所有 :math:`|i\rangle\langle j|` 檢查。
    """
    dim = 2 ** n
    worst = 0.0
    for i in range(dim):
        for j in range(dim):
            E = np.zeros((dim, dim), dtype=complex)
            E[i, j] = 1.0
            lhs = dm.dephase(dm.apply_unitary(E, U), n)
            rhs = dm.apply_unitary(dm.dephase(E, n), U)
            worst = max(worst, float(np.max(np.abs(lhs - rhs))))
    return worst


# ----------------------------------------------------------------------
banner("【1】么模仿塊矩陣的判準：哪些閘與去相位交換？")
n_test = 3
gates = {
    "I": np.eye(2, dtype=complex),
    "X": dm._X,
    "Z": dm._Z,
    "S = diag(1,i)": np.diag([1.0, 1j]),
    "T = diag(1,e^{i pi/4})": np.diag([1.0, np.exp(1j * np.pi / 4)]),
    "RZ(0.7)": dm.rz(0.7),
    "H": dm._H,
    "RY(0.7)": dm.ry(0.7),
    "RX(0.7) = H RZ H": dm._H @ dm.rz(0.7) @ dm._H,
}
print(f"  {'單閘':<24}{'么模仿塊？':<12}{'max|D U - U D| (n=2, 全基底)':>34}")
results = {}
for name, g in gates.items():
    U2 = dm.embed1(g, 0, 2)
    norm = channel_commutator_norm(U2, None, 2)
    results[name] = (is_monomial(g), norm)
    print(f"  {name:<24}{str(is_monomial(g)):<12}{norm:>34.3e}")

for name in ["I", "X", "Z", "S = diag(1,i)", "T = diag(1,e^{i pi/4})", "RZ(0.7)"]:
    check(f"{name} 是么模仿塊且與去相位交換", results[name][0]
          and results[name][1] < 1e-14, f"max = {results[name][1]:.3e}")
for name in ["H", "RY(0.7)", "RX(0.7) = H RZ H"]:
    check(f"{name} 非么模仿塊且與去相位**不**交換", (not results[name][0])
          and results[name][1] > 1e-3, f"max = {results[name][1]:.3e}")

# ----------------------------------------------------------------------
banner("【2】CNOT 與計算基底去相位交換（專案要求的核心命題）")
for (c, t) in [(0, 1), (1, 0), (0, 2), (2, 1)]:
    U = dm.cnot_full(c, t, n_test)
    norm = channel_commutator_norm(U, None, n_test)
    check(f"CNOT(control={c}, target={t}) 與去相位交換", norm < 1e-14,
          f"max|D U - U D| = {norm:.3e}")
print("  註：CNOT 在計算基底是**置換矩陣**，置換矩陣是么模仿塊的特例，")
print("      故 D(U rho U^dag) = U D(rho) U^dag 對所有 rho 成立。")

# 也驗證 CZ / SWAP
CZ01 = np.diag([1, 1, 1, -1]).astype(complex)
norm_cz = channel_commutator_norm(CZ01, None, 2)
check("CZ 與去相位交換", norm_cz < 1e-14, f"max = {norm_cz:.3e}")
SWAP = dm.perm_full([0, 2, 1, 3], 2)
norm_sw = channel_commutator_norm(SWAP, None, 2)
check("SWAP 與去相位交換", norm_sw < 1e-14, f"max = {norm_sw:.3e}")

# ----------------------------------------------------------------------
banner("【3】明確實作的超算符交換子（n=2，16x16）")
D_sup = dm.superop_dephase(2)
RY_sup = dm.superop_unitary(dm.embed1(dm.ry(0.7), 0, 2))
CNOT_sup = dm.superop_unitary(dm.cnot_full(0, 1, 2))
comm_ry = dm.commutator(D_sup, RY_sup)
comm_cnot = dm.commutator(D_sup, CNOT_sup)
print("  [D, U_RY] 的 Frobenius 範數   = "
      f"{np.linalg.norm(comm_ry):.6f}   非零元素個數 = {int(np.sum(np.abs(comm_ry) > 1e-12))}")
print("  [D, U_CNOT] 的 Frobenius 範數 = "
      f"{np.linalg.norm(comm_cnot):.3e}   非零元素個數 = {int(np.sum(np.abs(comm_cnot) > 1e-12))}")
check("[D, U_CNOT] = 0（超算符層級）", np.allclose(comm_cnot, 0, atol=1e-14))
check("[D, U_RY] != 0（超算符層級）", np.linalg.norm(comm_ry) > 1e-3,
      f"||[D,U_RY]||_F = {np.linalg.norm(comm_ry):.6f}")

# ----------------------------------------------------------------------
banner("【4】最小反例：為什麼「先去相位」與「後去相位」不同？")
theta = np.pi / 4
# |+> 有同調性
plus = np.array([1, 1]) / np.sqrt(2)
rho_plus = dm.pure_dm(plus)
K0, K1 = dm.kraus_dephase_1q()
D1 = lambda r: K0 @ r @ K0.conj().T + K1 @ r @ K1.conj().T  # noqa: E731
R = dm.ry(theta)
path_A = dm.probs_from_rho(D1(dm.apply_unitary(rho_plus, R)))   # 先 RY 再去相位
path_B = dm.probs_from_rho(dm.apply_unitary(D1(rho_plus), R))   # 先去相位再 RY
print(f"  初態 |+>，θ = π/4，R_Y(θ) 與去相位的兩種順序：")
print(f"    路徑 A（先 R_Y 再去相位）機率 = [{path_A[0]:.6f}, {path_A[1]:.6f}]")
print(f"    路徑 B（先去相位再 R_Y）機率 = [{path_B[0]:.6f}, {path_B[1]:.6f}]")
print(f"    最大差 = {np.max(np.abs(path_A - path_B)):.6f}")
c_, s_ = np.cos(theta / 2), np.sin(theta / 2)
print("  解析：先去相位把 |+> 變成 I/2，而 I/2 在任何么正下都不變 → (1/2, 1/2)；")
print("        先 R_Y 則振幅 = ((c-s)/√2, (s+c)/√2)，")
print(f"        機率 = ((1-sinθ)/2, (1+sinθ)/2) = ({(1-np.sin(theta))/2:.6f}, "
      f"{(1+np.sin(theta))/2:.6f})（與上列路徑 A 相符）。")
print(f"  理論差 = |1/2 - (1-sinθ)/2| = sinθ/2 = {np.sin(theta)/2:.6f}")
check("兩種順序的機率不同（順序有意義）", np.max(np.abs(path_A - path_B)) > 0.3,
      f"max|dp| = {np.max(np.abs(path_A - path_B)):.6f}")
check("路徑 A 與解析式 ((1∓sinθ)/2) 相符",
      np.allclose(path_A, [(1 - np.sin(theta)) / 2, (1 + np.sin(theta)) / 2]),
      f"解析值 = [{(1-np.sin(theta))/2:.6f}, {(1+np.sin(theta))/2:.6f}]")
check("先去相位 → R_Y 的結果是 (1/2,1/2)（古典混態對 R_Y 不敏感）",
      np.allclose(path_B, [0.5, 0.5], atol=1e-14))

# ----------------------------------------------------------------------
banner("【5】重現本地實測：5 qubit QBN 電路的三種去相位插入位置")
print("  電路結構完全依照 dev/qbn5_encoding.py 的 qbn_layer（L178-192）：")
print("    |0>^5 -- RY(θ_i) 角度編碼 --+-- [ RY(φ) RZ(λ) ] -- [ 環形 CX ] --+--")
print("                                +---------- 重複 depth=2 次 ----------+")
print("    第 0 層接 RING_STEP1，第 1 層接 RING_STEP2（兩條 5-cycle 交替）。")
print("  輸入與權重取自 dev/qbn5_encoding.py::_demo_inputs（x5 固定、種子 42）。")
if _HAS_SIM:
    # --- 專案的示範輸入（直接 import，確保完全一致） --------------------
    try:
        from dev.qbn5_encoding import (  # noqa: E402
            _demo_inputs, N_UNITARY_PARAMS, N_QUBITS, RING_STEP1, RING_STEP2,
        )
        x5, weights = _demo_inputs()
        print(f"  [info] 已載入 dev.qbn5_encoding._demo_inputs，"
              f"N_UNITARY_PARAMS = {N_UNITARY_PARAMS}")
    except Exception as exc:
        print(f"  [warn] 無法 import qbn5_encoding（{exc}），改用硬編碼的示範輸入")
        x5 = np.array([0.90, 0.20, 0.75, 0.40, 0.60])
        rng0 = np.random.default_rng(42)
        weights = rng0.normal(0.0, 0.8, size=(2, N, 2))
        RING_STEP1 = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        RING_STEP2 = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]

    dim = 2 ** N
    ALL_Q = list(range(N))
    angles = 2.0 * np.arcsin(np.sqrt(np.asarray(x5, dtype=float)))
    RING = [RING_STEP1, RING_STEP2]

    def rot_block(d: int) -> list[np.ndarray]:
        """第 d 層的 5 個 RY + 5 個 RZ（weights[d,i,0]=RY, weights[d,i,1]=RZ）。"""
        out = []
        for i in range(N):
            out.append(dm.embed1(dm.ry(float(weights[d, i, 0])), i, N))
        for i in range(N):
            out.append(dm.embed1(dm.rz(float(weights[d, i, 1])), i, N))
        return out

    def cx_block(d: int) -> list[np.ndarray]:
        return [dm.cnot_full(c, t, N) for (c, t) in RING[d]]

    def apply_seq(Us: list[np.ndarray]) -> np.ndarray:
        U = np.eye(dim, dtype=complex)
        for G in Us:
            U = G @ U
        return U

    U_enc = apply_seq([dm.embed1(dm.ry(float(angles[i])), i, N) for i in range(N)])
    ket0 = np.eye(dim, dtype=complex)[:, 0]

    FULL = [dm.embed1(dm.ry(float(angles[i])), i, N) for i in range(N)] \
        + rot_block(0) + cx_block(0) + rot_block(1) + cx_block(1)

    # 全量子（未去相位）
    rho_full = dm.pure_dm(apply_seq(FULL) @ ket0)
    p_full = dm.probs_from_rho(rho_full)

    # --- 設定 (1)：去相位在電路最末端（緊接量測） ---------------------
    p1_c = dm.probs_from_rho(dm.dephase(rho_full, N))

    # --- 設定 (2)：去相位在中間，之後只接 10 個 CX（基底置換） --------
    #     依 qbn5_encoding.main【4】(d)：由全電路取 rho、去相位，再補 RING1+RING2
    U_allcx = apply_seq([dm.cnot_full(c, t, N) for (c, t) in (RING_STEP1 + RING_STEP2)])
    rho_c = dm.dephase(rho_full, N)
    p2_c = dm.probs_from_rho(U_allcx @ rho_c @ U_allcx.conj().T)
    p2_q = dm.probs_from_rho(U_allcx @ rho_full @ U_allcx.conj().T)

    # --- 設定 (3)：去相位在第 0 層之後，之後接完整第 1 層（RY+RZ+CX） --
    ABLATED = [dm.embed1(dm.ry(float(angles[i])), i, N) for i in range(N)] \
        + rot_block(0) + cx_block(0)          # 第 0 層
    rho_mid = dm.dephase(dm.pure_dm(apply_seq(ABLATED) @ ket0), N)   # ← 去相位
    U_rest = apply_seq(rot_block(1) + cx_block(1))                   # 第 1 層
    p3_c = dm.probs_from_rho(U_rest @ rho_mid @ U_rest.conj().T)

    d1 = float(np.max(np.abs(p_full - p1_c)))
    d2 = float(np.max(np.abs(p2_q - p2_c)))
    d3 = np.abs(p_full - p3_c)

    print("  三種插入位置的 32 維機率最大絕對差（本檔獨立密度矩陣實作）：")
    print(f"    (1) 最末端（緊接量測）          = {d1:.3e}")
    print(f"    (2) 中間，之後只接 10 個 CX     = {d2:.3e}")
    print(f"    (3) 中間，之後接完整第 1 層     = {d3.max():.8f}")
    print(f"        前 5 大差異 = {[f'{v:.6f}' for v in np.sort(d3)[::-1][:5]]}")
    print(f"        全變分距離 (1/2)Σ|Δp| = {0.5 * d3.sum():.8f}")
    print(f"        受影響基底態 (|Δp|>1e-9) = {int((d3 > 1e-9).sum())} / {dim}")
    print(f"        純度：全量子 {dm.purity(rho_full):.10f} "
          f"→ 去相位 {dm.purity(rho_c):.10f}")
    print(f"        去相位後 Σp_i² = {float(np.sum(dm.probs_from_rho(rho_c) ** 2)):.10f}")
    print(f"        去相位後 <X_0>,<Y_0> 最大殘值 = "
          f"{max(abs(np.real(np.trace(dm.pauli_full(P, 0, N) @ rho_c))) for P in (dm._X, dm._Y)):.3e}")

    check("(1) 尾端去相位：最大機率差 = 0（尾端去相位在量測上隱形）", d1 < 1e-15,
          f"{d1:.3e}   （專案實測 1.388e-17；README 記載 1.4e-17）")
    check("(2) 中間去相位 + 只接 CX：最大機率差 = 0（CX 與去相位交換）", d2 < 1e-15,
          f"{d2:.3e}   （專案實測 1.388e-17）")
    check("(3) 中間去相位 + 完整層：最大機率差為 O(0.01~0.1)（可觀測）",
          0.005 < d3.max() < 0.5,
          f"{d3.max():.8f}   （專案實測 0.05023467；README 記載 0.0502）")
    check("(3) 全部 32 個基底態都受影響",
          int((d3 > 1e-9).sum()) == dim, f"{int((d3 > 1e-9).sum())}/{dim}")
    print("  註：設定 (3) 的**確切數值**取決於權重 weights；上表已用專案自己的"
          "示範輸入（種子 42）")
    print("      重現，故與 dev/qbn5_encoding.py 的輸出同量級。"
          "權重不同時數值會變，但『非零』是定理。")
else:
    check("qbn_sim 可用", False, "略過")

# ----------------------------------------------------------------------
banner("【6】交換子的代數推論（為什麼么模仿塊閘『看不到』去相位）")
print("  若 U 是么模仿塊矩陣，則 U P_b U^dag = P_{sigma(b)} 對某個置換 sigma 成立。")
print("  => D(U rho U^dag) = sum_b P_b U rho U^dag P_b")
print("                    = U [sum_b P_{sigma^-1(b)} rho P_{sigma^-1(b)}] U^dag")
print("                    = U D(rho) U^dag。")
print("  又因為 D 只動非對角元、而么模仿塊閘只置換對角元，")
print("  故最後的 Born 機率向量只是被置換，**分布完全一樣**。")
rng = np.random.default_rng(11)
psi_r = rng.normal(size=4) + 1j * rng.normal(size=4)
psi_r /= np.linalg.norm(psi_r)
rho_r = dm.pure_dm(psi_r)
Ucn = dm.cnot_full(0, 1, 2)
p_a = dm.probs_from_rho(dm.dephase(dm.apply_unitary(rho_r, Ucn), 2))
p_b = dm.probs_from_rho(dm.apply_unitary(dm.dephase(rho_r, 2), Ucn))
check("任意態、任意么模仿塊閘：兩條路徑的機率向量完全相同",
      np.allclose(p_a, p_b, atol=1e-15), f"max|dp| = {np.max(np.abs(p_a - p_b)):.3e}")

banner("總結")
n_ok = sum(1 for _, ok in PASS if ok)
print(f"  通過 {n_ok} / {len(PASS)} 項")
for name, ok in PASS:
    if not ok:
        print(f"  !! 未通過：{name}")
sys.exit(0 if n_ok == len(PASS) else 1)
