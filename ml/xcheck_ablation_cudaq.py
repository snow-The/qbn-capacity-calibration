"""跨軌對帳（§5.2 消融）：去相位消融的電路在 CUDA-Q 上等價。

為什麼要做這件事：
  `AGENTS.md` 規定「論文要報的數字一律由正式軌（CUDA-Q）產生」，而 §5.2 的消融實驗
  （s17）是用我們自己的密度矩陣模擬器跑的。§5.1 的容量掃描已經有跨軌對帳
  （xcheck_跨軌對帳.md：同一顆 250 閘電路，torch vs CUDA-Q = 3.469e-18），
  但 §5.2 走的是**完全不同的代碼路徑**（密度矩陣 + 去相位通道 + adjoint 梯度），
  那份對帳完全沒有覆蓋到它。本檔補上這個缺口。

方法（為什麼不用 CUDA-Q 的 NoiseModel）：
  完全去相位在計算基底上的定義是 D_S(rho) = sum_b P_b rho P_b，
  也就是「以機率 p_b 把態換成 |b><b|」——**它本身就是一個經典混合**。
  所以不必把通道塞進 CUDA-Q 的雜訊模型，可以直接按定義精確實現：
    1. 用 CUDA-Q 狀態向量算出編碼層之後每個基底態的精確機率 p_b；
    2. 對每個 p_b > 0 的 b，用 CUDA-Q 從 |b> 出發跑完其餘電路；
    3. 以 p_b 加權平均。
  全程的量子演化都由 CUDA-Q 執行，通道按數學定義精確展開，沒有任何近似。

★ 位序陷阱（本檔第一次跑就踩到，值 4.957e-02）：
  p_basis 來自 CUDA-Q 的平坦索引（qubit k <-> bit k，little-endian），
  所以把 b 還原成基態時必須用**同一個**約定；若改用 s17 的 big-endian 解讀，
  等於在錯的基底上做混合。輸出端的類別映射則相反，需要位元反轉才能與 s17 對齊。
  同一個位序問題在本專案已經出現過多次（見 hardware/README.md §7.4）。

被檢驗的是 s17 的 DensitySim：
  臂 A（無通道）、臂 B（編碼層後去相位）。
  臂 C（尾端去相位）是代數恆等式——計算基底測量只讀對角元，去相位不改對角元，
  s17 自己已驗到精確 0.000e+00，本檔一併重印該值作為對照。
  臂 D（去極化）與 adjoint 梯度路徑**尚未**由正式軌背書，見報告的殘留缺口一節。
"""
import warnings
warnings.filterwarnings("ignore")

import pathlib
import sys

import numpy as np
import cudaq

ML = pathlib.Path("/mnt/c/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration/ml")
sys.path.insert(0, str(ML))
import s17_dephasing_ablation as s17  # noqa: E402  被檢驗的實作

N = s17.N_QUBIT          # 5
DEPTH = s17.DEPTH        # 2
NCLS = s17.N_CLASS       # 8
TOL = 1e-10

cudaq.set_target("qpp-cpu")


@cudaq.kernel
def enc_only(ang: list[float], n: int):
    """編碼層。參數不可命名為 x——會遮蔽 X 閘。"""
    q = cudaq.qvector(n)
    for i in range(n):
        ry(ang[i], q[i])


@cudaq.kernel
def full_a(ang: list[float], w: list[float], n: int, depth: int):
    """臂 A：編碼層 + 變分層，一顆電路跑完。"""
    q = cudaq.qvector(n)
    for i in range(n):
        ry(ang[i], q[i])
    for d in range(depth):
        for i in range(n):
            ry(w[(d * n + i) * 2 + 0], q[i])
            rz(w[(d * n + i) * 2 + 1], q[i])
        for i in range(n):
            # 環形 CX 步長逐層交替 1, 2；CUDA-Q 核心不支援三元運算式。
            t = (i + 1 + d % 2) % n
            cx(q[i], q[t])


@cudaq.kernel
def var_from_basis(bits: list[int], w: list[float], n: int, depth: int):
    """從 |bits> 出發，跑完變分層。"""
    q = cudaq.qvector(n)
    for i in range(n):
        if bits[i] == 1:
            x(q[i])
    for d in range(depth):
        for i in range(n):
            ry(w[(d * n + i) * 2 + 0], q[i])
            rz(w[(d * n + i) * 2 + 1], q[i])
        for i in range(n):
            t = (i + 1 + d % 2) % n
            cx(q[i], q[t])


def cls_from_probs(p_flat: np.ndarray, flip: bool) -> np.ndarray:
    """把 2^n 的平坦機率向量收成 8 類。

    s17 是 big-endian（qubit 0 = 最高位），類別 = 平坦索引的前 3 位；
    CUDA-Q 的位序相反，故 flip=True 時先做位元反轉。
    """
    p = np.asarray(p_flat, dtype=float).copy()
    if flip:
        idx = np.arange(1 << N)
        rev = np.zeros_like(idx)
        for k in range(N):
            rev |= ((idx >> k) & 1) << (N - 1 - k)
        p = p[rev]
    return p.reshape(NCLS, 1 << (N - 3)).sum(axis=1)


def main() -> int:
    print("CUDA-Q", cudaq.__version__, "| target =", cudaq.get_target().name)
    print("被檢驗：s17.DensitySim（%d qubit, depth %d）" % (N, DEPTH))
    print()

    rng = np.random.default_rng(20260920)
    X = rng.normal(0.0, 0.7, size=(1, N))
    W = rng.normal(0.0, 0.5, size=(1, DEPTH, N, 2))
    ang = [float(v) for v in X[0]]
    w_flat = [float(v) for v in W.reshape(-1)]

    # ---------- 被檢驗方：s17 的密度矩陣模擬器 ----------
    P_A_ref = s17.class_probs(X, W, "none", None, 0.0)[0]
    P_B_ref = s17.class_probs(X, W, "dephase", 0, 0.0)[0]
    P_C_ref = s17.class_probs(X, W, "dephase", DEPTH, 0.0)[0]
    print("s17 臂 C - 臂 A：max|dP| = %.3e（代數恆等式，應為精確 0）"
          % float(np.max(np.abs(P_C_ref - P_A_ref))))
    print("s17 臂 B - 臂 A：max|dP| = %.3e（通道確實改變預測）"
          % float(np.max(np.abs(P_B_ref - P_A_ref))))

    # ---------- 檢驗方：CUDA-Q ----------
    psi = np.array(cudaq.get_state(enc_only, ang, N))
    p_basis = np.abs(psi) ** 2
    print()
    print("CUDA-Q 編碼層：sum|amp|^2 = %.15f，非零基底態 %d/%d"
          % (float(p_basis.sum()), int((p_basis > 1e-14).sum()), 1 << N))

    stA = np.array(cudaq.get_state(full_a, ang, w_flat, N, DEPTH))
    P_A_cq = np.abs(stA) ** 2

    # 臂 B：以 p_b 混合「從 |b> 跑完其餘電路」的結果（＝ D_S 的精確定義）
    P_B_cq = np.zeros(1 << N)
    for b in np.nonzero(p_basis > 1e-14)[0]:
        # ★ 必須用 CUDA-Q 的約定解讀 b（qubit k <-> bit k）
        bits = [int((b >> k) & 1) for k in range(N)]
        st = np.array(cudaq.get_state(var_from_basis, bits, w_flat, N, DEPTH))
        P_B_cq += float(p_basis[b]) * (np.abs(st) ** 2)

    print()
    print("=== 位序判定 ===")
    for flip in (True, False):
        da = float(np.max(np.abs(cls_from_probs(P_A_cq, flip) - P_A_ref)))
        db = float(np.max(np.abs(cls_from_probs(P_B_cq, flip) - P_B_ref)))
        print("  %-10s 臂 A max|dP| = %.3e  |  臂 B max|dP| = %.3e"
              % ("位元反轉" if flip else "直接比較", da, db))

    P_A_fin = cls_from_probs(P_A_cq, True)
    P_B_fin = cls_from_probs(P_B_cq, True)
    da = float(np.max(np.abs(P_A_fin - P_A_ref)))
    db = float(np.max(np.abs(P_B_fin - P_B_ref)))
    print()
    print("  臂 A  s17    :", np.array2string(P_A_ref, precision=6))
    print("  臂 A  CUDA-Q :", np.array2string(P_A_fin, precision=6))
    print("  臂 B  s17    :", np.array2string(P_B_ref, precision=6))
    print("  臂 B  CUDA-Q :", np.array2string(P_B_fin, precision=6))
    print()
    ok = da < TOL and db < TOL
    print("判定（門檻 %.0e）：%s" % (TOL, "通過——§5.2 的消融電路在正式軌上等價" if ok else "**未通過**"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
