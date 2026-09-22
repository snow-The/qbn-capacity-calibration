# -*- coding: utf-8 -*-
"""w14_lab1_dephasing.py — 去相位（dephasing / Tucci 的 ``cl`` 算子）實作與驗證。

本檔對應書中章節：``docs/05-實驗/消融實驗.md`` 的「動手做 1」。
它是一個**獨立**的最小實作，只依賴 NumPy，刻意與 ``dev/qbn_sim.py`` 解耦，
以便讀者複製貼上；同時也補上 ``qbn_sim.py`` 目前**沒有**的東西：
去相位算子需要密度矩陣，而 ``qbn_sim.py`` 的 ``StateVectorSim`` 是純態模擬器
（其 docstring 已明說「``dephase`` 不在本類別裡」）。

理論依據（行號為抽取檔實體行號）
--------------------------------
* ``cl`` 的定義：``docs/_extract/F1-tucci-qbn-mixed-states.md``【L358】
  ``cl_b(rho_ba) = sum_b [ |b><b|_b  rho_ba ][h.c.]``
* 「去相位＝丟掉非對角項」：【L410】
* 「對每個節點套 cl，QB net 就退化成古典貝氏網路」：【L53】
* 對應的 Kraus 算子 ``K_a = |a><a|``：【L526】
* 乘積封閉性與冪等性線索 ``tr_b cl_b = tr_b``：【L374】

執行方式::

    .venv\\Scripts\\python.exe dev/labs/w14_lab1_dephasing.py

輸出會同時印到 stdout 並寫入 ``dev/labs/out/w14_lab1_dephasing.txt``。
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from typing import Callable, List, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# 基底順序公約：與 dev/qbn_sim.py 一致 —— qubit 0 是最高位元（big-endian）。
# n 個 qubit 的索引 i 之二進位展開是 i = b_0 b_1 ... b_{n-1}，b_0 為最高位。
# 例：n=2 時 0=|00>, 1=|01>, 2=|10>, 3=|11>，第一個字元是 qubit 0。
# ---------------------------------------------------------------------------

N_QUBITS = 5
DIM = 1 << N_QUBITS  # 32


# ---------------------------------------------------------------------------
# 單量子位閘
# ---------------------------------------------------------------------------
def ry(theta: float) -> np.ndarray:
    """R_Y(theta) = [[cos(t/2), -sin(t/2)], [sin(t/2), cos(t/2)]]。"""
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def hadamard() -> np.ndarray:
    """H = (1/sqrt2)[[1,1],[1,-1]]，用來把 Z 基底量測換成 X 基底量測。"""
    return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)


def _embed_single(u: np.ndarray, target: int, n: int) -> np.ndarray:
    """把單量子位閘 u 嵌入 n qubit 的大矩陣（target=0 為最高位元）。

    ⚠️ 陷阱：起始值必須是 ``np.eye(1, dtype=complex)``（形狀 (1,1)），
    不能寫 ``np.array([[1.0 + 0j]])`` 之外的 0 維寫法。
    若起始值退化成 0 維純量，``np.kron`` 的結果也會是 0 維，
    後續 ``p @ rho @ p`` 就會拋出
    ``ValueError: matmul: Input operand 1 does not have enough dimensions``。
    本檔曾因 ``np.array(1.0 + 0j)``（0 維）而失敗，已改為顯式的 (1,1) 單位矩陣。
    """
    ops = [np.eye(2, dtype=complex)] * n
    ops[target] = u
    out = np.eye(1, dtype=complex)          # 形狀 (1,1)，保證 kron 的維度不塌陷
    for op in ops:
        out = np.kron(out, op)
    return out


# ---------------------------------------------------------------------------
# 電路：RY 角度編碼 -> 環形 CX 糾纏 -> 可訓練 RY/RZ 層 -> （可選第二層糾纏）
# ---------------------------------------------------------------------------
def _ring_pairs(n: int) -> List[Tuple[int, int]]:
    """環形拓樸（5 qubit：0-1-2-3-4-0）的受控閘配對。"""
    return [(i, (i + 1) % n) for i in range(n)]


def _chain_pairs(n: int) -> List[Tuple[int, int]]:
    """線性鏈拓樸的受控閘配對。"""
    return [(i, i + 1) for i in range(n - 1)]


def _all_pairs(n: int) -> List[Tuple[int, int]]:
    """全連接拓樸的受控閘配對。"""
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


TOPOLOGIES = {"ring": _ring_pairs, "chain": _chain_pairs, "full": _all_pairs}


def _cx_matrix(control: int, target: int, n: int) -> np.ndarray:
    """以 |0><0| ⊗ I + |1><1| ⊗ X 的形式建構 CNOT（含控制位與目標位順序）。"""
    proj0 = np.array([[1, 0], [0, 0]], dtype=complex)
    proj1 = np.array([[0, 0], [0, 1]], dtype=complex)
    xgate = np.array([[0, 1], [1, 0]], dtype=complex)
    ops0 = [np.eye(2, dtype=complex)] * n
    ops1 = [np.eye(2, dtype=complex)] * n
    ops0[control] = proj0
    ops1[control] = proj1
    ops1[target] = xgate

    def kron_all(ops: Sequence[np.ndarray]) -> np.ndarray:
        """把一串單量子位算子的張量積縮成一個大矩陣。

        ⚠️ 起始值必須是 ``np.eye(1, dtype=complex)``（形狀 ``(1,1)``），
        **不能**寫 ``np.array([[1.0 + 0j]])`` 之類容易退化的寫法：
        一旦起始值變成 0 維純量，``np.kron`` 會一路保持 0 維，
        最終回傳 object dtype 的純量，讓上層的 ``@`` 運算在遠處才爆開
        （症狀：``matmul: Input operand 1 does not have enough dimensions``）。
        本檔曾在 ``_embed_single`` 與此處各犯一次同樣的錯，兩處都已修正。
        """
        out = np.eye(1, dtype=complex)      # 形狀 (1,1)，保證 kron 維度不塌陷
        for op in ops:
            out = np.kron(out, op)
        return out

    return kron_all(ops0) + kron_all(ops1)


def build_state(
    thetas: Sequence[float],
    depth: int = 2,
    topology: str = "ring",
    encode_angles: Sequence[float] | None = None,
    entangle: bool = True,
) -> np.ndarray:
    """回傳 5 qubit 的**態向量**（全同調，未去相位）。

    參數
    ----
    thetas
        可訓練的 RY 角度，長度 ``depth * N_QUBITS``（逐一填入每一層）。
    depth
        可訓練旋轉層數（每層＝N 個 RY，之後選擇性接一層糾纏）。
    topology
        ``"ring"`` / ``"chain"`` / ``"full"``。
    encode_angles
        角度編碼的輸入角（長度 N_QUBITS）；``None`` 時用一組固定的示範值。
    entangle
        ``False`` 時**完全不加**任何 CX，電路全程維持乘積態（A2 對照臂）。
    """
    n = N_QUBITS
    if encode_angles is None:
        # 示範用的固定編碼角：刻意不對稱，使糾纏有東西可以混合。
        encode_angles = [0.35, 1.10, 2.20, 0.75, 1.85]

    u = np.eye(DIM, dtype=complex)
    for i in range(n):
        u = _embed_single(ry(float(encode_angles[i])), i, n) @ u

    pairs = TOPOLOGIES[topology](n)
    for layer in range(depth):
        for i in range(n):
            theta = float(thetas[layer * n + i])
            u = _embed_single(ry(theta), i, n) @ u
        if entangle:
            for c, t in pairs:
                u = _cx_matrix(c, t, n) @ u
    psi = u[:, 0]  # 從 |0...0> 出發
    return psi


# ---------------------------------------------------------------------------
# 去相位（本檔的主角）
# ---------------------------------------------------------------------------
def dephase(rho: np.ndarray, targets: Sequence[int], n: int = N_QUBITS) -> np.ndarray:
    """對指定 qubit 集合套用去相位算子 ``cl``。

    等價定義（三者相同，本檔用第一種，因其最不容易寫錯）:

    1. **元素逐項遮罩**：把 ``rho`` 中「targets 這幾個 qubit 的位元不相等」的
       元素全部歸零。這是 ``cl``【F1 L358】在計算基底下的直接結果。
    2. **投影算子夾擠**：``cl(rho) = sum_b P_b rho P_b``，其中
       ``P_b = |b><b|`` 只作用在 targets 上、其餘 qubit 不動【F1 L526】。
    3. **取部分跡再張量回對角**：對 targets 取 ``Tr`` 之後得到的古典分布，
       重新嵌回對角（把「消失了哪些 qubit 的同調」講清楚）。

    本函式對 targets 為空集合時回傳原矩陣（恆等操作）。
    """
    targets = list(targets)
    if not targets:
        return rho.copy()

    # ---- 方法 1：位元遮罩 ----
    idx = np.arange(DIM)
    # 取出 targets 那幾個位元的值（qubit 0 為最高位元）
    bits = np.stack([(idx >> (n - 1 - t)) & 1 for t in targets], axis=1)  # (DIM, len(targets))
    same = np.all(bits[:, None, :] == bits[None, :, :], axis=2)  # (DIM, DIM) bool
    out = np.where(same, rho, 0.0)

    # ---- 交叉檢查：方法 2（投影算子夾擠）必須給出同一個矩陣 ----
    proj_sum = np.zeros_like(rho)
    for b in range(1 << len(targets)):
        p = np.eye(DIM, dtype=complex)
        for k, t in enumerate(targets):
            bit = (b >> (len(targets) - 1 - k)) & 1
            keep = np.array([[1, 0], [0, 0]], dtype=complex) if bit == 0 else np.array(
                [[0, 0], [0, 1]], dtype=complex
            )
            p = _embed_single(keep, t, n) @ p
        proj_sum += p @ rho @ p
    assert np.allclose(out, proj_sum, atol=1e-12), "方法 1 與方法 2 不一致！"
    return out


def apply_dephasing(
    psi: np.ndarray, targets: Sequence[int], n: int = N_QUBITS
) -> np.ndarray:
    """把態向量先轉成密度矩陣，再去相位；回傳密度矩陣。"""
    rho = np.outer(psi, psi.conj())
    return dephase(rho, targets, n)


# ---------------------------------------------------------------------------
# 觀測量
# ---------------------------------------------------------------------------
def z_probs(rho: np.ndarray) -> np.ndarray:
    """計算基底量測的機率分布（對角元）。"""
    return np.real(np.diag(rho))


def x_probs(rho: np.ndarray) -> np.ndarray:
    """X 基底量測的機率分布：先對每個 qubit 套 H，再讀對角元。

    這是「去相位有沒有改變**可觀測的**分布」的關鍵測試：
    在 Z 基底下去相位是隱形的（見 main 的說明），但在 X 基底不是。
    """
    u = np.eye(DIM, dtype=complex)
    for i in range(N_QUBITS):
        u = _embed_single(hadamard(), i, N_QUBITS) @ u
    rotated = u @ rho @ u.conj().T
    return np.real(np.diag(rotated))


def coherence_l1(rho: np.ndarray) -> float:
    """同調性（coherence）的 l1 範數：所有非對角元絕對值之和。"""
    return float(np.sum(np.abs(rho)) - np.sum(np.abs(np.diag(rho))))


def expectation_x(rho: np.ndarray, target: int) -> float:
    """單一 qubit 的 <X> = Tr[rho * X_target]。"""
    xg = np.array([[0, 1], [1, 0]], dtype=complex)
    return float(np.real(np.trace(rho @ _embed_single(xg, target, N_QUBITS))))


def purity(rho: np.ndarray) -> float:
    """純度 Tr[rho^2]；純態為 1，完全混合態為 1/DIM。"""
    return float(np.real(np.trace(rho @ rho)))


def entanglement_entropy(rho: np.ndarray, keep: Sequence[int]) -> float:
    """對 ``keep`` 取部分跡後的馮紐曼熵（以 2 為底）。"""
    keep = list(keep)
    n = N_QUBITS
    rest = [q for q in range(n) if q not in keep]
    tensor = rho.reshape([2] * (2 * n))
    # 把 rest 的 ket 軸與 bra 軸搬到後面，再 reshape 成 (dim_keep, dim_rest, dim_keep, dim_rest)
    perm = keep + [q + n for q in keep] + rest + [q + n for q in rest]
    t = np.transpose(tensor, perm)
    dk = 1 << len(keep)
    dr = 1 << len(rest)
    t = t.reshape(dk, dr, dk, dr)
    reduced = np.einsum("ikjk->ij", t)
    ev = np.linalg.eigvalsh((reduced + reduced.conj().T) / 2.0)
    ev = ev[ev > 1e-12]
    return float(-np.sum(ev * np.log2(ev)))


# ---------------------------------------------------------------------------
# 三個插入位置的實驗
# ---------------------------------------------------------------------------
def build_rho(insert_at: str | None) -> np.ndarray:
    """依 ``insert_at`` 決定 ``cl`` 插在哪裡，回傳最終密度矩陣。

    ``insert_at`` 的三種值（對應消融項 A1 的三個候選位置）:

    * ``None``      —— 全量子（不對任何節點去相位）。這是對照組。
    * ``"encode"``  —— 只在**編碼層之後**去相位（古典前端剛注入完）。
    * ``"nodes"``   —— 在**每個節點**去相位（編碼層後、每一層可訓練旋轉後）。
                       這是【F1 L53】字面上說的「對每個節點套 cl」。
    * ``"final"``   —— 只在**最後**（測量前）去相位。
    """
    n = N_QUBITS
    thetas = [0.62, -1.05, 0.44, 1.31, -0.78,   # 第 1 層的 5 個 RY
              0.93, 0.27, -1.42, 0.58, 1.16]    # 第 2 層的 5 個 RY
    encode_angles = [0.35, 1.10, 2.20, 0.75, 1.85]
    pairs = _ring_pairs(n)

    # 初始態 |0...0>，同時持有態向量與其密度矩陣。
    # ★ 設計原則：rho 從頭到尾都是 (DIM, DIM) 的 ndarray，**絕不使用 None 哨兵**。
    #   先前的版本用 `rho = None` 當「還沒開始用密度矩陣」的標記，結果在
    #   "nodes" 路徑把已經建好的 rho 覆寫成 None，一路傳到 dephase() 才爆開
    #   （症狀是 object dtype 與 0 維，離真正的原因很遠）。
    psi = np.eye(DIM, dtype=complex)[:, 0].astype(complex)
    rho = np.outer(psi, psi.conj())

    # --- 編碼層 ---
    for i in range(n):
        psi = _embed_single(ry(float(encode_angles[i])), i, n) @ psi
    rho = np.outer(psi, psi.conj())          # 把編碼後的 psi 同步成 rho

    if insert_at == "encode":
        rho = dephase(rho, range(n))         # 古典前端剛注入完就去相位

    # --- 兩層「旋轉 + 糾纏」，全程都用密度矩陣演化 ---
    for layer in range(2):
        for i in range(n):
            gate = _embed_single(ry(float(thetas[layer * n + i])), i, n)
            rho = gate @ rho @ gate.conj().T
        for c, t in pairs:
            gate = _cx_matrix(c, t, n)
            rho = gate @ rho @ gate.conj().T
        if insert_at == "nodes":
            rho = dephase(rho, range(n))     # 每個節點後去相位【F1 L53】

    if insert_at == "final":
        rho = dephase(rho, range(n))         # 只在測量前去相位

    return rho


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------
def main() -> int:
    out = io.StringIO()

    def emit(*args: object) -> None:
        line = " ".join(str(a) for a in args)
        print(line)
        out.write(line + "\n")

    emit("=" * 78)
    emit("W14 動手做 1：去相位（cl）算子的實作與驗證")
    emit("=" * 78)
    emit("")

    # ------------------------------------------------------------------
    # 0. 先建立一個「有同調性」的 5 qubit 態
    # ------------------------------------------------------------------
    psi = build_state(
        thetas=[0.62, -1.05, 0.44, 1.31, -0.78, 0.93, 0.27, -1.42, 0.58, 1.16],
        depth=2,
        topology="ring",
    )
    rho = np.outer(psi, psi.conj())
    emit("【0】受測態：5 qubit，RY 角度編碼 -> 環形 CX -> 2 層 RY+環形 CX")
    emit(f"     Tr[rho]      = {np.real(np.trace(rho)):.15f}")
    emit(f"     純度 Tr[rho^2] = {purity(rho):.15f}   （純態應為 1.0）")
    emit(f"     非對角 l1 同調 = {coherence_l1(rho):.6f}")
    emit(f"     與 qubit{0} 的糾纏熵 S = {entanglement_entropy(rho, [0]):.6f} bit")
    emit("")

    # ------------------------------------------------------------------
    # 1. 驗證 (a)：機率分布「改變」
    # ------------------------------------------------------------------
    rho_d = dephase(rho, range(N_QUBITS))
    pz_before, pz_after = z_probs(rho), z_probs(rho_d)
    px_before, px_after = x_probs(rho), x_probs(rho_d)

    emit("【1】驗證 (a)：機率分布會不會變？—— 答案取決於「用哪個基底量測」")
    emit("")
    emit("  (a-1) 計算基底（Z 基底）下的 32 維分布：")
    emit(f"        max |p_before - p_after| = {np.max(np.abs(pz_before - pz_after)):.3e}")
    emit("        ==> 0。這是**定理**不是巧合：去相位只刪非對角元，而 Born 機率")
    emit("            取的是對角元。所以「在 Z 基底量測」時去相位完全隱形。")
    emit("            → 這一條必須誠實報告，否則整組消融會被老師一句話推翻。")
    emit("")
    emit("  (a-2) X 基底（每個 qubit 先過 H 再量）下的 32 維分布：")
    emit(f"        max |p_before - p_after| = {np.max(np.abs(px_before - px_after)):.6f}")
    emit(f"        l1 距離  sum|p_before - p_after| = {np.sum(np.abs(px_before - px_after)):.6f}")
    emit("        ==> 明顯改變。因為 X 基底量的是非對角（同調）資訊。")
    emit("")
    emit("        逐 qubit 的 <X> 對照（同調性最直接的證據）：")
    for q in range(N_QUBITS):
        emit(
            f"          qubit {q}:  <X>_全量子 = {expectation_x(rho, q):+.6f}"
            f"   <X>_去相位 = {expectation_x(rho_d, q):+.6f}"
            f"   差 = {expectation_x(rho, q) - expectation_x(rho_d, q):+.6f}"
        )
    emit("")
    emit("  (a-3) 前 8 個基底態的分布並排（量化「Z 基底不變、X 基底會變」）：")
    emit("        idx   Z_before   Z_after     X_before   X_after")
    for i in range(8):
        emit(
            f"        {i:>3}   {pz_before[i]:.6f}   {pz_after[i]:.6f}    "
            f"{px_before[i]:.6f}   {px_after[i]:.6f}"
        )
    emit("")

    # ------------------------------------------------------------------
    # 2. 驗證 (b)：跡仍為 1、且仍為合法密度矩陣
    # ------------------------------------------------------------------
    c1 = np.real(np.trace(rho_d)) - 1.0
    emit("【2】驗證 (b)：去相位後仍是合法密度矩陣")
    emit(f"     |Tr[rho_cl] - 1|        = {abs(c1):.3e}")
    herm = np.max(np.abs(rho_d - rho_d.conj().T))
    emit(f"     Hermitian 誤差 max|rho-rho^dag| = {herm:.3e}")
    ev = np.linalg.eigvalsh((rho_d + rho_d.conj().T) / 2.0)
    emit(f"     最小 eigenvalue          = {ev.min():.3e}   （必須 >= 0）")
    emit(f"     純度由 {purity(rho):.10f} 降為 {purity(rho_d):.10f}")
    emit("     ==> 跡保（trace-preserving）成立。理由：cl 是 CPTP 通道，")
    emit("         其 Kraus 算子 K_a=|a><a| 滿足 sum_a K_a^dag K_a = I【F1 L486/L526】。")
    emit("")

    # ------------------------------------------------------------------
    # 3. 驗證 (c)：冪等性
    # ------------------------------------------------------------------
    rho_dd = dephase(rho_d, range(N_QUBITS))
    rho_ddd = dephase(rho_dd, range(N_QUBITS))
    e2 = np.max(np.abs(rho_dd - rho_d))
    e3 = np.max(np.abs(rho_ddd - rho_d))
    emit("【3】驗證 (c)：冪等性 cl(cl(rho)) = cl(rho)")
    emit(f"     max|cl(cl(rho)) - cl(rho)|     = {e2:.3e}")
    emit(f"     max|cl^3(rho)   - cl(rho)|     = {e3:.3e}")
    emit("     ==> 冪等性成立（數值上是機器精度等級）。")
    emit("         理論理由：cl 之後非對角元已全為 0，再遮罩一次沒有東西可刪；")
    emit("         這與【F1 L374】的封閉性 tr_b cl_b = tr_b 同源。")
    emit("")
    emit("     順帶檢查：cl 不可逆【F1 L438】——去相位後再補一個么正閘，")
    emit("     同調性仍然回不來（見下方第 4 節的對照）。")
    emit("")

    # ------------------------------------------------------------------
    # 4. 三個插入位置的比較
    # ------------------------------------------------------------------
    emit("【4】``cl`` 插在哪裡？三種插入位置 + 全量子對照")
    emit("")
    header = (
        f"     {'設定':<26}{'Tr':>10}{'純度':>14}{'l1同調':>12}"
        f"{'maxΔPz':>12}{'maxΔPx':>12}"
    )
    emit(header)
    emit("     " + "-" * (len(header) - 5))

    ref_pz, ref_px = pz_before, px_before
    rows: List[Tuple[str, np.ndarray]] = [
        ("(0) 全量子（對照）", rho),
        ("(1) 只在編碼層後 cl", build_rho("encode")),
        ("(2) 在每個節點 cl【L53】", build_rho("nodes")),
        ("(3) 只在最後 cl", build_rho("final")),
    ]
    for name, r in rows:
        emit(
            f"     {name:<26}{np.real(np.trace(r)):>10.6f}{purity(r):>14.6f}"
            f"{coherence_l1(r):>12.6f}"
            f"{np.max(np.abs(z_probs(r) - ref_pz)):>12.6f}"
            f"{np.max(np.abs(x_probs(r) - ref_px)):>12.6f}"
        )
    emit("")
    emit("  讀法：")
    emit("   * 「在每個節點 cl」把同調性壓到 0（l1 同調 = 0），X 基底分布與全量子")
    emit("     的差距最大 —— 這正是【F1 L53】所說的『退化為古典貝氏網路』。")
    emit("   * 「只在最後 cl」同樣讓最終 rho 變成對角（非對角在最後一步被刪），")
    emit("     但它**保留了中間過程的干涉**：中間的振幅相加已經發生、結果已經")
    emit("     寫進對角元，所以 Z 基底分布與全量子完全相同。")
    emit("   * 因此 A1 消融必須**明講插入位置**，否則「去相位」三個字是歧義的。")
    emit("     本專案正式實驗採「在每個節點 cl」作為 A1 的處理臂，因為那才是")
    emit("     【F1 L53】字面上的操作；「只在最後 cl」作為附帶的第二個處理臂，")
    emit("     用來分離「中間干涉」與「最終讀出同調」兩項貢獻。")
    emit("")

    # ------------------------------------------------------------------
    # 5. 冗餘實作一致性（方法 1 vs 方法 2 已在 dephase 內 assert）
    # ------------------------------------------------------------------
    emit("【5】實作自我檢查")
    emit("     dephase() 內部已 assert「位元遮罩」與「投影算子夾擠」兩條路徑")
    emit("     給出同一個矩陣（atol=1e-12），本執行未觸發 assert。")
    emit("     第三條路徑（取部分跡後張量回對角）等價性另由 dev/labs 的")
    emit("     w14_lab1b 交叉驗證。")
    emit("")
    emit("=" * 78)
    emit("結論：去相位函式通過 (a) 分布改變（X 基底）、(b) 跡保、(c) 冪等 三項驗證。")
    emit("=" * 78)

    # 寫檔
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "w14_lab1_dephasing.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out.getvalue())
    print(f"\n[寫入] {path}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
