"""s17_dephasing_ablation.py — RQ2：去相位（古典化）消融，四臂 × 5 種子。

為什麼要做這個實驗
==================
論文 §5「校準消融」的表目前全是佔位符（`paper/paper.typ` L363-372），
因為這個實驗從未被執行。本檔把它補起來。

設計上的硬約束（來自 ``研究搜尋/00-碰撞處置-Ghosh2026.md``）
-----------------------------------------------------------------------
Ghosh 等（2026, ICOSAAS, DOI 10.1109/icosaas68663.2026.11648877）發現
「退極化雜訊從不降低 ECE」，並警告「**表達力較差的 ansatz 可能只因塌縮到
退化解而看起來校準良好**」。因此本實驗必須能排除兩種替代解釋：

* **塌縮**：去相位臂若 ECE 變好，可能只是模型退化。⇒ 每個 (臂, 種子) 都要
  記錄塌縮指標。
* **雜訊即正則化**：效果可能來自「任何雜訊」而非「失去相干性」。⇒ 加一個
  等強度退極化對照臂（臂 D）。

四臂
----
+------+--------------------------------------+--------------------------------+
| 臂   | 內容                                 | 為什麼要它                     |
+======+======================================+================================+
| A    | 不加任何通道（全量子）               | 對照基線                       |
+------+--------------------------------------+--------------------------------+
| B    | **編碼層後**施加計算基底去相位       | 主實驗（論文表的「編碼層後」） |
+------+--------------------------------------+--------------------------------+
| C    | **測量前**（電路尾端）施加去相位     | 內建 sanity check：依 T5 定理  |
|      |                                      | 必須是**精確 no-op**           |
+------+--------------------------------------+--------------------------------+
| D    | 與 B **同一位置**施加退極化，強度以  | 排除「雜訊即正則化」           |
|      | 二分法校準到與 B 相同的平均純度      |                                |
+------+--------------------------------------+--------------------------------+

數學約定（沿用專案既有定義，不另立一套）
----------------------------------------
* 去相位通道：`theory/verify/t4_kraus_dephasing.py` +
  `theory/verify/dmtools.py`。
  D_S(rho) = sum_b P_b rho P_b，作用在矩陣元上即
  (D_S(rho))_ij = rho_ij * prod_{q in S} delta_{b_q(i), b_q(j)}。
  本檔直接呼叫 `dmtools.dephase_mask` 取得遮罩，不自行重寫定義。
* 位元公約：big-endian，最左邊是 qubit 0（與 `dev/qbn_sim.py`、`dmtools.py`、
  `s09`、`s12` 一致）。
* 交換定理：`theory/verify/t5_commutator_placement.py`。
  CNOT 與 R_Z 在計算基底是**么模仿塊矩陣**，與 D 交換；R_Y 不是。
  ⇒ 尾端去相位（後面只剩對角讀出）必須是 no-op。
* 電路與資料：`s09_capacity_scan.py`（角度編碼 → 環形 CX ansatz →
  前 3 個 qubit 讀出 8 類；資料用 `s09.make_data`）。
* 去相位後狀態是**混態**，故一律用密度矩陣（2^5 x 2^5 = 32 x 32）模擬。

梯度（兩條獨立路徑，互相對帳）
------------------------------
1. **參數平移**（`loss_grad`）：dP/dtheta = (P(+pi/2) - P(-pi/2)) / 2。
   插入中間的通道是**線性**映射，而平移規則只依賴閘層級的代數恆等式，線性映射
   與它交換，故規則在通道存在時依然**精確**。
2. **反向模式（adjoint）**（`loss_grad_adjoint`）：一次前向 + 一次反向。
   反向傳遞三條恆等式：
     * 么正閘 U：sigma -> U^dag sigma U
     * 通道 C（去相位與退極化都是自伴映射）：sigma -> C(sigma)
     * 可訓練角度（U = exp(-i theta G / 2)，G 為 Y 或 Z）：
           dL/dtheta = -(i/2) Tr(G [rho_after, sigma_after])
   preflight 會把兩條路徑與中心差分三方對帳；不一致就中止。

效能註記（實測，非推測）
------------------------
本機 numpy 2.5.2 上，**每次重新配置**一個 1.3 MB 的 complex128 陣列要 ~456 us
（分頁缺頁主導），而同大小、寫入重用緩衝區的 `np.copyto` 只要 ~23 us
（差 20 倍）。因此所有核心運算都改寫成「就地 + 預先配置暫存緩衝區」，
不用 `np.stack`／`np.empty_like`。

判準（寫進報告）
----------------
1. 若去相位臂（B）的 ECE 改善，**同時**伴隨塌縮指標惡化，
   則該改善**不得**歸因於量子性。
2. 若退極化臂（D）與 B 表現相同，則效果來自「雜訊」而非「失去相干性」，
   假設 H2 不成立。

執行
----
    python projects/qbn-capacity-calibration/ml/s17_dephasing_ablation.py
    python .../s17_dephasing_ablation.py --preflight-only      # 只跑正確性檢查
    python .../s17_dephasing_ablation.py --arms A --seeds 7   # 短跑 pilot
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np

# ===========================================================================
# 檔頭參數（所有可調參數集中在此；CLI 只是覆寫，供短跑驗證用）
# ===========================================================================
N_QUBIT = 5                      # 輸出層 qubit 數（論文設計）
DEPTH = 2                        # 變分層數（環形 CX ansatz，沿用 s09/s12）
N_CLASS = 8                      # 前 3 個 qubit 的基底模式 → 8 類（與 n 無關）
SEEDS = (7, 21, 42, 84, 168)     # 論文 §統計協定 指定的 5 個種子
STEPS = 800                      # Adam 步數（已足夠讓四臂都收敛，見報告）
LR = 0.08                        # Adam 學習率
GRADIENT = "adjoint"             # "adjoint"（快）或 "paramshift"（慢但直觀）
BETA1, BETA2, EPS_ADAM = 0.9, 0.999, 1e-8
W_INIT_STD = 0.3                 # 權重初始化 N(0, 0.3)（沿用 s09/s12/s16）
DATA_SEED = 12345                # s09.make_data 的預設種子（資料固定）
CHANNEL_POS_FRONT = 0            # 已套用 0 層 ⇒ 編碼層後（臂 B/D）
CHANNEL_POS_END = DEPTH          # 已套用全部層 ⇒ 測量前（臂 C）
SHIFT_CHUNK = 8                  # 參數平移梯度：每批次處理幾個參數
ECE_BINS = 10                    # 論文 §評估指標：M = 10 等寬分箱
BISECT_ITERS = 80                # 退極化強度二分法迭代上限
BISECT_TOL = 1e-14               # 純度匹配容差
PREFLIGHT_TOL_ARM_C = 1e-14      # 臂 C no-op 的硬門檻
PREFLIGHT_TOL_GRAD = 1e-9        # adjoint vs 參數平移的相對誤差門檻
T975_DF4 = 2.7764451051977987    # t_{0.975, df=4}（5 個種子的 95% CI）

HERE = pathlib.Path(__file__).resolve().parent
VERIFY_DIR = HERE.parent / "theory" / "verify"
OUT_JSON = HERE / "out" / "s17_dephasing_ablation.json"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(VERIFY_DIR))

import s09_capacity_scan as s09          # noqa: E402  電路／資料／編碼的權威定義
import dmtools as dm                     # noqa: E402  去相位通道的權威定義

# 四臂定義：kind ∈ {none, dephase, depolarize}；pos = 通道前已套用的層數
ARMS = {
    "A_baseline": dict(kind="none", pos=None, label="A 無通道（全量子）"),
    "B_dephase_front": dict(kind="dephase", pos=CHANNEL_POS_FRONT,
                            label="B 去相位（編碼層後）"),
    "C_dephase_end": dict(kind="dephase", pos=CHANNEL_POS_END,
                          label="C 去相位（電路尾端，測量前）"),
    "D_depolar_front": dict(kind="depolarize", pos=CHANNEL_POS_FRONT,
                            label="D 退極化（等純度，同 B 位置）"),
}

_MASK_CACHE: dict = {}


# ===========================================================================
# 就地核心運算（全部零配置；暫存緩衝區由呼叫者提供）
# ===========================================================================
def _bc6(x, B):
    """把純量或 (B,) 的閘元素廣播成 (B,1,1,1,1,1)（可對 6 軸視圖廣播）。"""
    return np.broadcast_to(np.asarray(x, dtype=np.complex128), (B,)).reshape(B, 1, 1, 1, 1, 1)


def apply_1q_ip(rho, s1, s2, g00, g01, g10, g11, t, n):
    """就地施加單閘 rho <- U rho U^dag（big-endian：軸 k ↔ qubit k）。

    分兩步：先對「列索引」的 qubit t 收縮，再對「行索引」的 qubit t 收縮。
    s1、s2 是同形狀的暫存緩衝區；結果寫回 rho 的緩衝區。
    """
    B = rho.shape[0]
    A, C = 1 << t, 1 << (n - 1 - t)
    g00, g01, g10, g11 = (_bc6(g, B) for g in (g00, g01, g10, g11))
    R = rho.reshape(B, A, 2, C, A, 2, C)
    S = s1.reshape(B, A, 2, C, A, 2, C)
    Q = s2.reshape(B, A, 2, C, A, 2, C)
    a, b = R[:, :, 0], R[:, :, 1]
    x, y = S[:, :, 0], S[:, :, 1]
    q = Q[:, :, 0]
    # 列：rho'[a,i,c|...] = sum_p U[i,p] rho[a,p,c|...]
    np.multiply(b, g01, out=q)
    np.multiply(a, g00, out=x)
    x += q
    np.multiply(b, g11, out=q)
    np.multiply(a, g10, out=y)
    y += q
    # 行：rho''[..|d,j,e] = sum_q conj(U[j,q]) rho'[..|d,q,e]
    a2, b2 = S[:, :, :, :, :, 0], S[:, :, :, :, :, 1]
    x2, y2 = R[:, :, :, :, :, 0], R[:, :, :, :, :, 1]
    q2 = Q[:, :, :, :, :, 0]
    c00, c01, c10, c11 = (np.conj(g) for g in (g00, g01, g10, g11))
    np.multiply(b2, c01, out=q2)
    np.multiply(a2, c00, out=x2)
    x2 += q2
    np.multiply(b2, c11, out=q2)
    np.multiply(a2, c10, out=y2)
    y2 += q2


def cnot_perm(control, target, n):
    idx = np.arange(1 << n)
    cbit = (idx >> (n - 1 - control)) & 1
    perm = idx ^ (cbit << (n - 1 - target))
    return perm, np.argsort(perm)


def apply_cx_ip(rho, scratch, control, target, n):
    """就地施加 CNOT（計算基底置換矩陣）：rho -> P rho P^T。"""
    _, inv = cnot_perm(control, target, n)
    np.take(rho, inv, axis=1, out=scratch)
    np.take(scratch, inv, axis=2, out=rho)


def dephase_ip(rho, n):
    """就地計算基底去相位（遮罩直接取自 dmtools.dephase_mask）。"""
    m = _MASK_CACHE.get(n)
    if m is None:
        m = dm.dephase_mask(n).reshape(1 << n, 1 << n)[None, :, :]
        _MASK_CACHE[n] = m
    np.multiply(rho, m, out=rho)


def depolarize_ip(rho, ptbuf, p, n):
    """就地對**每一個** qubit 施加退極化（同強度 p）：

        E_t(rho) = (1-p) rho + p * Tr_t[rho] (x) I/2

    這是「推向最大混態」的標準參數化。單 qubit 的等價 Pauli 形式是
    (1-p) rho + (p/3)(X rho X + Y rho Y + Z rho Z)，故 Pauli 錯誤率 q = 4p/3。
    對純態的純度變化為 Tr[rho^2] -> 1 - p + p^2/2。
    """
    B = rho.shape[0]
    h = 0.5 * p
    for t in range(n):
        A, C = 1 << t, 1 << (n - 1 - t)
        R = rho.reshape(B, A, 2, C, A, 2, C)
        P = ptbuf.reshape(B, A, C, A, C)
        # 對 qubit t 取部分跡：pt[b,a,c,d,e] = sum_p R[b,a,p,c,d,p,e]
        np.add(R[:, :, 0][..., 0, :], R[:, :, 1][..., 1, :], out=P)
        np.multiply(rho, 1.0 - p, out=rho)
        np.multiply(P, h, out=P)
        R2 = rho.reshape(B, A, 2, C, A, 2, C)
        R2[:, :, 0, :, :, 0, :] += P
        R2[:, :, 1, :, :, 1, :] += P


# ===========================================================================
# 密度矩陣模擬器（big-endian：軸 k ↔ qubit k）
# ===========================================================================
class DensitySim:
    """批次密度矩陣模擬器，支援去相位與（局部）退極化通道。

    狀態 `rho` 形狀 `(B, 2^n, 2^n)`。所有閘／通道都沿批次軸作用，
    所以「一次呼叫 = 一整個批次」，可以順便把參數平移的每個平移量塞進批次。
    所有運算就地進行，暫存緩衝區在建構時一次配置好（見檔頭的效能註記）。
    """

    def __init__(self, n: int, batch: int) -> None:
        self.n = n
        self.batch = batch
        self.dim = 1 << n
        self.rho = np.zeros((batch, self.dim, self.dim), dtype=np.complex128)
        self.rho[:, 0, 0] = 1.0                      # |0...0>
        self.s1 = np.empty_like(self.rho)
        self.s2 = np.empty_like(self.rho)
        self.pt = np.empty((batch, self.dim // 2, self.dim // 2), dtype=np.complex128)

    # ---- 單閘 -----------------------------------------------------------
    def apply_ry(self, theta, t: int) -> None:
        """theta：純量或形狀 (B,) 的角度陣列（角度編碼／可訓練參數共用）。"""
        th = np.broadcast_to(np.asarray(theta, dtype=np.float64).reshape(-1), (self.batch,))
        c, s = np.cos(th / 2.0), np.sin(th / 2.0)
        apply_1q_ip(self.rho, self.s1, self.s2, c, -s, s, c, t, self.n)

    def apply_rz(self, theta, t: int) -> None:
        th = np.broadcast_to(np.asarray(theta, dtype=np.float64).reshape(-1), (self.batch,))
        z = np.zeros(self.batch, dtype=np.complex128)
        apply_1q_ip(self.rho, self.s1, self.s2,
                    np.exp(-0.5j * th), z, z, np.exp(0.5j * th), t, self.n)

    def apply_mat(self, g, t: int) -> None:
        """施加一般 2x2 閘（純量矩陣或 (B,2,2)）——反向傳播用。"""
        g = np.asarray(g, dtype=np.complex128)
        if g.ndim == 2:
            apply_1q_ip(self.rho, self.s1, self.s2,
                        g[0, 0], g[0, 1], g[1, 0], g[1, 1], t, self.n)
        else:
            apply_1q_ip(self.rho, self.s1, self.s2,
                        g[:, 0, 0], g[:, 0, 1], g[:, 1, 0], g[:, 1, 1], t, self.n)

    def apply_cx(self, control: int, target: int) -> None:
        apply_cx_ip(self.rho, self.s1, control, target, self.n)

    # ---- 通道 -----------------------------------------------------------
    def apply_dephase(self) -> None:
        dephase_ip(self.rho, self.n)

    def apply_depolarize_local(self, p: float) -> None:
        depolarize_ip(self.rho, self.pt, p, self.n)

    # ---- 讀出 -----------------------------------------------------------
    def basis_probs(self) -> np.ndarray:
        idx = np.arange(self.dim)
        return self.rho[:, idx, idx].real

    def class_probs(self) -> np.ndarray:
        """前 3 個 qubit（qubit 0,1,2）的基底模式 → 8 類（與 n 無關）。

        big-endian：平坦索引 = sum_k qubit_k * 2^(n-1-k)，故 qubit 0 是最高位。
        (B, 2^n) -> (B, 8, 2^(n-3)) -> 對最後一軸求和。
        """
        p = self.basis_probs()
        return p.reshape(p.shape[0], N_CLASS, 1 << (self.n - 3)).sum(axis=2)

    def z_expectations(self) -> np.ndarray:
        """每個 qubit 的 <Z_q> = sum_i (-1)^{b_q(i)} rho_ii（形狀 (B, n)）。"""
        p = self.basis_probs()
        idx = np.arange(self.dim).astype(np.float64)
        return np.stack([p @ (1 - 2 * ((idx.astype(np.int64) >> (self.n - 1 - q)) & 1))
                         for q in range(self.n)], axis=1)

    def purity(self) -> np.ndarray:
        return np.real(np.einsum("bij,bji->b", self.rho, self.rho))


# ===========================================================================
# 電路：編碼 → [通道] → 變分層（含環形 CX）→ [通道] → 讀出
# ===========================================================================
def ring(n: int, step: int) -> list:
    """與 s09.probs_for / s12.ring 完全相同的環形 CX 連線。"""
    return [(i, (i + step) % n) for i in range(n)]


def _channel(sim: DensitySim, kind: str, p_dep: float) -> None:
    if kind == "dephase":
        sim.apply_dephase()
    elif kind == "depolarize":
        sim.apply_depolarize_local(p_dep)
    else:
        raise ValueError(kind)


def run_circuit(X: np.ndarray, W: np.ndarray, kind: str, pos, p_dep: float,
                n: int = N_QUBIT, depth: int = DEPTH) -> DensitySim:
    """X：(B,n) 編碼角度；W：(B,depth,n,2) 可訓練角度（可帶批次軸）。

    通道只套用一次，位置 pos = 「已套用幾層之後」；pos == depth
    代表全部層之後（＝測量前）。
    """
    sim = DensitySim(n, X.shape[0])
    for i in range(n):
        sim.apply_ry(X[:, i], i)
    if kind != "none" and pos == 0:
        _channel(sim, kind, p_dep)
    for d in range(depth):
        for i in range(n):
            sim.apply_ry(W[:, d, i, 0], i)
            sim.apply_rz(W[:, d, i, 1], i)
        for c, t in ring(n, 1 if d % 2 == 0 else 2):
            sim.apply_cx(c, t)
        if kind != "none" and pos == d + 1 and pos < depth:
            _channel(sim, kind, p_dep)
    if kind != "none" and pos == depth and depth > 0:
        _channel(sim, kind, p_dep)
    return sim


def class_probs(X: np.ndarray, W: np.ndarray, kind: str, pos, p_dep: float,
                n: int = N_QUBIT, depth: int = DEPTH) -> np.ndarray:
    return run_circuit(X, W, kind, pos, p_dep, n, depth).class_probs()


# ===========================================================================
# 梯度路徑 1：參數平移
# ===========================================================================
def loss_grad(X: np.ndarray, y: np.ndarray, W: np.ndarray, kind: str, pos,
              p_dep: float, n: int = N_QUBIT, depth: int = DEPTH,
              chunk: int = SHIFT_CHUNK):
    """回傳 (cross-entropy loss, grad)。W 是「單一樣本」的權重 (depth,n,2)，
    內部沿批次軸廣播；梯度也回傳同形狀。

    參數平移：對第 k 個角度，dP/dtheta_k = (P(+pi/2) - P(-pi/2)) / 2，
    再乘上 dL/dP 的解析式（**不**直接平移整個損失——那是專案已知的坑）。
    """
    B = X.shape[0]
    W = np.asarray(W, dtype=np.float64)
    Wb = np.tile(W[None], (B, 1, 1, 1))
    flat = Wb.reshape(B, -1)
    npar = flat.shape[1]
    P = class_probs(X, Wb, kind, pos, p_dep, n, depth)
    Pc = np.clip(P, 1e-12, None)
    loss = float(-np.mean(np.log(Pc[np.arange(B), y])))
    dLdP = np.zeros_like(P)
    dLdP[np.arange(B), y] = -1.0 / (Pc[np.arange(B), y] * B)

    grad = np.zeros(npar)
    for start in range(0, npar, chunk):
        ks = list(range(start, min(start + chunk, npar)))
        m = len(ks)
        Xs = np.tile(X, (2 * m + 1, 1))
        Ws = np.tile(flat, (2 * m + 1, 1))
        for j, k in enumerate(ks):
            Ws[(2 * j + 1) * B:(2 * j + 2) * B, k] += np.pi / 2
            Ws[(2 * j + 2) * B:(2 * j + 3) * B, k] -= np.pi / 2
        Ps = class_probs(Xs, Ws.reshape(-1, depth, n, 2), kind, pos, p_dep,
                         n, depth).reshape(2 * m + 1, B, N_CLASS)
        for j, k in enumerate(ks):
            grad[k] = 0.5 * float(np.sum(dLdP * (Ps[2 * j + 1] - Ps[2 * j + 2])))
    # 權重沿批次軸共用，故梯度是「單一樣本」的形狀 (depth, n, 2)，可對 W 廣播。
    return loss, grad.reshape(depth, n, 2)


# ===========================================================================
# 梯度路徑 2：反向模式（adjoint）
# ===========================================================================
def _bit_pairs(t, n):
    """回傳 (jj, kk, pp, qq)：G_t 在計算基底的非零元素 (G_t)_{j,k} = g[p,q]。"""
    dim = 1 << n
    s = n - 1 - t
    base = np.array([m for m in range(dim) if ((m >> s) & 1) == 0])
    jj, kk, pp, qq = [], [], [], []
    for p in (0, 1):
        for q in (0, 1):
            for m in base:
                jj.append(int(m) | (p << s))
                kk.append(int(m) | (q << s))
                pp.append(p)
                qq.append(q)
    return (np.array(jj), np.array(kk), np.array(pp), np.array(qq))


# 梯度抽取用的**生成元**（不是閘本身）：R_Y(theta)=exp(-i theta Y/2)，R_Z 同理用 Z。
_GEN = {"ry": dm._Y, "rz": dm._Z}


def _gen_weights(kindg, t, n):
    """回傳 gg[t] = G 在 (j_t, k_t) 配對上的元素（G 為 Y 或 Z）。"""
    _, _, pp, qq = _bit_pairs(t, n)
    G = _GEN[kindg]
    return np.array([G[p, q] for p, q in zip(pp, qq)])


def loss_grad_adjoint(X: np.ndarray, y: np.ndarray, W: np.ndarray, kind: str, pos,
                      p_dep: float, n: int = N_QUBIT, depth: int = DEPTH):
    """反向模式（adjoint）梯度：一次前向 + 一次反向，取代 2P+1 次前向。

    反向傳遞：
      * 么正閘 U（含編碼，但編碼不需梯度）：sigma <- U^dag sigma U
      * 通道 C：sigma <- C(sigma)（去相位與退極化都是自伴映射，見檔頭說明）
      * 可訓練角度：dL/dtheta = -(i/2) Tr(G [rho_after, sigma_after])

    推導（G 為 Y 或 Z，U = exp(-i theta G/2) 且 [G,U]=0）：
        d rho_after/dtheta = -(i/2) [G, rho_after]
        dL/dtheta = Tr(sigma_after * d rho_after/dtheta)
                  = -(i/2) Tr(sigma [G, rho]) = -(i/2)(Tr(G rho sigma) - Tr(G sigma rho))
    最後一式只需 G 的非零元素，故可 O(B * 2*dim * dim) 算完，不必做矩陣乘法。
    """
    B = X.shape[0]
    dim = 1 << n
    W = np.asarray(W, dtype=np.float64)
    sim = DensitySim(n, B)
    for i in range(n):
        sim.apply_ry(X[:, i], i)

    afters, ops = [], []

    def rec(op):
        afters.append(sim.rho.copy())
        ops.append(op)

    if kind != "none" and pos == 0:
        _channel(sim, kind, p_dep)
        rec(("chan", 0, 0))
    for d in range(depth):
        for i in range(n):
            sim.apply_ry(W[d, i, 0], i)
            rec(("ry", d, i))
            sim.apply_rz(W[d, i, 1], i)
            rec(("rz", d, i))
        for c, t in ring(n, 1 if d % 2 == 0 else 2):
            sim.apply_cx(c, t)
            rec(("cx", c, t))
        if kind != "none" and pos == d + 1 and pos < depth:
            _channel(sim, kind, p_dep)
            rec(("chan", 0, 0))
    if kind != "none" and pos == depth and depth > 0:
        _channel(sim, kind, p_dep)
        rec(("chan", 0, 0))

    P = sim.class_probs()
    Pc = np.clip(P, 1e-12, None)
    loss = float(-np.mean(np.log(Pc[np.arange(B), y])))
    dLdP = np.zeros_like(P)
    dLdP[np.arange(B), y] = -1.0 / (Pc[np.arange(B), y] * B)

    # 讀出泛函 L = Tr(M rho)：M 在 (class, rest) 分解下是實對角矩陣
    M = np.zeros((B, dim, dim), dtype=np.complex128)
    idx = np.arange(dim)
    M[:, idx, idx] = dLdP[:, idx >> (n - 3)]
    sigma = M

    # 梯度抽取用的暫存（避免每次配置）
    T = 4 * (dim // 2)          # G_t 的 non-zero 個數 = 4 * 2^(n-1)
    Xb = np.empty((B, T, dim), dtype=np.complex128)
    Yb = np.empty((B, dim, T), dtype=np.complex128)
    pairs = {t: _bit_pairs(t, n) for t in range(n)}
    ggs = {(kg, t): _gen_weights(kg, t, n) for kg in ("ry", "rz") for t in range(n)}
    ssim = DensitySim(n, B)     # 反向傳遞用的 sigma 容器（緩衝區可重用）
    del ssim.rho
    ssim.rho = sigma

    grad = np.zeros((depth, n, 2))

    def trG_AB(A, Bm, t, gg):
        jj, kk = pairs[t][0], pairs[t][1]
        np.take(A, kk, axis=1, out=Xb)
        np.take(Bm, jj, axis=2, out=Yb)
        # 必須保留複數值：Tr(G A B) 本身是複數，只有 Tr(G [rho,sigma]) 才是純虛數。
        return complex(np.sum(np.einsum("btm,bmt->bt", Xb, Yb) * gg[None, :]))

    for k in range(len(ops) - 1, -1, -1):
        op = ops[k]
        rho_a = afters[k]
        if op[0] == "ry":
            _, d, i = op
            gg = ggs[("ry", i)]                       # 生成元 Y 的元素
            grad[d, i, 0] = (-0.5j * (trG_AB(rho_a, sigma, i, gg)
                                      - trG_AB(sigma, rho_a, i, gg))).real
            ssim.apply_mat(dm.ry(float(W[d, i, 0])).conj().T, i)
        elif op[0] == "rz":
            _, d, i = op
            gg = ggs[("rz", i)]                       # 生成元 Z 的元素
            grad[d, i, 1] = (-0.5j * (trG_AB(rho_a, sigma, i, gg)
                                      - trG_AB(sigma, rho_a, i, gg))).real
            ssim.apply_mat(dm.rz(float(W[d, i, 1])).conj().T, i)
        elif op[0] == "cx":
            _, c, t = op
            ssim.apply_cx(c, t)
        else:                                  # 通道（自伴）
            _channel(ssim, kind, p_dep)
    return loss, grad


GRAD_FUNCS = {"adjoint": loss_grad_adjoint, "paramshift": loss_grad}


# ===========================================================================
# 退極化強度的等純度校準（二分法）
# ===========================================================================
def encoded_purity_and_depolarized(X: np.ndarray, p: float = None, n: int = N_QUBIT):
    """回傳 (去相位後平均純度, 退極化 p 後平均純度)——插入點是純乘積態。

    插入點在**編碼層後**，該處的態只依賴輸入 x、**不依賴可訓練參數**，
    所以校準出來的 p 在整個訓練過程中都成立（不是「只在初始化時成立」）。
    """
    sim = DensitySim(n, X.shape[0])
    for i in range(n):
        sim.apply_ry(X[:, i], i)
    out = [float(np.mean(sim.purity()))]
    sim.apply_dephase()
    out.append(float(np.mean(sim.purity())))
    if p is not None:
        s2 = DensitySim(n, X.shape[0])
        for i in range(n):
            s2.apply_ry(X[:, i], i)
        s2.apply_depolarize_local(p)
        out.append(float(np.mean(s2.purity())))
    return out


def calibrate_depolarizing_p(X: np.ndarray, n: int = N_QUBIT):
    """二分法找 p，使通道後**平均純度**等於去相位後的平均純度。

    插入點的態是 5 個 qubit 的**純乘積態**，故有閉式解可交叉驗證：
      去相位後   Tr[rho^2] = prod_q (cos^4(theta_q/2) + sin^4(theta_q/2))
      退極化後   Tr[rho^2] = (1 - p + p^2/2)^5
    解 (1-p+p^2/2)^5 = T 得 p = 1 - sqrt(2 T^(1/5) - 1)。
    """
    _, target = encoded_purity_and_depolarized(X, None, n)

    def purity_at(p):
        return encoded_purity_and_depolarized(X, p, n)[2]

    lo, hi = 0.0, 1.0
    trace, p = [], 0.5
    for it in range(BISECT_ITERS):
        p = 0.5 * (lo + hi)
        val = purity_at(p)
        trace.append(dict(it=it, p=p, purity=val, diff=val - target))
        if abs(val - target) < BISECT_TOL:
            break
        if val > target:
            lo = p
        else:
            hi = p
    T = target ** (1.0 / n)
    p_closed = 1.0 - math.sqrt(max(2.0 * T - 1.0, 0.0))
    return dict(target_purity=target, p=p, p_closed_form=p_closed,
                purity_at_p=purity_at(p), trace=trace)


# ===========================================================================
# 指標
# ===========================================================================
def ece(P: np.ndarray, y: np.ndarray, bins: int = ECE_BINS) -> float:
    """期望校準誤差（M 等寬分箱）——與 s12/s16 完全相同的實作。"""
    conf, pred = P.max(axis=1), P.argmax(axis=1)
    hit = (pred == y).astype(float)
    edges, out = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            out += float(m.mean()) * abs(hit[m].mean() - conf[m].mean())
    return float(out)


def nll(P: np.ndarray, y: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, None))))


def brier(P: np.ndarray, y: np.ndarray) -> float:
    E = np.zeros_like(P)
    E[np.arange(len(y)), y] = 1.0
    return float(np.mean(np.sum((P - E) ** 2, axis=1)))


def collapse_metrics(P: np.ndarray, Z: np.ndarray, purity: np.ndarray) -> dict:
    """塌縮／退化指標（Ghosh 等 2026 的警告要求的欄位）。

    + mean_max_prob        ：平均最大預測機率（信心）
    + n_distinct_classes   ：測試樣本中出現過的相異預測類別數（滿分 8）
    + majority_frac        ：被預測成最常見那一類的比例（退化解指標）
    + kl_meanpred_uniform  ：**平均預測分布**與均勻分布的 KL（nat）
    + kl_persample_mean    ：每個樣本自己的預測分布與均勻分布的 KL 平均（nat）
    + mean_entropy         ：平均預測熵（nat）
    + z_var_per_qubit      ：各 qubit 的 <Z_i> 在測試集上的變異數
    + z_var_mean           ：上面 5 個變異數的平均
    + z_absmean            ：平均 |<Z_i>|
    + mean_purity          ：讀出點的平均純度 Tr[rho^2]
    """
    conf = P.max(axis=1)
    pred = P.argmax(axis=1)
    u = np.full(N_CLASS, 1.0 / N_CLASS)
    pbar = P.mean(axis=0)
    counts = np.bincount(pred, minlength=N_CLASS).astype(float)
    zvar = Z.var(axis=0)
    return dict(
        mean_max_prob=float(conf.mean()),
        n_distinct_classes=int((counts > 0).sum()),
        majority_frac=float(counts.max() / len(pred)),
        kl_meanpred_uniform=float(np.sum(pbar * np.log(np.clip(pbar, 1e-12, None) / u))),
        kl_persample_mean=float(np.mean(np.sum(P * np.log(np.clip(P, 1e-12, None) / u),
                                                axis=1))),
        mean_entropy=float(np.mean(-np.sum(P * np.log(np.clip(P, 1e-12, None)), axis=1))),
        z_var_per_qubit=[float(v) for v in zvar],
        z_var_mean=float(zvar.mean()),
        z_absmean=float(np.mean(np.abs(Z))),
        mean_purity=float(np.mean(purity)),
        pred_class_counts=[int(c) for c in counts],
    )


def evaluate(X: np.ndarray, y: np.ndarray, W: np.ndarray, kind: str, pos,
             p_dep: float):
    Wb = np.tile(np.asarray(W, dtype=np.float64)[None], (X.shape[0], 1, 1, 1))
    sim = run_circuit(X, Wb, kind, pos, p_dep)
    P = sim.class_probs()
    m = collapse_metrics(P, sim.z_expectations(), sim.purity())
    m.update(test_acc=float((P.argmax(1) == y).mean()), ece=ece(P, y),
             nll=nll(P, y), brier=brier(P, y))
    return m, P


# ===========================================================================
# 正確性檢查（preflight）——臂 C no-op 是硬門檻
# ===========================================================================
def preflight(Xtr: np.ndarray, ytr: np.ndarray, n: int, depth: int) -> dict:
    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append(dict(name=name, ok=bool(ok), detail=detail))
        print("  [%s] %s   %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    rng = np.random.default_rng(20260920)
    dim = 1 << n
    psi = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    psi /= np.linalg.norm(psi)
    rho0 = np.outer(psi, psi.conj())

    # 1. 本檔的去相位 == dmtools 的去相位 == 投影子求和形式
    sim = DensitySim(n, 1)
    sim.rho = rho0[None].copy()
    sim.apply_dephase()
    mine = sim.rho[0]
    ref = dm.dephase(rho0, n)
    ref2 = dm.dephase_sum_form(rho0, n)
    check("去相位實作 == dmtools.dephase（遮罩形式）",
          np.max(np.abs(mine - ref)) < 1e-14, "max|d| = %.3e" % np.max(np.abs(mine - ref)))
    check("dmtools.dephase == dephase_sum_form（Kraus 求和形式）",
          np.max(np.abs(ref - ref2)) < 1e-14, "max|d| = %.3e" % np.max(np.abs(ref - ref2)))
    check("去相位保跡、Hermitian 保持、非對角元歸零",
          abs(np.trace(mine).real - 1) < 1e-13
          and np.max(np.abs(mine - mine.conj().T)) < 1e-14
          and np.max(np.abs(mine - np.diag(np.diag(mine)))) < 1e-14,
          "Tr = %.12f" % np.trace(mine).real)

    # 2. 本檔的密度矩陣模擬器（無通道）== s09 的狀態向量模擬器
    s09.DEPTH = depth
    W1 = rng.normal(0.0, 0.4, size=(depth, n, 2))
    X1 = rng.random((6, n))
    p_mine = class_probs(X1, np.tile(W1[None], (6, 1, 1, 1)), "none", None, 0.0, n, depth)
    p_s09 = s09.probs_for(n, X1, W1)
    d2 = float(np.max(np.abs(p_mine - p_s09)))
    check("密度矩陣模擬器 == s09 狀態向量模擬器（無通道）", d2 < 1e-12, "max|dP| = %.3e" % d2)

    # 3. ★ 臂 C 必須是精確 no-op
    X2 = Xtr[:16]
    W2 = np.tile(rng.normal(0.0, 0.4, size=(depth, n, 2))[None], (16, 1, 1, 1))
    pA = class_probs(X2, W2, "none", None, 0.0)
    pC = class_probs(X2, W2, "dephase", depth, 0.0)
    d3 = float(np.max(np.abs(pA - pC)))
    check("★ 臂 C（尾端去相位）對 8 類機率是精確 no-op",
          d3 < PREFLIGHT_TOL_ARM_C,
          "max|P_C - P_A| = %.3e（門檻 %.0e）" % (d3, PREFLIGHT_TOL_ARM_C))
    d3b = float(np.max(np.abs(run_circuit(X2, W2, "none", None, 0.0).basis_probs()
                              - run_circuit(X2, W2, "dephase", depth, 0.0).basis_probs())))
    check("★ 臂 C 對 32 維 Born 機率也是精確 no-op",
          d3b < PREFLIGHT_TOL_ARM_C, "max|dp| = %.3e" % d3b)

    # 4. 臂 B 必須**不**是 no-op（否則實驗沒東西可量）
    pB = class_probs(X2, W2, "dephase", 0, 0.0)
    d4 = float(np.max(np.abs(pA - pB)))
    check("臂 B（編碼層後去相位）確實改變機率（非 no-op）", d4 > 1e-6,
          "max|P_B - P_A| = %.6f" % d4)

    # 5. 么模仿塊閘與去相位交換：去相位後只接 RZ + CX，機率必須與不去相位相同
    WZ = np.zeros((16, depth, n, 2))
    WZ[..., 1] = rng.normal(0.0, 0.7, size=(16, depth, n))
    d5 = float(np.max(np.abs(class_probs(X2, WZ, "none", None, 0.0)
                             - class_probs(X2, WZ, "dephase", 0, 0.0))))
    check("去相位後只接 RZ+CX 時機率不變（T5：么模仿塊閘與 D 交換）",
          d5 < 1e-13, "max|dp| = %.3e" % d5)

    # 6. 等純度校準：二分法 == 閉式解；且公式 1-p+p^2/2 成立
    cal = calibrate_depolarizing_p(Xtr)
    d6 = abs(cal["p"] - cal["p_closed_form"])
    check("退極化等純度校準：二分法 == 閉式解", d6 < 1e-10,
          "p_bisect = %.12f  p_closed = %.12f  |d| = %.3e"
          % (cal["p"], cal["p_closed_form"], d6))
    check("校準後純度確實匹配", abs(cal["purity_at_p"] - cal["target_purity"]) < 1e-12,
          "目標 = %.12f  達成 = %.12f" % (cal["target_purity"], cal["purity_at_p"]))
    s = DensitySim(1, 1)
    pp = 0.37
    s.apply_depolarize_local(pp)
    check("單 qubit 退極化純度公式 Tr[rho^2] -> 1-p+p^2/2",
          abs(float(s.purity()[0]) - (1 - pp + pp ** 2 / 2)) < 1e-15,
          "|d| = %.3e" % abs(float(s.purity()[0]) - (1 - pp + pp ** 2 / 2)))

    # 7. 梯度三方對帳：參數平移 vs 中心差分 vs adjoint
    Xg, yg = Xtr[:6], ytr[:6]
    Wg = rng.normal(0.0, 0.3, size=(depth, n, 2))

    def L(wmat):
        P = class_probs(Xg, np.tile(wmat[None], (6, 1, 1, 1)), "dephase", 0, 0.0)
        return float(-np.mean(np.log(np.clip(P[np.arange(6), yg], 1e-12, None))))

    _, g_ps = loss_grad(Xg, yg, Wg, "dephase", 0, cal["p"])
    h, worst = 1e-6, 0.0
    for k in rng.choice(Wg.size, size=8, replace=False):
        wp, wm = Wg.copy(), Wg.copy()
        wp.reshape(-1)[k] += h
        wm.reshape(-1)[k] -= h
        worst = max(worst, abs((L(wp) - L(wm)) / (2 * h) - g_ps.reshape(-1)[k]))
    check("參數平移梯度 == 中心差分（臂 B，通道在電路中間）", worst < 1e-6,
          "max abs err = %.3e" % worst)

    grad_report = {}
    for tag, kk_, pp_ in (("A", "none", None), ("B", "dephase", 0),
                          ("C", "dephase", depth), ("D", "depolarize", 0)):
        _, g1 = loss_grad(Xg, yg, Wg, kk_, pp_, cal["p"])
        _, g2 = loss_grad_adjoint(Xg, yg, Wg, kk_, pp_, cal["p"])
        scale = max(float(np.max(np.abs(g1))), 1e-30)
        rel = float(np.max(np.abs(g1 - g2))) / scale
        grad_report[tag] = rel
        check("adjoint 梯度 == 參數平移梯度（臂 %s）" % tag, rel < PREFLIGHT_TOL_GRAD,
              "rel err = %.3e" % rel)

    # 8. 臂 C 的梯度必須與臂 A 完全相同（no-op 在梯度層級也成立）
    _, gA = loss_grad_adjoint(Xg, yg, Wg, "none", None, cal["p"])
    _, gC = loss_grad_adjoint(Xg, yg, Wg, "dephase", depth, cal["p"])
    d8 = float(np.max(np.abs(gA - gC)))
    check("★ 臂 C 的 adjoint 梯度 == 臂 A（0 差值）", d8 < 1e-15, "max|dg| = %.3e" % d8)

    return dict(checks=checks, all_pass=all(c["ok"] for c in checks),
                arm_c_max_dp=d3, arm_c_max_dp_basis=d3b, arm_b_max_dp=d4,
                gradient_rel_err=grad_report,
                calibration=dict(target_purity=cal["target_purity"], p=cal["p"],
                                 p_closed_form=cal["p_closed_form"]))


# ===========================================================================
# 主流程
# ===========================================================================
def ci95(xs):
    """平均、半寬（t_{0.975,df=4} * s / sqrt(n)）、標準差。"""
    a = np.asarray(xs, dtype=float)
    m, sd = float(a.mean()), (float(a.std(ddof=1)) if len(a) > 1 else 0.0)
    half = T975_DF4 * sd / math.sqrt(len(a)) if len(a) > 1 else 0.0
    return m, half, sd


def main() -> int:
    global DEPTH, CHANNEL_POS_END
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seeds", default=",".join(str(s) for s in SEEDS))
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--lr", type=float, default=LR)
    ap.add_argument("--depth", type=int, default=DEPTH)
    ap.add_argument("--grad", default=GRADIENT, choices=sorted(GRAD_FUNCS))
    ap.add_argument("--out", default=str(OUT_JSON))
    args = ap.parse_args()
    steps, lr, depth = args.steps, args.lr, args.depth
    alias = {k[0]: k for k in ARMS}
    arms = [alias.get(a.strip(), a.strip()) for a in args.arms.split(",") if a.strip()]
    for a in arms:
        if a not in ARMS:
            raise SystemExit("未知的臂 %r；可用：%s（或簡寫 A/B/C/D）" % (a, list(ARMS)))
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    DEPTH = depth
    CHANNEL_POS_END = depth
    ARMS["C_dephase_end"]["pos"] = depth
    gfun = GRAD_FUNCS[args.grad]

    t_all = time.perf_counter()
    print("=" * 96)
    print("s17：去相位（古典化）消融 — RQ2")
    print("  %d qubit、%d 類、depth=%d、參數 %d 個、Adam lr=%g、%d 步、%d 個種子、梯度=%s"
          % (N_QUBIT, N_CLASS, depth, 2 * depth * N_QUBIT, lr, steps, len(seeds), args.grad))
    print("  臂：%s" % arms)
    print("=" * 96)

    Z_tr, y_tr, Z_te, y_te = s09.make_data(DATA_SEED)
    Xtr = s09.encode(Z_tr[:, :N_QUBIT])
    Xte = s09.encode(Z_te[:, :N_QUBIT])
    chance = 1.0 / N_CLASS
    print("  資料：s09.make_data(%d)；訓練 %d／測試 %d；隨機猜測 = %.4f"
          % (DATA_SEED, Xtr.shape[0], Xte.shape[0], chance))

    print("\n--- 正確性檢查（preflight）---")
    pf = preflight(Xtr, y_tr, N_QUBIT, depth)
    print("  => %d/%d 項通過；臂 C 最大機率偏差 = %.3e"
          % (sum(c["ok"] for c in pf["checks"]), len(pf["checks"]), pf["arm_c_max_dp"]))
    if not pf["all_pass"]:
        failed = [c["name"] for c in pf["checks"] if not c["ok"]]
        print("\n  !! preflight 未全數通過，未過項目：%s" % failed)
        if not [c for c in pf["checks"]
                if c["name"].startswith("★ 臂 C") and not c["ok"]]:
            print("     （臂 C no-op 本身通過；失敗在其餘檢查。）")
        else:
            print("     ★ 臂 C 不是 no-op => 去相位的實作位置或定義有問題，"
                  "依硬規則**停止**，不繼續往下跑。")
        return 2
    print("  => 臂 C 確認為精確 no-op，繼續。", flush=True)

    print("\n--- 退極化等強度校準（二分法，目標：通道後平均純度 == 去相位後）---")
    cal = calibrate_depolarizing_p(Xtr)
    print("  編碼後（純態）平均純度 = %.12f；去相位後平均純度 T = %.12f"
          % (encoded_purity_and_depolarized(Xtr)[0], cal["target_purity"]))
    print("  %4s %18s %18s %15s" % ("迭代", "p", "通道後純度", "與目標差"))
    for t in cal["trace"][:6] + cal["trace"][-3:]:
        print("  %4d %18.12f %18.12f %+15.3e" % (t["it"], t["p"], t["purity"], t["diff"]))
    print("  => p = %.12f（閉式解 %.12f，誤差 %.3e）；Pauli 錯誤率 q = 4p/3 = %.6f"
          % (cal["p"], cal["p_closed_form"], abs(cal["p"] - cal["p_closed_form"]),
             4 * cal["p"] / 3))
    p_dep = cal["p"]

    if args.preflight_only:
        print("\n  --preflight-only：總耗時 %.1f s" % (time.perf_counter() - t_all))
        return 0

    print("\n--- 訓練掃描：%d 臂 x %d 種子 = %d 次 ---"
          % (len(arms), len(seeds), len(arms) * len(seeds)))
    print("  %-18s%5s%9s%9s%9s%9s%10s%8s%9s%9s%8s"
          % ("臂", "種子", "訓練", "測試", "ECE", "NLL", "最大機率", "類別數", "KL", "VarZ", "秒"),
          flush=True)
    rows, t0_all = [], time.perf_counter()
    for arm in arms:
        spec = ARMS[arm]
        for seed in seeds:
          try:
            rng = np.random.default_rng(seed)
            W = rng.normal(0.0, W_INIT_STD, size=(depth, N_QUBIT, 2))
            m = np.zeros_like(W)
            v = np.zeros_like(W)
            hist, t0 = [], time.perf_counter()
            for step in range(1, steps + 1):
                loss, g = gfun(Xtr, y_tr, W, spec["kind"], spec["pos"], p_dep)
                m = BETA1 * m + (1 - BETA1) * g
                v = BETA2 * v + (1 - BETA2) * g * g
                mh = m / (1 - BETA1 ** step)
                vh = v / (1 - BETA2 ** step)
                W = W - lr * mh / (np.sqrt(vh) + EPS_ADAM)
                if step % 50 == 0 or step == steps:
                    hist.append(dict(step=step, loss=round(loss, 6)))
            dt = time.perf_counter() - t0
            tr_m, _ = evaluate(Xtr, y_tr, W, spec["kind"], spec["pos"], p_dep)
            te_m, _ = evaluate(Xte, y_te, W, spec["kind"], spec["pos"], p_dep)
            row = dict(arm=arm, label=spec["label"], kind=spec["kind"], pos=spec["pos"],
                       seed=seed, depth=depth, n_qubit=N_QUBIT,
                       n_trainable=2 * depth * N_QUBIT,
                       p_depolarizing=(p_dep if spec["kind"] == "depolarize" else None),
                       train_acc=round(tr_m["test_acc"], 6),
                       train_ece=round(tr_m["ece"], 6),
                       train_nll=round(tr_m["nll"], 6),
                       train_loss=round(float(hist[-1]["loss"]), 6) if hist else None,
                       loss_history=hist, seconds=round(dt, 3))
            row.update({k: (round(vv, 6) if isinstance(vv, float) else vv)
                        for k, vv in te_m.items()})
            rows.append(row)
            # 逐列寫出部分結果：長跑中斷也不會全部遺失
            op = pathlib.Path(args.out)
            op.parent.mkdir(parents=True, exist_ok=True)
            op.write_text(json.dumps(dict(experiment="s17_dephasing_ablation",
                                          partial=True, generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                                          config=dict(n_qubit=N_QUBIT, n_class=N_CLASS, depth=depth,
                                                      steps=steps, lr=lr, seeds=list(seeds),
                                                      arms=arms, data_seed=DATA_SEED, chance=chance,
                                                      gradient=args.grad),
                                          preflight=pf,
                                          calibration=dict(p=cal["p"], target_purity=cal["target_purity"],
                                                           p_closed_form=cal["p_closed_form"],
                                                           trace=cal["trace"]),
                                          rows=rows), indent=1, ensure_ascii=False),
                      encoding="utf-8")
            print("  %-18s%5d%9.4f%9.4f%9.4f%9.4f%10.4f%8d%9.4f%9.4f%8.1f"
                  % (arm, seed, row["train_acc"], row["test_acc"], row["ece"], row["nll"],
                     row["mean_max_prob"], row["n_distinct_classes"],
                     row["kl_meanpred_uniform"], row["z_var_mean"], dt), flush=True)
          except Exception as exc:      # 單一 (臂, 種子) 失敗不應毀掉整個掃描
            import traceback
            traceback.print_exc()
            rows.append(dict(arm=arm, label=spec["label"], seed=seed, depth=depth,
                             n_qubit=N_QUBIT, error="%s: %s" % (type(exc).__name__, exc),
                             seconds=None))
            print("  %-18s%5d  ** 失敗：%s: %s" % (arm, seed, type(exc).__name__, exc),
                  flush=True)
        s = [r for r in rows if r["arm"] == arm]
        print("      -> %-18s train %.4f | test %.4f | ECE %.4f | VarZ %.4f"
              % (arm, np.mean([r["train_acc"] for r in s]),
                 np.mean([r["test_acc"] for r in s]),
                 np.mean([r["ece"] for r in s]),
                 np.mean([r["z_var_mean"] for r in s])), flush=True)

    # ---- 彙總 ----------------------------------------------------------
    metrics = ["train_acc", "train_ece", "train_nll", "test_acc", "ece", "nll", "brier",
               "mean_max_prob", "n_distinct_classes", "majority_frac",
               "kl_meanpred_uniform", "kl_persample_mean", "mean_entropy",
               "z_var_mean", "z_absmean", "mean_purity", "seconds"]
    aggregate = {}
    for arm in arms:
        s = [r for r in rows if r["arm"] == arm]
        aggregate[arm] = {k: dict(mean=float(np.mean([r[k] for r in s])),
                                  std=(float(np.std([r[k] for r in s], ddof=1))
                                       if len(s) > 1 else 0.0),
                                  values=[float(r[k]) for r in s])
                          for k in metrics if k in s[0]}
        aggregate[arm]["label"] = ARMS[arm]["label"]

    def paired(arm_x, arm_y, keys):
        out = {}
        for k in keys:
            dx = [r[k] for r in rows if r["arm"] == arm_x]
            dy = [r[k] for r in rows if r["arm"] == arm_y]
            if len(dx) != len(dy) or not dx:
                continue
            mm, half, sd = ci95([a - b for a, b in zip(dy, dx)])
            out[k] = dict(mean=float(mm), ci95_half=float(half), std=float(sd),
                          sig=bool(abs(mm) > half and half > 0))
        return out

    pkeys = ["test_acc", "ece", "nll", "mean_max_prob", "n_distinct_classes",
             "majority_frac", "kl_meanpred_uniform", "kl_persample_mean",
             "z_var_mean", "mean_purity"]
    paired_B_A = paired("A_baseline", "B_dephase_front", pkeys)
    paired_D_B = paired("B_dephase_front", "D_depolar_front", pkeys)
    paired_C_A = (paired("A_baseline", "C_dephase_end", pkeys)
                  if "C_dephase_end" in arms else {})

    verdict = {}
    if paired_B_A:
        e = paired_B_A["ece"]
        improves = bool(e["mean"] < 0 and abs(e["mean"]) > e["ci95_half"])
        coll = dict(
            mean_max_prob=bool(paired_B_A["mean_max_prob"]["mean"] > 0),
            n_distinct_classes=bool(paired_B_A["n_distinct_classes"]["mean"] < 0),
            majority_frac=bool(paired_B_A["majority_frac"]["mean"] > 0),
            kl_meanpred_uniform=bool(paired_B_A["kl_meanpred_uniform"]["mean"] > 0),
            z_var_mean=bool(paired_B_A["z_var_mean"]["mean"] < 0),
        )
        verdict["B_vs_A_ece_improves"] = improves
        verdict["B_vs_A_collapse_signals"] = coll
        verdict["B_vs_A_collapse_any"] = bool(any(coll.values()))
        verdict["RQ2_rule1"] = ("ECE 改善但伴隨塌縮指標惡化 => 改善不得歸因於量子性"
                                if (improves and any(coll.values())) else
                                "ECE 未顯著改善，或未伴隨塌縮惡化 => 規則 1 不觸發")
    if paired_D_B:
        same = {}
        for k in ["test_acc", "ece", "nll"]:
            d = paired_D_B[k]
            same[k] = bool(d["ci95_half"] > 0 and abs(d["mean"]) <= d["ci95_half"])
        verdict["D_vs_B_within_noise"] = same
        verdict["H2_rule2"] = ("D 與 B 在 95% CI 內無差異 => 效果來自雜訊而非失去相干性，"
                               "H2 不成立" if all(same.values()) else
                               "D 與 B 至少一項指標有顯著差異 => 規則 2 不觸發")
    if paired_C_A:
        verdict["arm_C_equals_A_max_abs_metric_diff"] = float(
            max(abs(paired_C_A[k]["mean"]) for k in paired_C_A))

    print("\n--- 四臂彙總（平均 ± 標準差，n=%d 個種子）---" % len(seeds))
    cols = ["test_acc", "ece", "nll", "mean_max_prob", "n_distinct_classes",
            "kl_meanpred_uniform", "z_var_mean", "mean_purity"]
    print("  %-18s" % "臂" + "".join("%13s" % c[:11] for c in cols))
    for arm in arms:
        a = aggregate[arm]
        print("  %-18s" % arm + "".join("%7.4f±%.4f" % (a[c]["mean"], a[c]["std"])
                                        for c in cols))
    if paired_B_A:
        print("\n  配對差（B - A，95% CI 含 0 即不顯著）：")
        for k in ["ece", "test_acc", "nll", "mean_max_prob", "n_distinct_classes",
                  "z_var_mean"]:
            if k not in paired_B_A:
                continue
            d = paired_B_A[k]
            print("    %-24s %+9.4f ± %.4f   %s"
                  % (k, d["mean"], d["ci95_half"], "顯著" if d["sig"] else "不顯著"))
    if paired_D_B:
        print("  配對差（D - B，用來判定『雜訊即正則化』）：")
        for k in ["ece", "test_acc", "nll", "mean_max_prob", "z_var_mean"]:
            if k not in paired_D_B:
                continue
            d = paired_D_B[k]
            print("    %-24s %+9.4f ± %.4f   %s"
                  % (k, d["mean"], d["ci95_half"], "顯著" if d["sig"] else "不顯著"))
    print("\n  判定：")
    for k, v in verdict.items():
        print("    %s: %s" % (k, v))

    out = dict(experiment="s17_dephasing_ablation",
               generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
               config=dict(n_qubit=N_QUBIT, n_class=N_CLASS, depth=depth,
                           n_trainable=2 * depth * N_QUBIT, steps=steps, lr=lr,
                           seeds=list(seeds), arms=arms, data_seed=DATA_SEED,
                           n_train=int(Xtr.shape[0]), n_test=int(Xte.shape[0]),
                           chance=chance, weight_init_std=W_INIT_STD,
                           channel_pos_front=CHANNEL_POS_FRONT,
                           channel_pos_end=CHANNEL_POS_END, ece_bins=ECE_BINS,
                           gradient=args.grad,
                           gradient_note=("adjoint (reverse mode); cross-checked against "
                                          "parameter shift and central differences"),
                           simulator="density matrix 2^n x 2^n (numpy, big-endian, "
                                     "allocation-free in-place kernels)",
                           readout="qubits 0,1,2 -> 8 classes (as in s09/s12)"),
               channel_semantics=dict(
                   dephase="D_S(rho) = sum_b P_b rho P_b; mask from dmtools.dephase_mask",
                   depolarize="E_t(rho) = (1-p) rho + p Tr_t[rho] (x) I/2, all qubits",
                   depolarize_pauli_rate="q = 4p/3",
                   matched_quantity="mean purity Tr[rho^2] after the channel"),
               preflight=pf,
               calibration=dict(target_purity=cal["target_purity"], p=cal["p"],
                                p_closed_form=cal["p_closed_form"],
                                purity_at_p=cal["purity_at_p"], trace=cal["trace"]),
               rows=rows, aggregate=aggregate,
               paired_B_minus_A=paired_B_A, paired_D_minus_B=paired_D_B,
               paired_C_minus_A=paired_C_A, verdict=verdict,
               total_seconds=round(time.perf_counter() - t0_all, 1))
    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n  已寫出 %s；總耗時 %.1f s" % (outp, time.perf_counter() - t_all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
