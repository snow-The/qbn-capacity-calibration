"""t4_kraus_dephasing.py — T4 的數值驗證。

對應文件：``projects/qbn-capacity-calibration/theory/T4_dephasing_kraus.md``

驗證清單
--------
1. Kraus 完備性 :math:`\\sum_k K_k^\\dagger K_k = I`
2. 單 qubit：:math:`\\rho=|+\\rangle\\langle+|` 的非對角元 :math:`1/2\\to0`
3. 跡保性 :math:`\\mathrm{Tr}[\\mathcal E(\\rho)]=\\mathrm{Tr}[\\rho]`
4. 共軛自伴與正性（去相位後仍是合法密度矩陣）
5. 冪等性 :math:`\\mathcal D\\circ\\mathcal D=\\mathcal D`（去相位不可逆）
6. :math:`n` qubit：張量積 Kraus 算符 = :math:`2^n` 個基底投影子
7. 遮罩形式與投影子求和形式一致
8. 隨機 :math:`Z` 塗鴉（twirling）形式一致
9. 完全正性（Choi 矩陣半正定）
10. 計算基底機率不變（:math:`P(i)=\\rho_{ii}`）
11. 與 ``dev/qbn_sim.py`` 態向量路徑交叉驗證（5 qubit QBN 電路）
12. 純度與 :math:`\\langle X\\rangle,\\langle Y\\rangle` 的變化

執行：``uv run python projects/qbn-capacity-calibration/theory/verify/t4_kraus_dephasing.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dmtools as dm  # noqa: E402

# ---- 專案模擬器（態向量路徑，作為獨立交叉驗證） --------------------------
_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))
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
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"   {detail}" if detail else ""))


def banner(title: str) -> None:
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


# ----------------------------------------------------------------------
banner("【1】Kraus 算符的定義與完備性（單 qubit）")
K0, K1 = dm.kraus_dephase_1q()
print("  K0 = |0><0| ="); print("   ", np.array2string(K0.real, prefix="    "))
print("  K1 = |1><1| ="); print("   ", np.array2string(K1.real, prefix="    "))
comp = K0.conj().T @ K0 + K1.conj().T @ K1
check("完備性 sum_k K_k^dag K_k = I", np.allclose(comp, np.eye(2)),
      f"max|sum - I| = {np.max(np.abs(comp - np.eye(2))):.3e}")
check("K_k 是投影子且 Hermitian（K^2=K, K^dag=K）",
      np.allclose(K0 @ K0, K0) and np.allclose(K1 @ K1, K1)
      and np.allclose(K0.conj().T, K0) and np.allclose(K1.conj().T, K1))
check("K0 K1 = 0（Kraus 算符互相正交）", np.allclose(K0 @ K1, 0))

# ----------------------------------------------------------------------
banner("【2】|+> 態：非對角元歸零")
plus = np.array([1, 1]) / np.sqrt(2)
rho_plus = dm.pure_dm(plus)
print("  去相位前 rho ="); print("   ", np.array2string(rho_plus, prefix="    "))
rho_d = K0 @ rho_plus @ K0.conj().T + K1 @ rho_plus @ K1.conj().T
print("  去相位後 rho ="); print("   ", np.array2string(rho_d, prefix="    "))
check("非對角元 rho_01: 0.5 -> 0", np.isclose(rho_plus[0, 1], 0.5)
      and np.isclose(rho_d[0, 1], 0.0),
      f"rho_01: {rho_plus[0,1]:.6f} -> {rho_d[0,1]:.3e}")
check("對角元不變（rho_00 = rho_11 = 0.5）",
      np.allclose(np.diag(rho_d), np.diag(rho_plus)),
      f"diag = {np.array2string(np.diag(rho_d).real, precision=6)}")
check("跡保性 Tr[E(rho)] = Tr[rho] = 1",
      np.isclose(np.trace(rho_d).real, np.trace(rho_plus).real),
      f"Tr = {np.trace(rho_d).real:.15f}")
check("Hermitian 保持", np.allclose(rho_d, rho_d.conj().T))
check("正性（最小特徵值 >= 0）", np.linalg.eigvalsh(rho_d).min() >= -1e-15,
      f"lambda_min = {np.linalg.eigvalsh(rho_d).min():.3e}")
check("純度下降 Tr[rho^2]: 1 -> 0.5",
      np.isclose(dm.purity(rho_plus), 1.0) and np.isclose(dm.purity(rho_d), 0.5),
      f"Tr[rho^2] = {dm.purity(rho_plus):.6f} -> {dm.purity(rho_d):.6f}")

# 冪等
rho_dd = K0 @ rho_d @ K0.conj().T + K1 @ rho_d @ K1.conj().T
check("冪等性 D(D(rho)) = D(rho)", np.allclose(rho_dd, rho_d),
      f"max|D^2 - D| = {np.max(np.abs(rho_dd - rho_d)):.3e}")

# ----------------------------------------------------------------------
banner("【3】一般態與任意 qubit 數：n qubit 的張量積 Kraus 算符")
# 3a. 一般單 qubit 態
rng = np.random.default_rng(7)
psi = rng.normal(size=2) + 1j * rng.normal(size=2)
psi /= np.linalg.norm(psi)
rho = dm.pure_dm(psi)
rd = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
check("一般態：非對角元全歸零", np.allclose(np.diag(np.diag(rd)), rd, atol=1e-15),
      f"max|offdiag| = {np.max(np.abs(rd - np.diag(np.diag(rd)))):.3e}")

# 3b. n qubit：2^n 個張量積 Kraus 算符 = 2^n 個基底投影子
dim = 2 ** N
Kraus_n = []
for b in range(dim):
    K = np.zeros((dim, dim), dtype=complex)
    K[b, b] = 1.0          # K_b = |b><b|  =  tensor product of |b_q><b_q|
    Kraus_n.append(K)
comp_n = sum(K.conj().T @ K for K in Kraus_n)
check(f"n={N}：2^n = {dim} 個 Kraus 算符的完備性",
      np.allclose(comp_n, np.eye(dim)), f"max|sum - I| = {np.max(np.abs(comp_n - np.eye(dim))):.3e}")

# 檢查 K_b 真的是單 qubit Kraus 的張量積
b_test = 0b10110
K_tensor = np.array([[1.0 + 0j]])
for q in range(N):
    bit = (b_test >> (N - 1 - q)) & 1
    K_tensor = np.kron(K_tensor, K0 if bit == 0 else K1)
check("K_b 等於單 qubit Kraus 的張量積（big-endian 約定）",
      np.allclose(K_tensor, Kraus_n[b_test]),
      f"b = {b_test:05b}")

# ----------------------------------------------------------------------
banner("【4】三種等價形式的互相驗證（遮罩 / 投影子求和 / 隨機 Z 塗鴉）")
psi5 = rng.normal(size=dim) + 1j * rng.normal(size=dim)
psi5 /= np.linalg.norm(psi5)
rho5 = dm.pure_dm(psi5)

f_mask = dm.dephase(rho5, N)
f_sum = dm.dephase_sum_form(rho5, N)
# 隨機 Z 塗鴉： (1/2^n) sum_s Z_s rho Z_s
f_twirl = np.zeros_like(rho5)
for pat in range(dim):
    Zs = np.eye(dim, dtype=complex)
    for q in range(N):
        if (pat >> (N - 1 - q)) & 1:
            Zs = Zs @ dm.pauli_full(dm._Z, q, N)
    f_twirl += Zs @ rho5 @ Zs.conj().T
f_twirl /= dim

check("遮罩形式 == 投影子求和形式", np.allclose(f_mask, f_sum),
      f"max|diff| = {np.max(np.abs(f_mask - f_sum)):.3e}")
check("遮罩形式 == 隨機 Z 塗鴉形式", np.allclose(f_mask, f_twirl),
      f"max|diff| = {np.max(np.abs(f_mask - f_twirl)):.3e}")
check("三者都等於 diag(rho)（去相位的閉式解）",
      np.allclose(f_mask, np.diag(np.diag(rho5))),
      f"max|D(rho) - diag(rho)| = {np.max(np.abs(f_mask - np.diag(np.diag(rho5)))):.3e}")

# 部分去相位（只對子集 S）也要對
for S in ([0], [0, 2], [0, 1, 2, 3]):
    a = dm.dephase(rho5, N, S)
    b = dm.dephase_sum_form(rho5, N, S)
    check(f"部分去相位 S={S}：兩形式一致", np.allclose(a, b),
          f"max|diff| = {np.max(np.abs(a - b)):.3e}")

# ----------------------------------------------------------------------
banner("【5】完全正性（Choi 矩陣半正定）")
# Choi 矩陣 J(E) = sum_ij E(|i><j|) ⊗ |i><j|
J = np.zeros((4, 4), dtype=complex)
for i in range(2):
    for j in range(2):
        Eij = K0 @ np.outer(np.eye(2)[:, i], np.eye(2)[:, j].conj()) @ K0.conj().T \
            + K1 @ np.outer(np.eye(2)[:, i], np.eye(2)[:, j].conj()) @ K1.conj().T
        J += np.kron(Eij, np.outer(np.eye(2)[:, i], np.eye(2)[:, j].conj()))
ev = np.linalg.eigvalsh((J + J.conj().T) / 2)
check("Choi 矩陣 Hermitian", np.allclose(J, J.conj().T))
check("Choi 矩陣半正定（=> 通道完全正）", ev.min() >= -1e-14,
      f"lambda_min(J) = {ev.min():.3e}")
# 對照：轉置映射 T 是正但**不**完全正
J_T = np.zeros((4, 4), dtype=complex)
for i in range(2):
    for j in range(2):
        Eij = np.outer(np.eye(2)[:, i], np.eye(2)[:, j].conj()).T
        J_T += np.kron(Eij, np.outer(np.eye(2)[:, i], np.eye(2)[:, j].conj()))
ev_T = np.linalg.eigvalsh((J_T + J_T.conj().T) / 2)
check("對照組：轉置映射 T 的 Choi 矩陣有負特徵值（正但非完全正）",
      ev_T.min() < 0, f"lambda_min(J_T) = {ev_T.min():.3e}")

# ----------------------------------------------------------------------
banner("【6】計算基底機率不變：P(i) = Tr[M_i rho] = rho_ii")
p_before = dm.probs_from_rho(rho5)
p_after = dm.probs_from_rho(f_mask)
check("去相位前後 32 維 Born 機率完全相同", np.allclose(p_before, p_after),
      f"max|dp| = {np.max(np.abs(p_before - p_after)):.3e}")
# 但 ⟨X⟩、⟨Y⟩ 會歸零
X0 = dm.pauli_full(dm._X, 0, N)
Y0 = dm.pauli_full(dm._Y, 0, N)
Z0 = dm.pauli_full(dm._Z, 0, N)
x_b, x_a = np.real(np.trace(X0 @ rho5)), np.real(np.trace(X0 @ f_mask))
y_b, y_a = np.real(np.trace(Y0 @ rho5)), np.real(np.trace(Y0 @ f_mask))
z_b, z_a = np.real(np.trace(Z0 @ rho5)), np.real(np.trace(Z0 @ f_mask))
print(f"  <X_0>: {x_b:+.6f} -> {x_a:+.3e}")
print(f"  <Y_0>: {y_b:+.6f} -> {y_a:+.3e}")
print(f"  <Z_0>: {z_b:+.6f} -> {z_a:+.6f}")
check("<X>,<Y> 歸零（同調性被抹除）",
      abs(x_a) < 1e-14 and abs(y_a) < 1e-14)
check("<Z> 完全不變（Z 是對角的）", np.isclose(z_b, z_a, atol=1e-14))

# ----------------------------------------------------------------------
banner("【7】與 dev/qbn_sim.py 態向量路徑交叉驗證（5 qubit QBN 電路）")
if _HAS_SIM:
    x_enc = [0.9, 0.2, 0.75, 0.4, 0.6]
    params = [0.31, -0.52, 0.77, 1.13, -0.29, 0.41, 0.88, -0.63, 0.19, 0.55]

    sim = StateVectorSim(N)
    for i in range(N):
        sim.ry(2.0 * np.arcsin(np.sqrt(x_enc[i])), i)
    for i in range(N):
        sim.cx(i, (i + 1) % N)
    for i in range(N):
        sim.ry(params[i], i)
    for i in range(N):
        sim.rz(params[N + i], i)
    p_sim = sim.probabilities()

    # 同一電路的密度矩陣路徑
    U = np.eye(dim, dtype=complex)
    for i in range(N):
        U = dm.embed1(dm.ry(2.0 * np.arcsin(np.sqrt(x_enc[i]))), i, N) @ U
    for i in range(N):
        U = dm.cnot_full(i, (i + 1) % N, N) @ U
    for i in range(N):
        U = dm.embed1(dm.ry(params[i]), i, N) @ U
    for i in range(N):
        U = dm.embed1(dm.rz(params[N + i]), i, N) @ U
    psi_dm = U @ np.eye(dim, dtype=complex)[:, 0]
    rho_dm = dm.pure_dm(psi_dm)
    p_dm = dm.probs_from_rho(rho_dm)

    check("態向量路徑（qbn_sim）vs 密度矩陣路徑（dmtools）機率一致",
          np.allclose(p_sim, p_dm, atol=1e-12),
          f"max|dp| = {np.max(np.abs(p_sim - p_dm)):.3e}")

    # 去相位後
    rho_d = dm.dephase(rho_dm, N)
    p_d = dm.probs_from_rho(rho_d)
    check("5 qubit 電路：去相位後 Born 機率不變（尾端去相位隱形）",
          np.allclose(p_dm, p_d, atol=1e-12),
          f"max|dp| = {np.max(np.abs(p_dm - p_d)):.3e}")
    print(f"  純度 Tr[rho^2]: {dm.purity(rho_dm):.12f} -> {dm.purity(rho_d):.12f}")
    print(f"  糾纏熵 S(qubit 0): {dm.vn_entropy(dm.partial_trace(rho_dm,[0],N)):.8f} bit"
          f" -> {dm.vn_entropy(dm.partial_trace(rho_d,[0],N)):.8f} bit")
    print(f"  糾纏熵 S(qubits 0,1): {dm.vn_entropy(dm.partial_trace(rho_dm,[0,1],N)):.8f} bit"
          f" -> {dm.vn_entropy(dm.partial_trace(rho_d,[0,1],N)):.8f} bit")
    print("  註：去相位後整體是古典混態，但**單邊約化熵不會下降**——")
    print("      因為 ρ 的非對角元貢獻的是『純態整體』的糾纏，而古典混態"
          "也能有大的邊際熵。")
else:
    check("qbn_sim 可用", False, "略過交叉驗證")

# ----------------------------------------------------------------------
banner("總結")
n_ok = sum(1 for _, ok in PASS if ok)
print(f"  通過 {n_ok} / {len(PASS)} 項")
for name, ok in PASS:
    if not ok:
        print(f"  !! 未通過：{name}")
sys.exit(0 if n_ok == len(PASS) else 1)
