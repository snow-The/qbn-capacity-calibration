"""s18：有效維度（effective dimension）補強實驗 —— 把已量到的容量曲線接上既有理論架構。

## 為什麼要做這個實驗（來源：研究搜尋/00-碰撞處置4-RQ1縮放已被佔位.md）

s16 已量到：深度是唯一有效的軸（L=1→8 讓 test 由 0.13 升到 0.62），qubit 數反而有害
（峰值在 n=4、n=10 掉到 0.49），而且 train 準確率不降反升（n=8,L=8 達 0.8375）⇒ 不是最佳化失敗。
theory/verify/t3_entanglement_barren.py 又已排除貧瘠高原。於是候選解釋是：

    有效維度（effective dimension）的增速超過資料量與讀出所能支撐的程度。

本檔把這個解釋變成可量測的數字：對每個 (n, L) 算 normalized effective dimension。

## 我實作的定義版本（可追溯）

**出處 A**：Abbas, Sutter, Figalli, Woerner, *Effective dimension of machine learning models*,
arXiv:2112.04807（Definition 1「global effective dimension」、Definition 2「local effective dimension」）。

**出處 B**：Abbas, Sutter, Zoufal, Lucchi, Figalli, Woerner, *The power of quantum neural networks*,
arXiv:2011.00027（effective dimension 的原始定義，eq. (4)；本檔的公式與其一致）。

原文定義（照抄，僅改符號排版）：

    kappa_{n,gamma} = gamma * n / (2 * pi * log n)
    F(theta)_{ij}   = E_{(x,y)~p}[ d_i log p(x,y;theta) * d_j log p(x,y;theta) ]      （Fisher 資訊矩陣）
    Fbar(theta)     = d * V / ( integral_Region tr(F(theta)) dtheta ) * F(theta)      （正規化，使 tr 的平均 = d）
    d_{n,gamma}(M_Region) = 2 * log( (1/V) * integral_Region sqrt(det(I_d + kappa * Fbar(theta))) dtheta )
                            / log(kappa)
    normalized:  dbar = d_{n,gamma} / d          （d = 可訓練參數個數）

**Region 的兩種取法**：
  * global（出處 A Def.1）：Region = Theta，本檔取 Theta = [-1,1]^d（與出處 B Theorem 4 的假設一致）。
  * local（出處 A Def.2）：Region = B_eps(theta*) = {theta : ||theta - theta*|| <= eps}，
    eps > 1/sqrt(n)，原文實驗取 eps = 1/sqrt(n)；本檔沿用 eps = 1/sqrt(n)，theta* = 訓練後參數。

**我實際算的近似（原文附錄 C 明載的兩條，逐條標明）**：
  (A1) **中點近似（midpoint approximation）**：略去 Region 上的積分，直接在 theta* 取值。
       原文附錄 C 第一條明載此近似，並用 Table 3 驗證（中點 0.21815588 vs 1000 取樣 0.21815838，
       相對差 ~1e-5）。本檔照做，並另外用蒙地卡羅在 eps-球內取樣作為**獨立驗證列**（不是替代）。
  (A2) **經驗 Fisher（empirical Fisher）近似**：原文用 K-FAC 近似 F。我們的 d <= 160，直接算**精確**
       Jacobian，不需要 K-FAC。因此本檔的 Fisher 比原文更精確，但**少了** K-FAC 這個誤差來源。
  其餘照原文：gamma = 1、n = 訓練樣本數（= s09.N_TRAIN = 80）、log 為自然對數
  （原文註腳「n >= 19 才能保證 2*pi*log n < n」只在自然對數下吻合：2*pi*ln(20)=18.8 < 20）。
  數值上用原文 Remark 2 的 z(theta) 穩定式：
        z(theta) = 0.5 * sum_i log(1 + kappa * lambda_i(Fbar(theta)))
        d_{n,gamma} = 2*zeta/log(kappa) + (2/log(kappa)) * log( (1/V) integral exp(z(theta)-zeta) dtheta )
  其中 zeta = max_theta z(theta)。

**F 的三個版本（本檔全部計算並互相比較；Proposition 2 說 d_eff 對 F 連續，正好可以檢查）**：
  * JJ  —— F = J^T J，J = 模型輸出對參數的 Jacobian（**任務指定的版本，也是本檔主結果**）。
           對 8 類輸出即 F = E_x[ sum_c grad p_c grad p_c^T ]。
  * FIM —— 原文定義的精確 Fisher：F = E_x[ sum_c (1/p_c) grad p_c grad p_c^T ]（因為 grad log p_c = grad p_c / p_c）。
  * EMP —— 原文附錄 C 的經驗 Fisher：F = (1/N) sum_i (grad p_{y_i}/p_{y_i})(grad p_{y_i}/p_{y_i})^T，用真實標籤。

## 結構提醒（會影響結果解讀，先寫在前面）

Σ_c p_c = 1 恆成立 ⇒ Σ_c grad p_c = 0 ⇒ **單一樣本**的 Jacobian J_x（8×d）秩 ≤ 7。
但本檔的 Fisher 是對輸入分布取平均的 F = (1/N) Σ_x J_x^T J_x，其秩上限是 min(d, 7N)；
N=80、d ≤ 160 ⇒ **沒有有效上限**。也就是說「讀出只有 8 類」並不對 d_eff 造成硬上限，
每多一個樣本就最多多 7 個新方向 —— 這正是「資料量決定能解析多少容量」的來源。
本檔把兩件事都印出來驗證：單樣本的 Σ_c grad p_c = 0，以及聚合 F 的實際秩。

梯度＝torch autograd 穿過 s12 的批次狀態向量模擬器（s12 已對帳：機率 vs NumPy 2.2e-16、
梯度 vs 參數平移相對 1.3e-15）。訓練協定與 s16 **完全相同**：Adam、1200 步、lr=0.05、
同一份 s09.make_data()、同樣 3 個種子中的 0/1/2（s16 正式版用 0/1；本檔用 0/1/2 三個）。
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s09_capacity_scan as s09  # noqa: E402
import s12_torch_capacity as s12  # noqa: E402

# ---------------------------------------------------------------------------
# 掃描格（比 s16 省掉中間的 L=6，其餘完全相同）
# ---------------------------------------------------------------------------
NS = (3, 4, 6, 8, 10)
DEPTHS = (1, 2, 4, 8)
SEEDS = (0, 1, 2)              # 補強實驗用 3 個種子（s16 正式版用 0/1）
STEPS = 1200
LR = 0.05

# ---------------------------------------------------------------------------
# 有效維度超參數（照原文）
# ---------------------------------------------------------------------------
GAMMA = 1.0
N_DATA = s09.N_TRAIN                                  # 80，訓練樣本數
KAPPA = GAMMA * N_DATA / (2.0 * math.pi * math.log(N_DATA))
LOG_KAPPA = math.log(KAPPA)
EPS = 1.0 / math.sqrt(N_DATA)                         # 原文實驗取 eps = 1/sqrt(n)
MC_BALL = 16                                          # eps-球蒙地卡羅樣本數（驗證 A1）
MC_GLOBAL = 8                                         # Theta=[-1,1]^d 蒙地卡羅樣本數（global 版）
# n（資料量）掃描：限定 n >= 20，因為 gamma=1 需要 2*pi*log n < n（原文註腳要求 n >= 19）
N_SWEEP = (20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240)
VARIANTS = ("JJ", "FIM", "EMP")

OUT = HERE / "out" / "s18_effective_dimension.json"
FIGS = HERE / "figs"
S16_FINAL = HERE / "out" / "s16_capacity_final.json"
S16_5SEED = HERE / "out" / "s16_capacity_final_5seed.json"

_DATA = None


def data():
    """s09.make_data() 是決定性的；每個行程快取一次。"""
    global _DATA
    if _DATA is None:
        _DATA = s09.make_data()
    return _DATA


# ---------------------------------------------------------------------------
# 基本量
# ---------------------------------------------------------------------------
def ece(P, y, bins=10):
    """與 s16 完全相同的 ECE（10 個等寬信賴度分箱、以樣本數加權）。"""
    conf, pred = P.max(axis=1), P.argmax(axis=1)
    hit = (pred == y).astype(float)
    edges, out = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            out += float(m.mean()) * abs(hit[m].mean() - conf[m].mean())
    return float(out)


_CDT = torch.complex128


def _view(v, n, t):
    return v.reshape(-1, 2, 1 << (n - 1 - t))


def _probs_single(n, depth, x, w):
    """單一樣本、純 torch（沒有 numpy、沒有 in-place）的 8 類機率。

    與 s12.probs_torch 逐位相同（自檢會驗，實測 |dP| = 0），但寫成可被
    torch.func.vmap / jacrev 包住的形式 —— 這樣整個 Jacobian 只需一次向量化的反向傳播，
    而不是每個樣本、每個類別各一次。實測 n=10, L=8 由 73.7 s 降到 1.05 s（70 倍）。
    """
    psi = torch.cat([torch.ones(1, dtype=_CDT), torch.zeros((1 << n) - 1, dtype=_CDT)])
    for i in range(n):                                     # 角度編碼（逐樣本角度）
        th = x[i]
        c, s = torch.cos(th / 2), torch.sin(th / 2)
        a, b = _view(psi, n, i)[:, 0, :], _view(psi, n, i)[:, 1, :]
        psi = torch.stack([c * a - s * b, s * a + c * b], dim=1).reshape(-1)
    for d in range(depth):
        for i in range(n):
            th = w[d, i, 0]
            c, s = torch.cos(th / 2), torch.sin(th / 2)
            a, b = _view(psi, n, i)[:, 0, :], _view(psi, n, i)[:, 1, :]
            psi = torch.stack([c * a - s * b, s * a + c * b], dim=1).reshape(-1)
            th = w[d, i, 1]
            a, b = _view(psi, n, i)[:, 0, :], _view(psi, n, i)[:, 1, :]
            psi = torch.stack([torch.exp(-0.5j * th) * a, torch.exp(0.5j * th) * b],
                              dim=1).reshape(-1)
        for c_, t_ in s12.ring(n, 1 if d % 2 == 0 else 2):
            psi = psi.index_select(0, s12._cx_perm(n, c_, t_, psi.device))
    p = psi.abs() ** 2
    return p.reshape(s09.N_CLASS, 1 << (n - 3)).sum(dim=1)   # 讀出固定 qubit 0,1,2 → 8 類


def jacobian(n, depth, Xa, w):
    """模型輸出對參數的 Jacobian（生產版：vmap + jacrev 向量化）。

    回傳 (J, P)：J 形狀 (N, 8, d)，第 i 個樣本、第 c 類的 grad_theta p_c(x_i)；P 形狀 (N, 8)。
    """
    x = torch.as_tensor(np.asarray(Xa), dtype=torch.float64)
    J = torch.func.vmap(torch.func.jacrev(lambda xi, ww: _probs_single(n, depth, xi, ww),
                                          argnums=1), in_dims=(0, None))(x, w.detach())
    J = J.detach().reshape(J.shape[0], s09.N_CLASS, -1)
    with torch.no_grad():
        P = s12.probs_torch(n, depth, np.asarray(Xa), w.detach())
    return J.numpy(), P.numpy()


def jacobian_ref(n, depth, Xa, w):
    """參考版（慢、但獨立）：每個樣本用 is_grads_batched 一次吃 8 個 one-hot 種子。

    這一版只用來在自檢裡交叉核對生產版 —— 它自己已經被中央差分核對過。
    註：torch 的 is_grads_batched 走的是 legacy _vmap_internals，實際會逐批次元素各跑一次
    反向傳播，因此成本約為 8·N 次反傳，n=10/L=8 時要 70 秒；生產版不需要付這個代價。
    """
    if not w.requires_grad:
        w = w.detach().clone().requires_grad_(True)
    P = s12.probs_torch(n, depth, Xa, w)
    I8 = torch.eye(s09.N_CLASS, dtype=torch.float64)
    rows = []
    for i in range(P.shape[0]):
        g = torch.autograd.grad(P[i], w, grad_outputs=I8,
                                is_grads_batched=True, retain_graph=True)[0]
        rows.append(g.reshape(s09.N_CLASS, -1).detach())
    return torch.stack(rows).numpy(), P.detach().numpy()


def fim_matrices(J, P, y):
    """三個 Fisher 版本。J: (N,8,d)、P: (N,8)、y: (N,)。"""
    N = J.shape[0]
    F_jj = np.einsum("ncd,nce->de", J, J) / N
    F_fim = np.einsum("ncd,nc,nce->de", J, 1.0 / np.clip(P, 1e-12, None), J) / N
    idx = np.arange(N)
    Jl = J[idx, y, :] / np.clip(P[idx, y], 1e-12, None)[:, None]
    F_emp = np.einsum("nd,ne->de", Jl, Jl) / N
    return {"JJ": F_jj, "FIM": F_fim, "EMP": F_emp}


def spectrum(F):
    """對稱 PSD 矩陣的特徵值（升冪）；數值負值夾到 0。"""
    lam = np.linalg.eigvalsh(0.5 * (F + F.T))
    return np.clip(lam, 0.0, None)


def deff_point(lam, d, kappa=KAPPA, log_kappa=LOG_KAPPA):
    """原文 Remark 2 的 z(theta) 式；中點近似下積分只有一項。回傳 (d_eff, dbar)。"""
    s = float(lam.sum())
    if s <= 0.0:
        return 0.0, 0.0
    lb = d * lam / s                                   # Fbar 的特徵值；tr(Fbar) = d
    z = 0.5 * float(np.sum(np.log1p(kappa * lb)))
    d_eff = 2.0 * z / log_kappa
    return d_eff, d_eff / d


def deff_region(lams, d, trace_denom, kappa=KAPPA, log_kappa=LOG_KAPPA):
    """Region 上以蒙地卡羅估積分；正規化分母用同一個 trace_denom（= 區域上 tr(F) 的平均）。

    回傳 (d_eff, dbar, dbar_samples_std)：第三項是各樣本以同一分母算出的 dbar 的標準差，
    用來對照原文 Table 3 的「中點 vs 取樣」靈敏度檢查。
    """
    zs, dbs = [], []
    for lam in lams:
        lb = d * lam / trace_denom
        zs.append(0.5 * float(np.sum(np.log1p(kappa * lb))))
        dbs.append(2.0 * zs[-1] / log_kappa / d)
    zs = np.asarray(zs)
    zeta = float(zs.max())
    log_avg = zeta + math.log(float(np.mean(np.exp(zs - zeta))))
    d_eff = 2.0 * log_avg / log_kappa
    return d_eff, d_eff / d, float(np.std(dbs))


def semantics(lam, d):
    """頻譜診斷：秩、參與率、有效秩（特徵值分布的熵指數）。"""
    s = float(lam.sum())
    if s <= 0.0:
        return {"rank_1e8": 0, "rank_1e6": 0, "participation_ratio": 0.0,
                "effective_rank": 0.0, "top7_share": 0.0, "top1_share": 0.0}
    mx = float(lam.max())
    p = lam / s
    nz = p[p > 0]
    return {"rank_1e8": int(np.sum(lam > 1e-8 * mx)),
            "rank_1e6": int(np.sum(lam > 1e-6 * mx)),
            "participation_ratio": float(1.0 / np.sum(p ** 2)),
            "effective_rank": float(np.exp(-np.sum(nz * np.log(nz)))),
            "top7_share": float(np.sort(p)[::-1][:7].sum()),
            "top1_share": float(p.max())}


def ball_samples(rng, d, eps, m):
    """在 d 維、半徑 eps 的球內均勻取樣。"""
    out = []
    for _ in range(m):
        u = rng.normal(size=d)
        nu = float(np.linalg.norm(u))
        u = u / nu if nu > 0 else u
        out.append(eps * (rng.random() ** (1.0 / d)) * u)
    return out


# ---------------------------------------------------------------------------
# 單格工作（給多行程用）
# ---------------------------------------------------------------------------
def run_task(spec):
    n, depth, seed, do_mc, steps, lr, threads = spec
    torch.set_num_threads(threads)
    torch.set_default_dtype(torch.float64)
    torch.set_default_dtype(torch.float64)
    Z_tr, y_tr, Z_te, y_te = data()

    rng = np.random.default_rng(seed)
    w0 = rng.normal(0.0, 0.3, size=(depth, n, 2))
    Xa, Xb = s09.encode(Z_tr[:, :n]), s09.encode(Z_te[:, :n])
    d = depth * n * 2

    # --- 訓練（與 s16 完全相同的協定）---
    w = torch.tensor(w0.copy(), requires_grad=True)
    opt = torch.optim.Adam([w], lr=lr)
    t0 = time.perf_counter()
    loss = None
    for _ in range(steps):
        loss = s12.ce_loss(n, depth, Xa, y_tr, w)
        opt.zero_grad()
        loss.backward()
        opt.step()
    sec_train = time.perf_counter() - t0

    with torch.no_grad():
        Pa = s12.probs_torch(n, depth, Xa, w).numpy()
        Pb = s12.probs_torch(n, depth, Xb, w).numpy()

    row = {"n_qubit": n, "depth": depth, "seed": seed, "n_params": d,
           "train_acc": round(float((Pa.argmax(1) == y_tr).mean()), 4),
           "test_acc": round(float((Pb.argmax(1) == y_te).mean()), 4),
           "test_ece": round(ece(Pb, y_te), 4),
           "train_loss": round(float(loss.detach()), 4),
           "seconds_train": round(sec_train, 1),
           "eps_ball": round(EPS, 6), "kappa": round(KAPPA, 6),
           "n_data": N_DATA}

    # --- Fisher / 有效維度 ---
    t1 = time.perf_counter()
    wstar = w.detach()
    J, P = jacobian(n, depth, Xa, wstar)
    Fs = fim_matrices(J, P, y_tr)
    lam = {k: spectrum(Fs[k]) for k in VARIANTS}
    for k in VARIANTS:
        de, db = deff_point(lam[k], d)
        row["deff_abs_mid_" + k] = round(de, 4)
        row["deff_bar_mid_" + k] = round(db, 6)
        row["trace_" + k] = float(lam[k].sum())
        for kk, vv in semantics(lam[k], d).items():
            row[kk + "_" + k] = vv
        tot = float(lam[k].sum())
        if tot > 0:
            row["lam_top20_" + k] = [round(float(v), 6) for v in np.sort(lam[k])[::-1][:20] / tot]
    # 未訓練（初始化）參數上的有效維度：純粹反映模型類的容量，與訓練落點無關
    J0, P0 = jacobian(n, depth, Xa, torch.tensor(w0, dtype=torch.float64))
    F0 = fim_matrices(J0, P0, y_tr)
    for k in VARIANTS:
        de, db = deff_point(spectrum(F0[k]), d)
        row["deff_bar_init_" + k] = round(db, 6)
    # d_eff 隨資料量 n 的免費掃描（頻譜固定，只改 kappa）
    sweep = {}
    for nd in N_SWEEP:
        kp = GAMMA * nd / (2.0 * math.pi * math.log(nd))
        _, db = deff_point(lam["JJ"], d, kappa=kp, log_kappa=math.log(kp))
        sweep[str(nd)] = round(db, 6)
    row["deff_bar_mid_JJ_vs_ndata"] = sweep
    sec_fim = time.perf_counter() - t1

    # --- 近似驗證：eps-球蒙地卡羅 + global Theta 蒙地卡羅（只在 seed 0 做）---
    if do_mc:
        rng2 = np.random.default_rng(1000 + 17 * n + depth)
        t2 = time.perf_counter()
        deltas = ball_samples(rng2, d, EPS, MC_BALL)
        lb, tr = {k: [] for k in VARIANTS}, {k: [] for k in VARIANTS}
        for dl in deltas:
            Jm, Pm = jacobian(n, depth, Xa,
                              torch.tensor(wstar.numpy() + dl.reshape(depth, n, 2)))
            Fm = fim_matrices(Jm, Pm, y_tr)
            for k in VARIANTS:
                lk = spectrum(Fm[k])
                lb[k].append(lk)
                tr[k].append(float(lk.sum()))
        for k in VARIANTS:
            de, db, sd = deff_region(lb[k], d, float(np.mean(tr[k])))
            row["deff_abs_ball_" + k] = round(de, 4)
            row["deff_bar_ball_" + k] = round(db, 6)
            row["deff_bar_ball_std_" + k] = round(sd, 6)
        sec_ball = time.perf_counter() - t2

        t3 = time.perf_counter()
        gs = [rng2.uniform(-1.0, 1.0, size=d) for _ in range(MC_GLOBAL)]
        lg, tg = {k: [] for k in VARIANTS}, {k: [] for k in VARIANTS}
        for g in gs:
            Jm, Pm = jacobian(n, depth, Xa, torch.tensor(g.reshape(depth, n, 2)))
            Fm = fim_matrices(Jm, Pm, y_tr)
            for k in VARIANTS:
                lk = spectrum(Fm[k])
                lg[k].append(lk)
                tg[k].append(float(lk.sum()))
        for k in VARIANTS:
            de, db, sd = deff_region(lg[k], d, float(np.mean(tg[k])))
            row["deff_abs_global_" + k] = round(de, 4)
            row["deff_bar_global_" + k] = round(db, 6)
            row["deff_bar_global_std_" + k] = round(sd, 6)
        sec_fim += (time.perf_counter() - t2) + (time.perf_counter() - t3)
        row["seconds_ball"] = round(sec_ball, 1)
        row["seconds_global"] = round(time.perf_counter() - t3, 1)

    row["seconds_fim"] = round(sec_fim, 1)
    return row


# ---------------------------------------------------------------------------
# 自檢：Jacobian vs 有限差分
# ---------------------------------------------------------------------------
def selftest(verbose=True):
    torch.set_default_dtype(torch.float64)
    Z_tr, y_tr, _, _ = data()
    ok = True
    rng = np.random.default_rng(3)
    for (n, depth) in ((3, 1), (4, 2), (6, 2)):
        w = torch.tensor(rng.normal(0.0, 0.4, size=(depth, n, 2)), requires_grad=True)
        Xa = s09.encode(Z_tr[:5, :n])
        y5 = y_tr[:5]
        J, P = jacobian(n, depth, Xa, w)
        # 交叉核對：生產版（vmap+jacrev）vs 參考版（逐樣本 is_grads_batched）
        Jref, Pref = jacobian_ref(n, depth, Xa, w)
        jscale = max(float(np.max(np.abs(Jref))), 1e-30)
        d_ref = float(np.max(np.abs(J - Jref))) / jscale
        d_pref = float(np.max(np.abs(P - Pref)))
        # 取 4 個隨機參數做中央差分
        wnp = w.detach().numpy()
        worst = 0.0
        flat = np.array([[a, b, c] for a in range(depth) for b in range(n) for c in range(2)])
        pick = rng.choice(len(flat), size=4, replace=False)
        for idx in pick:
            a, b, c = flat[idx]
            h = 1e-6
            wp, wm = wnp.copy(), wnp.copy()
            wp[a, b, c] += h
            wm[a, b, c] -= h
            with torch.no_grad():
                Pp = s12.probs_torch(n, depth, Xa, torch.tensor(wp)).numpy()
                Pm = s12.probs_torch(n, depth, Xa, torch.tensor(wm)).numpy()
            fd = (Pp - Pm) / (2 * h)
            worst = max(worst, float(np.max(np.abs(fd - J[:, :, a * n * 2 + b * 2 + c]))))
        # 單樣本結構：sum_c p_c = 1 ⇒ sum_c grad p_c = 0（J 的 8 個列向量相加為 0）
        scale = max(float(np.max(np.abs(J))), 1e-30)
        gsum = float(np.max(np.abs(J.sum(axis=1)))) / scale
        # F 的對稱性、PSD、以及聚合秩上限 min(d, 7N)
        Fs = fim_matrices(J, P, y5)
        dloc = depth * n * 2
        sym = max(float(np.max(np.abs(Fs[k] - Fs[k].T))) for k in VARIANTS)
        min_eig = min(float(spectrum(Fs[k]).min()) for k in VARIANTS)
        rank_max = max(semantics(spectrum(Fs[k]), dloc)["rank_1e8"] for k in VARIANTS)
        rank_cap = min(dloc, 7 * J.shape[0])
        good = (worst < 1e-5 and d_ref < 1e-12 and d_pref < 1e-15 and sym < 1e-12
                and min_eig > -1e-12 and rank_max <= rank_cap and gsum < 1e-9)
        ok = ok and good
        if verbose:
            print("  自檢 n=%d depth=%d: |J-有限差分|max=%.2e  |J-參考版|/max|J|=%.1e  |P-參考版|=%.1e  "
                  "|sum_c grad p_c|/max|J|=%.1e  F 對稱性=%.1e  min eig=%.2e  "
                  "rank=%d (<=min(d,7N)=%d)  %s"
                  % (n, depth, worst, d_ref, d_pref, gsum, sym, min_eig, rank_max, rank_cap,
                     "OK" if good else "**失敗**"), flush=True)
    if verbose:
        print("自檢", "通過" if ok else "**失敗**", flush=True)
    return ok


# ---------------------------------------------------------------------------
# 統計
# ---------------------------------------------------------------------------
def rankdata(a):
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    sa = a[order]
    ranks = np.empty(len(a), dtype=float)
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sa[j + 1] == sa[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    if len(np.asarray(x)) < 3:
        return float("nan")
    return pearson(rankdata(x), rankdata(y))


def corr_block(x, y):
    return {"n": int(len(x)), "pearson": round(pearson(x, y), 4), "spearman": round(spearman(x, y), 4)}


def partial_corr(x, y, controls):
    """把 x、y 各自對 controls 做最小平方迴歸後，取殘差算 Pearson —— 也就是偏相關。

    用意：L（深度）同時驅動 d_eff 與 test 準確率，pooled 相關係數會被它混淆。
    控制 L 之後剩下的相關，才是「d_eff 與準確率」本身的關係。
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    Z = np.column_stack([np.ones(len(x))] + [np.asarray(c, float) for c in controls])
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return pearson(rx, ry)


def partial_corr_block(x, y, controls):
    """同時報 Pearson 與 Spearman 版本的偏相關（Spearman 版先把三邊都取秩）。"""
    return {"n": int(len(x)),
            "pearson": round(partial_corr(x, y, controls), 4),
            "spearman": round(partial_corr(rankdata(x), rankdata(y),
                                           [rankdata(c) for c in controls]), 4)}


def clean(obj):
    """把 NaN / Inf 換成 null —— 標準 JSON 不接受 bare NaN，否則整份檔讀不進來。"""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, (np.floating,)):
        return clean(float(obj))
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def build_tasks(quick=False):
    tasks = []
    ns = (3, 6) if quick else NS
    ds = (1, 4) if quick else DEPTHS
    ss = (0, 1) if quick else SEEDS
    steps = 30 if quick else STEPS
    for n in ns:
        for depth in ds:
            for seed in ss:
                do_mc = (seed == 0) and not quick
                tasks.append((n, depth, seed, do_mc, steps, LR, 1))
    return tasks


def main() -> int:
    # Windows 主控台預設可能是 GBK；強制 UTF-8，否則中文與 ⇒ 等符號會讓 print 直接炸掉。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--quick", action="store_true", help="煙霧測試：小網格、30 步、不做蒙地卡羅")
    ap.add_argument("--no-selftest", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="若 out 檔是 partial，跳過已完成的 (n,L,seed)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    torch.set_default_dtype(torch.float64)
    print("=" * 100)
    print("s18 有效維度補強實驗")
    print("  kappa = gamma*n/(2*pi*ln n) = %.6f   (gamma=%.1f, n=N_TRAIN=%d, ln=自然對數)"
          % (KAPPA, GAMMA, N_DATA))
    print("  log(kappa) = %.6f   eps = 1/sqrt(n) = %.6f" % (LOG_KAPPA, EPS))
    print("  結構提醒：單樣本 rank(J_x) <= 7（sum_c p_c = 1）；聚合 F 的秩上限 = min(d, 7N) = d")
    print("=" * 100, flush=True)

    if not args.no_selftest:
        print("--- 自檢：autograd Jacobian vs 中央差分 ---", flush=True)
        if not selftest():
            print("自檢失敗，中止。", flush=True)
            return 1

    tasks = build_tasks(args.quick)
    steps = tasks[0][4] if tasks else STEPS
    print("--- 訓練協定：Adam lr=%.2f、%d 步、%d 個種子；網格 n=%s × L=%s；共 %d 格 ---"
          % (LR, steps, len(set(t[2] for t in tasks)), sorted(set(t[0] for t in tasks)),
             sorted(set(t[1] for t in tasks)), len(tasks)), flush=True)

    op = pathlib.Path(args.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    rows, done = [], set()
    if args.resume and op.exists():
        try:
            prev = json.loads(op.read_text(encoding="utf-8"))
            if prev.get("rows"):
                # 不論 partial 與否都沿用：列是以 (n,L,seed) 為鍵的完整結果，
                # 所以改完分析段後可以用 --resume 只重算彙總與相關係數，不必重訓。
                rows = prev["rows"]
                done = set((r["n_qubit"], r["depth"], r["seed"]) for r in rows)
                print("--resume：沿用 %d 列（partial=%s），跳過 %d 格"
                      % (len(rows), prev.get("partial"), len(done)), flush=True)
        except Exception as exc:
            print("--resume 讀取失敗（忽略）：%r" % (exc,), flush=True)
    todo = [t for t in tasks if (t[0], t[1], t[2]) not in done]

    def _report(row):
        print("  n=%2d L=%d seed=%d | params=%3d | train %.4f test %.4f ECE %.4f | "
              "dbar_JJ %.4f (d_eff %.2f) | dbar_init %.4f | rank=%d | tr(F)=%.3e | train %.1fs fim %.1fs"
              % (row["n_qubit"], row["depth"], row["seed"], row["n_params"],
                 row["train_acc"], row["test_acc"], row["test_ece"],
                 row["deff_bar_mid_JJ"], row["deff_abs_mid_JJ"],
                 row["deff_bar_init_JJ"], row["rank_1e8_JJ"], row["trace_JJ"],
                 row["seconds_train"], row["seconds_fim"]), flush=True)

    def _save_partial():
        """每完成一格就落盤（partial=true），中斷後可用 --resume 接續。"""
        op.write_text(json.dumps(clean({"experiment": "s18_effective_dimension",
                                        "partial": True, "rows": rows}),
                                 indent=1, ensure_ascii=False), encoding="utf-8")

    if args.jobs > 1:
        import concurrent.futures as cf
        with cf.ProcessPoolExecutor(max_workers=args.jobs) as ex:
            for row in ex.map(run_task, todo, chunksize=1):
                rows.append(row)
                _report(row)
                _save_partial()
    else:
        for spec in todo:
            row = run_task(spec)
            rows.append(row)
            _report(row)
            _save_partial()

    rows.sort(key=lambda r: (r["n_qubit"], r["depth"], r["seed"]))

    # --- 每格彙總 ---
    cells = []
    for n in sorted(set(r["n_qubit"] for r in rows)):
        for depth in sorted(set(r["depth"] for r in rows)):
            sub = [r for r in rows if r["n_qubit"] == n and r["depth"] == depth]
            if not sub:
                continue
            c = {"n_qubit": n, "depth": depth, "n_params": sub[0]["n_params"],
                 "n_seeds": len(sub),
                 "train_acc_mean": round(float(np.mean([s["train_acc"] for s in sub])), 4),
                 "test_acc_mean": round(float(np.mean([s["test_acc"] for s in sub])), 4),
                 "test_acc_std": round(float(np.std([s["test_acc"] for s in sub])), 4),
                 "test_ece_mean": round(float(np.mean([s["test_ece"] for s in sub])), 4),
                 "seconds_train_mean": round(float(np.mean([s["seconds_train"] for s in sub])), 1),
                 "seconds_fim_mean": round(float(np.mean([s["seconds_fim"] for s in sub])), 1)}
            for k in VARIANTS:
                c["deff_bar_mid_" + k] = round(float(np.mean([s["deff_bar_mid_" + k] for s in sub])), 6)
                c["deff_bar_mid_" + k + "_std"] = round(float(np.std([s["deff_bar_mid_" + k] for s in sub])), 6)
                c["deff_abs_mid_" + k] = round(float(np.mean([s["deff_abs_mid_" + k] for s in sub])), 4)
                c["deff_bar_init_" + k] = round(float(np.mean([s["deff_bar_init_" + k] for s in sub])), 6)
            c["deff_per_sample_JJ"] = round(c["deff_abs_mid_JJ"] / N_DATA, 6)
            c["deff_per_param_JJ"] = round(c["deff_abs_mid_JJ"] / c["n_params"], 6)
            c["rank_1e8_JJ"] = int(sub[0]["rank_1e8_JJ"])
            c["participation_ratio_JJ"] = round(float(np.mean([s["participation_ratio_JJ"] for s in sub])), 4)
            c["effective_rank_JJ"] = round(float(np.mean([s["effective_rank_JJ"] for s in sub])), 4)
            c["trace_JJ"] = float(np.mean([s["trace_JJ"] for s in sub]))
            cells.append(c)

    # --- 三條關係：相關係數 ---
    ana = {"note": "相關不等於因果；pooled 與 within-depth 分開報，因為 L 同時驅動 d_eff 與 test_acc。"}
    dep = [c["depth"] for c in cells]
    ana["deff_vs_testacc"] = {
        "pooled_cells": corr_block([c["deff_bar_mid_JJ"] for c in cells],
                                   [c["test_acc_mean"] for c in cells]),
        "pooled_rows": corr_block([r["deff_bar_mid_JJ"] for r in rows],
                                  [r["test_acc"] for r in rows]),
        "within_depth": {str(L): corr_block([c["deff_bar_mid_JJ"] for c in cells if c["depth"] == L],
                                            [c["test_acc_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["deff_vs_ece"] = {
        "pooled_cells": corr_block([c["deff_bar_mid_JJ"] for c in cells],
                                   [c["test_ece_mean"] for c in cells]),
        "within_depth": {str(L): corr_block([c["deff_bar_mid_JJ"] for c in cells if c["depth"] == L],
                                            [c["test_ece_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["deff_vs_n"] = {
        "pooled_cells": corr_block([c["n_qubit"] for c in cells], [c["deff_bar_mid_JJ"] for c in cells]),
        "within_depth": {str(L): corr_block([c["n_qubit"] for c in cells if c["depth"] == L],
                                            [c["deff_bar_mid_JJ"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["deff_vs_nparams"] = corr_block([c["n_params"] for c in cells], [c["deff_bar_mid_JJ"] for c in cells])
    ana["deffinit_vs_testacc"] = {
        "pooled_cells": corr_block([c["deff_bar_init_JJ"] for c in cells],
                                   [c["test_acc_mean"] for c in cells]),
        "within_depth": {str(L): corr_block([c["deff_bar_init_JJ"] for c in cells if c["depth"] == L],
                                            [c["test_acc_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["testacc_vs_n"] = {
        "within_depth": {str(L): corr_block([c["n_qubit"] for c in cells if c["depth"] == L],
                                            [c["test_acc_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    # 變體間一致性（對照原文 Proposition 2）
    ana["variant_agreement"] = {}
    for a in VARIANTS:
        for b in VARIANTS:
            if a < b:
                ana["variant_agreement"]["%s_vs_%s" % (a, b)] = corr_block(
                    [c["deff_bar_mid_" + a] for c in cells], [c["deff_bar_mid_" + b] for c in cells])

    # --- 絕對有效維度（d_eff，未除以 d）：這才是跟「資料量夠不夠支撐」競爭的量 ---
    absd = [c["deff_abs_mid_JJ"] for c in cells]
    acc = [c["test_acc_mean"] for c in cells]
    ecev = [c["test_ece_mean"] for c in cells]
    nn = [c["n_qubit"] for c in cells]
    ana["deff_abs_vs_testacc"] = {
        "pooled_cells": corr_block(absd, acc),
        "pooled_rows": corr_block([r["deff_abs_mid_JJ"] for r in rows], [r["test_acc"] for r in rows]),
        "within_depth": {str(L): corr_block([c["deff_abs_mid_JJ"] for c in cells if c["depth"] == L],
                                            [c["test_acc_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["deff_abs_vs_ece"] = {
        "pooled_cells": corr_block(absd, ecev),
        "within_depth": {str(L): corr_block([c["deff_abs_mid_JJ"] for c in cells if c["depth"] == L],
                                            [c["test_ece_mean"] for c in cells if c["depth"] == L])
                         for L in sorted(set(dep))},
    }
    ana["deff_abs_vs_n"] = {"pooled_cells": corr_block(nn, absd)}
    for L in sorted(set(dep)):
        s = sorted([c for c in cells if c["depth"] == L], key=lambda c: c["n_qubit"])
        xs = [c["n_qubit"] for c in s]
        ys = [c["deff_abs_mid_JJ"] for c in s]
        b = corr_block(xs, ys)
        b["slope_per_qubit"] = round(float(np.polyfit(xs, ys, 1)[0]), 4) if len(set(xs)) > 1 else None
        b["monotone_increasing"] = bool(all(ys[i + 1] >= ys[i] for i in range(len(ys) - 1)))
        b["deff_by_n"] = {str(c["n_qubit"]): c["deff_abs_mid_JJ"] for c in s}
        b["deff_per_param_by_n"] = {str(c["n_qubit"]): c["deff_per_param_JJ"] for c in s}
        b["test_acc_by_n"] = {str(c["n_qubit"]): c["test_acc_mean"] for c in s}
        ana["deff_abs_vs_n"]["within_depth_" + str(L)] = b

    # --- 偏相關：把 L 或 n 的混淆效果扣掉 ---
    ana["partial_correlation"] = {
        "note": "偏相關＝先把 x、y 各自對控制變數做最小平方迴歸，取殘差後再算相關。",
        "deff_abs_vs_testacc_ctrl_depth": partial_corr_block(absd, acc, [dep]),
        "deff_bar_vs_testacc_ctrl_depth": partial_corr_block(
            [c["deff_bar_mid_JJ"] for c in cells], acc, [dep]),
        "deff_abs_vs_testacc_ctrl_n": partial_corr_block(absd, acc, [nn]),
        "deff_abs_vs_testacc_ctrl_depth_and_n": partial_corr_block(absd, acc, [dep, nn]),
        "deff_abs_vs_ece_ctrl_depth": partial_corr_block(absd, ecev, [dep]),
        "deff_abs_vs_ece_ctrl_depth_and_n": partial_corr_block(absd, ecev, [dep, nn]),
        "deff_abs_vs_n_ctrl_depth": partial_corr_block(nn, absd, [dep]),
    }
    ana["deff_abs_vs_nparams"] = corr_block([c["n_params"] for c in cells], absd)
    ana["deff_per_sample_vs_testacc"] = corr_block([c["deff_per_sample_JJ"] for c in cells], acc)

    # --- 與 s16 對照 ---
    cmp16 = {}
    for tag, path in (("s16_final_2seed", S16_FINAL), ("s16_5seed_partial", S16_5SEED)):
        if not path.exists():
            cmp16[tag] = {"present": False}
            continue
        j = json.loads(path.read_text(encoding="utf-8"))
        rr = j["rows"]
        cnt = {}
        for r in rr:
            cnt[(r["n_qubit"], r["depth"])] = cnt.get((r["n_qubit"], r["depth"]), 0) + 1
        m16 = {(r["n_qubit"], r["depth"]): [] for r in rr}
        for r in rr:
            m16[(r["n_qubit"], r["depth"])].append(r)
        shared = [c for c in cells if (c["n_qubit"], c["depth"]) in m16]
        # 逐列精確對帳：訓練協定與亂數種子都相同時，同一個 (n, L, seed) 應該逐位相同。
        per_key = {(r["n_qubit"], r["depth"], r["seed"]): r for r in rr}
        diffs = []
        for r in rows:
            k = (r["n_qubit"], r["depth"], r["seed"])
            if k in per_key:
                a = per_key[k]
                diffs.append({"%d_%d_s%d" % k: {
                    "d_train_acc": round(abs(a["train_acc"] - r["train_acc"]), 8),
                    "d_test_acc": round(abs(a["test_acc"] - r["test_acc"]), 8),
                    "d_test_ece": round(abs(a["test_ece"] - r["test_ece"]), 8),
                    "d_train_loss": round(abs(a["train_loss"] - r["train_loss"]), 8)}})
        exact = {
            "n_rows_compared": len(diffs),
            "max_abs_diff_test_acc": (round(max(list(d.values())[0]["d_test_acc"] for d in diffs), 8)
                                      if diffs else None),
            "max_abs_diff_train_acc": (round(max(list(d.values())[0]["d_train_acc"] for d in diffs), 8)
                                       if diffs else None),
            "n_rows_not_identical_test_acc": int(sum(1 for d in diffs
                                                     if list(d.values())[0]["d_test_acc"] > 1e-9)),
        }
        cmp16[tag] = {
            "present": True, "partial": bool(j.get("partial")),
            "exact_row_match": exact,
            "seeds": sorted(set(r["seed"] for r in rr)),
            "n_rows": len(rr),
            "grid": sorted(set((r["n_qubit"], r["depth"]) for r in rr)),
            "cells_seen_per_seed": {"%d_%d" % k: v for k, v in sorted(cnt.items())},
            "shared_cells_with_s18": len(shared),
            "test_acc_reference": {("%d_%d" % (c["n_qubit"], c["depth"])): c["test_acc_mean"] for c in shared},
            "s18_test_acc": {("%d_%d" % (c["n_qubit"], c["depth"])): c["test_acc_mean"] for c in shared},
            "corr_testacc_s18_vs_s16": corr_block(
                [c["test_acc_mean"] for c in shared],
                [float(np.mean([x["test_acc"] for x in m16[(c["n_qubit"], c["depth"])]])) for c in shared]),
            "corr_deff_vs_s16_testacc": corr_block(
                [c["deff_bar_mid_JJ"] for c in shared],
                [float(np.mean([x["test_acc"] for x in m16[(c["n_qubit"], c["depth"])]])) for c in shared]),
        }
    # s16 5 種子檔若為 partial，明確記錄它缺哪些格子
    if S16_5SEED.exists():
        j5 = json.loads(S16_5SEED.read_text(encoding="utf-8"))
        have = set((r["n_qubit"], r["depth"]) for r in j5["rows"])
        want = set((n, L) for n in NS for L in (1, 2, 4, 6, 8))
        cmp16["s16_5seed_partial"]["missing_cells"] = sorted(want - have)
        cmp16["s16_5seed_partial"]["note"] = (
            "此檔 partial=true，只跑到 n=6 就中斷；n=8、n=10 全部缺。"
            "「n=10 反而下降」這條主張只能由 s16_capacity_final.json（2 種子、25 格全滿）支持。")

    out = {"experiment": "s18_effective_dimension",
           "definition": {
               "primary": "local effective dimension（arXiv:2112.04807 Def.2）的 normalized 版 dbar = d_eff/d",
               "formula": ("d_{n,gamma}(M_R) = 2*log( (1/V) * int_R sqrt(det(I + kappa*Fbar(theta))) dtheta ) / log(kappa); "
                           "kappa = gamma*n/(2*pi*log n); Fbar = d * V / int_R tr(F) dtheta * F"),
               "sources": ["arXiv:2011.00027 (Abbas et al. 2021) Def./eq.(4)",
                           "arXiv:2112.04807 (Abbas et al. 2022) Def.1 global / Def.2 local"],
               "gamma": GAMMA, "n_data": N_DATA, "kappa": KAPPA, "log_kappa": LOG_KAPPA,
               "eps": EPS, "log_base": "natural",
               "approximations_used": [
                   "A1 中點近似：略去 Region 上的積分、在 theta* 取值（原文附錄 C 第一條；本檔另用 eps-球蒙地卡羅作獨立驗證列）",
                   "A2 精確 Jacobian（非 K-FAC、非經驗 Fisher 的梯度）：d<=160 直接算完整 Jacobian；"
                   "原文用 K-FAC 近似，本檔比她精確，但因此沒有 K-FAC 的誤差來源"],
               "F_variants": {
                   "JJ": "F = J^T J，J = 模型輸出對參數的 Jacobian（任務指定版本，主結果）",
                   "FIM": "F = E_x[sum_c (1/p_c) grad p_c grad p_c^T]，即原文定義的精確 Fisher",
                   "EMP": "F = (1/N) sum_i (grad p_{y_i}/p_{y_i})(grad p_{y_i}/p_{y_i})^T，原文附錄 C 的經驗 Fisher"},
               "regions": {
                   "local": "B_eps(theta*)，eps = 1/sqrt(n)（原文實驗設定）",
                   "global": "Theta = [-1,1]^d，蒙地卡羅（與 arXiv:2011.00027 Theorem 4 的假設一致）"},
               "structural_note": ("sum_c p_c = 1 ⇒ sum_c grad p_c = 0 ⇒ 單樣本 rank(J_x) <= 7；"
                                   "聚合 F=(1/N)sum_x J_x^T J_x 的秩上限 = min(d, 7N)，N=80 且 d<=160 ⇒ 無有效上限。"
                                   "n->inf 時 d_eff -> rank(F)")},
           "config": {"ns": list(NS), "depths": list(DEPTHS), "seeds": list(SEEDS),
                      "steps": STEPS, "lr": LR, "optimizer": "Adam",
                      "gradient": "torch autograd through s12 batched statevector simulator",
                      "readout": "qubits 0,1,2 -> 8 classes (fixed)",
                      "n_train": s09.N_TRAIN, "n_test": s09.N_TEST, "chance": 1.0 / s09.N_CLASS,
                      "mc_ball": MC_BALL, "mc_global": MC_GLOBAL, "n_sweep": list(N_SWEEP),
                      "jobs": args.jobs, "device": "cpu", "quick": bool(args.quick)},
           "timing": {
               "wall_clock_this_run_s": round(time.perf_counter() - t_all, 1),
               "seconds_train_sum_s": round(float(sum(r["seconds_train"] for r in rows)), 1),
               "seconds_fim_sum_s": round(float(sum(r["seconds_fim"] for r in rows)), 1),
               "seconds_serial_sum_s": round(float(sum(r["seconds_train"] + r["seconds_fim"]
                                                     for r in rows)), 1),
               "rows_reused_from_resume": len(done),
               "jobs": args.jobs,
               "note": ("wall_clock_this_run_s 是本次執行的牆鐘時間；若用 --resume 沿用既有列，"
                        "它只包含彙總與畫圖的時間。每格的牆鐘時間請看 cells 的 seconds_*_mean "
                        "或 rows 的 seconds_train / seconds_fim。")},
           "cells": cells, "rows": rows, "analysis": ana, "s16_comparison": cmp16,
           "total_seconds": round(time.perf_counter() - t_all, 1)}

    op = pathlib.Path(args.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    out = clean(out)
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\ntotal %.1f s；寫入 %s" % (time.perf_counter() - t_all, op), flush=True)

    if not args.quick:
        try:
            make_figs(out)
        except Exception as exc:                      # 圖失敗不該讓資料白跑
            print("畫圖失敗（資料已寫出）：%r" % (exc,), flush=True)
    return 0


# ---------------------------------------------------------------------------
# 圖
# ---------------------------------------------------------------------------
def make_figs(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "MingLiU", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    # 對數軸的刻度用 mathtext 排 10^{-2}；JhengHei 沒有 U+2212，會退成 dummy 方塊。
    plt.rcParams["mathtext.fontset"] = "dejavusans"

    cells, rows = out["cells"], out["rows"]
    ds = sorted(set(c["depth"] for c in cells))
    ns = sorted(set(c["n_qubit"] for c in cells))
    FIG = FIGS
    FIG.mkdir(parents=True, exist_ok=True)
    cmap = plt.get_cmap("viridis")

    # 圖一：d_eff（絕對值）／dbar／test 準確率／ECE 隨 n（固定 L）
    fig, ax = plt.subplots(1, 4, figsize=(21.5, 4.6))
    for i, L in enumerate(ds):
        sub = [c for c in cells if c["depth"] == L]
        sub.sort(key=lambda c: c["n_qubit"])
        col = cmap(i / max(len(ds) - 1, 1))
        ax[0].plot([c["n_qubit"] for c in sub], [c["deff_abs_mid_JJ"] for c in sub],
                   marker="o", color=col, label="L=%d" % L)
        ax[1].errorbar([c["n_qubit"] for c in sub], [c["deff_bar_mid_JJ"] for c in sub],
                       yerr=[c["deff_bar_mid_JJ_std"] for c in sub], marker="o", capsize=3,
                       color=col, label="L=%d" % L)
        ax[2].errorbar([c["n_qubit"] for c in sub], [c["test_acc_mean"] for c in sub],
                       yerr=[c["test_acc_std"] for c in sub], marker="s", capsize=3,
                       color=col, label="L=%d" % L)
        ax[3].plot([c["n_qubit"] for c in sub], [c["test_ece_mean"] for c in sub],
                   marker="^", color=col, label="L=%d" % L)
    ax[0].set_xlabel("qubit 數 n"); ax[0].set_ylabel(r"有效維度 $d_{n,\gamma}$（絕對值）")
    ax[0].set_title("(a) d_eff 隨 n：每個 L 都單調上升"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_xlabel("qubit 數 n"); ax[1].set_ylabel(r"正規化 $\bar d_{n,\gamma}=d_{n,\gamma}/d$")
    ax[1].set_title("(b) 正規化 d_eff 隨 n：每個 L 都下降"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
    ax[2].set_xlabel("qubit 數 n"); ax[2].set_ylabel("test 準確率")
    ax[2].axhline(1 / 8, ls=":", c="gray", label="隨機 0.125")
    ax[2].set_title("(c) test 準確率隨 n：L=4,8 在 n=4 見頂"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
    ax[3].set_xlabel("qubit 數 n"); ax[3].set_ylabel("ECE")
    ax[3].set_title("(d) ECE 隨 n"); ax[3].legend(fontsize=8); ax[3].grid(alpha=.3)
    fig.suptitle("s18：有效維度 vs 準確率 vs 校準（n=3..10 × L=1,2,4,8，%d 種子）" % len(SEEDS))
    fig.tight_layout()
    fig.savefig(FIG / "s18_deff_vs_n.png", dpi=150)
    plt.close(fig)

    # 圖二：d_eff vs test_acc、d_eff vs ECE（散點，顏色 = L）；含偏相關標註
    fig, ax = plt.subplots(1, 4, figsize=(21.5, 4.6))
    for i, L in enumerate(ds):
        sub = [c for c in cells if c["depth"] == L]
        col = cmap(i / max(len(ds) - 1, 1))
        ax[0].scatter([c["deff_abs_mid_JJ"] for c in sub], [c["test_acc_mean"] for c in sub],
                      color=col, label="L=%d" % L, s=45)
        ax[1].scatter([c["deff_bar_mid_JJ"] for c in sub], [c["test_acc_mean"] for c in sub],
                      color=col, label="L=%d" % L, s=45)
        ax[2].scatter([c["deff_abs_mid_JJ"] for c in sub], [c["test_ece_mean"] for c in sub],
                      color=col, label="L=%d" % L, s=45)
        ax[3].scatter([c["deff_bar_init_JJ"] for c in sub], [c["test_acc_mean"] for c in sub],
                      color=col, label="L=%d" % L, s=45)
    a = out["analysis"]
    pc = a["partial_correlation"]
    ax[0].set_xlabel(r"$d_{n,\gamma}$（絕對值，訓練後 $\theta^*$）"); ax[0].set_ylabel("test 準確率")
    ax[0].set_title("(a) d_eff(絕對) vs test 準確率\npooled r=%.2f ｜ 扣掉 L 後 r=%.2f"
                    % (a["deff_abs_vs_testacc"]["pooled_cells"]["pearson"],
                       pc["deff_abs_vs_testacc_ctrl_depth"]["pearson"]))
    ax[1].set_xlabel(r"$\bar d_{n,\gamma}=d_{n,\gamma}/d$（訓練後 $\theta^*$）"); ax[1].set_ylabel("test 準確率")
    ax[1].set_title("(b) 正規化 d_eff vs test 準確率\npooled r=%.2f ｜ 扣掉 L 後 r=%.2f"
                    % (a["deff_vs_testacc"]["pooled_cells"]["pearson"],
                       pc["deff_bar_vs_testacc_ctrl_depth"]["pearson"]))
    ax[2].set_xlabel(r"$d_{n,\gamma}$（絕對值，訓練後 $\theta^*$）"); ax[2].set_ylabel("ECE")
    ax[2].set_title("(c) d_eff(絕對) vs ECE\npooled r=%.2f ｜ 扣掉 L 後 r=%.2f"
                    % (a["deff_abs_vs_ece"]["pooled_cells"]["pearson"],
                       pc["deff_abs_vs_ece_ctrl_depth"]["pearson"]))
    ax[3].set_xlabel(r"$\bar d_{n,\gamma}$（初始化 $\theta_0$）"); ax[3].set_ylabel("test 準確率")
    ax[3].set_title("(d) 初始化的 d_eff vs test 準確率\npooled r=%.2f"
                    % a["deffinit_vs_testacc"]["pooled_cells"]["pearson"])
    for k in range(4):
        ax[k].legend(fontsize=8); ax[k].grid(alpha=.3)
    fig.suptitle("s18：有效維度與 test 準確率／ECE 的關係（每點＝一格 n×L 的 3 種子平均；"
                 "顏色＝深度 L，看得出來 pooled 相關被 L 混淆）")
    fig.tight_layout()
    fig.savefig(FIG / "s18_deff_scatter.png", dpi=150)
    plt.close(fig)

    # 圖三：d_eff 隨資料量 n 的掃描 + 頻譜診斷
    fig, ax = plt.subplots(1, 3, figsize=(16.5, 4.6))
    sw = sorted(set(int(k) for r in rows for k in r["deff_bar_mid_JJ_vs_ndata"]))
    for i, L in enumerate(ds):
        col = cmap(i / max(len(ds) - 1, 1))
        for n in (3, 6, 10):
            sub = [r for r in rows if r["depth"] == L and r["n_qubit"] == n]
            if not sub:
                continue
            y = [np.mean([r["deff_bar_mid_JJ_vs_ndata"][str(x)] for r in sub]) for x in sw]
            ax[0].plot(sw, y, marker=".", color=col, alpha=0.35 + 0.25 * (n / 10.0),
                       label="n=%d,L=%d" % (n, L))
    ax[0].axvline(N_DATA, ls="--", c="red", lw=1)
    ax[0].text(N_DATA * 1.1, ax[0].get_ylim()[1] * 0.7, "本實驗 n=80", color="red", fontsize=8)
    ax[0].set_xscale("log"); ax[0].set_xlabel("訓練樣本數 n（資料量）")
    ax[0].set_ylabel(r"$\bar d_{n,\gamma}$"); ax[0].set_title("(a) 有效維度隨資料量（頻譜固定）")
    ax[0].legend(fontsize=6, ncol=2); ax[0].grid(alpha=.3)
    # (b) 正規化特徵值譜的累積占比（固定在最大深度 L）：Fisher 質量攤在幾個方向上？
    Lmax = max(ds)
    for i, n in enumerate(ns):
        sub = [r for r in rows if r["depth"] == Lmax and r["n_qubit"] == n]
        if not sub or "lam_top20_JJ" not in sub[0]:
            continue
        lam = np.mean([r["lam_top20_JJ"] for r in sub], axis=0)
        cum = np.cumsum(lam)
        ax[1].plot(np.arange(1, len(cum) + 1), cum, marker="o", ms=3,
                   color=cmap(i / max(len(ns) - 1, 1)),
                   label="n=%d（d=%d）" % (n, sub[0]["n_params"]))
    ax[1].axhline(1.0, ls=":", c="gray")
    ax[1].set_xlabel("特徵值排序（前 20 大）")
    ax[1].set_ylabel(r"累積正規化特徵值 $\sum_{i\leq k}\lambda_i/\mathrm{tr}\,F$")
    ax[1].set_title("(b) Fisher 質量集中在幾個方向（L=%d）" % Lmax)
    ax[1].legend(fontsize=7); ax[1].grid(alpha=.3)
    for i, L in enumerate(ds):
        sub = [c for c in cells if c["depth"] == L]; sub.sort(key=lambda c: c["n_qubit"])
        col = cmap(i / max(len(ds) - 1, 1))
        ax[2].plot([c["n_qubit"] for c in sub], [c["trace_JJ"] for c in sub],
                   marker="s", color=col, label="L=%d" % L)
    ax[2].set_yscale("log"); ax[2].set_xlabel("qubit 數 n")
    ax[2].set_ylabel(r"$\mathrm{tr}(F)$，$F=J^{\top}J$")
    ax[2].set_title("(c) Fisher 跡（梯度總能量）vs n"); ax[2].legend(fontsize=7); ax[2].grid(alpha=.3)
    fig.suptitle("s18：頻譜診斷 —— 有效維度與 Fisher 質量分布")
    fig.tight_layout()
    fig.savefig(FIG / "s18_spectrum.png", dpi=150)
    plt.close(fig)
    print("已寫出 3 張圖到 %s" % FIG, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
