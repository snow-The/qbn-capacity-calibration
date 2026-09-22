"""C1 量子層：統一的閘序列表示 ＋ 純 NumPy 參考實作。

為什麼要有「統一的閘序列」這個中間層：
  C1 要問的是「同一條電路換框架會不會變」。若每個框架各自解讀參數，
  差異就分不清是「框架不同」還是「我們實作不同」。所以先產生一份**明確的閘列表**，
  三個框架執行的都是同一份列表 —— 這樣差異只可能來自框架本身。

電路（依原文 L178/L261 能確定的部分）：
  |0>^4 → RY(x_i) 編碼 → depth 2 的 [Rot(θ) 逐 qubit ＋ ring CX] → 量 ⟨Z_i⟩

原文**沒有寫**的（見 協定-C1.md §一）：
  * Rot(θ) 的歐拉角順序 → 由參數決定，外部掃描
  * 角度縮放式子       → 由參數決定，外部掃描
  * 糾纏閘的參數化     → 本檔用 ring CX（原文只說「controlled two-qubit gates」）
"""
from __future__ import annotations

import numpy as np

N_QUBIT = 4
DEPTH = 2
RING = [(i, (i + 1) % N_QUBIT) for i in range(N_QUBIT)]

# 四種歐拉角順序（原文只說「可分解為繞 X、Y、Z 的旋轉」，沒給順序）
EULER_ORDERS = {
    "RZ-RY-RX": ("rz", "ry", "rx"),
    "RX-RY-RZ": ("rx", "ry", "rz"),
    "RY-RZ-RX": ("ry", "rz", "rx"),
    "RY-RX-RZ": ("ry", "rx", "rz"),
}


def scale(kind: str, v: np.ndarray) -> np.ndarray:
    """把 tanh 後的 10 維特徵壓到旋轉角。三種合理寫法，原文未指定。"""
    if kind == "pi_tanh":
        return np.pi * np.tanh(v)
    if kind == "pi_minmax":
        lo, hi = v.min(), v.max()
        return (np.pi * (2 * (v - lo) / (hi - lo) - 1)) if hi > lo else np.zeros_like(v)
    if kind == "two_arctan":
        return 2.0 * np.arctan(v)
    raise ValueError(kind)


SCALINGS = ("pi_tanh", "pi_minmax", "two_arctan")


def gates_for(x: np.ndarray, theta: np.ndarray, euler: str, scaling: str):
    """回傳閘列表：[(閘名, [qubit...], 角度或 None), ...]。

    x     : (10,) 前端輸出的 10 維特徵（未縮放）
    theta : (DEPTH, N_QUBIT, 3) 可訓練參數
    """
    order = EULER_ORDERS[euler]
    angles = scale(scaling, np.tanh(x))[:N_QUBIT]   # 10 維 -> 取前 4 個當編碼角
    out = [("ry", [i], float(angles[i])) for i in range(N_QUBIT)]
    for d in range(DEPTH):
        for i in range(N_QUBIT):
            for k, g in enumerate(order):
                out.append((g, [i], float(theta[d, i, k])))
        for c, t in RING:
            out.append(("cx", [c, t], None))
    return out


def z_expectations(gates) -> np.ndarray:
    """純 NumPy 狀態向量參考實作（big-endian：軸 k = qubit k）。"""
    psi = np.zeros(1 << N_QUBIT, dtype=np.complex128)
    psi[0] = 1.0

    def apply_1q(mat, q):
        nonlocal psi
        v = psi.reshape(-1, 2, 1 << (N_QUBIT - 1 - q))
        a, b = v[..., 0, :], v[..., 1, :]
        psi = np.stack([mat[0, 0] * a + mat[0, 1] * b,
                        mat[1, 0] * a + mat[1, 1] * b], axis=-2).reshape(psi.shape)

    for name, qs, ang in gates:
        if name == "cx":
            c, t = qs
            idx = np.arange(1 << N_QUBIT)
            cb = (idx >> (N_QUBIT - 1 - c)) & 1
            psi = psi[idx ^ ((1 << (N_QUBIT - 1 - t)) * cb)]
            continue
        th = ang
        if name == "ry":
            m = np.array([[np.cos(th / 2), -np.sin(th / 2)],
                          [np.sin(th / 2), np.cos(th / 2)]], dtype=complex)
        elif name == "rz":
            m = np.array([[np.exp(-1j * th / 2), 0], [0, np.exp(1j * th / 2)]], dtype=complex)
        elif name == "rx":
            m = np.array([[np.cos(th / 2), -1j * np.sin(th / 2)],
                          [-1j * np.sin(th / 2), np.cos(th / 2)]], dtype=complex)
        else:
            raise ValueError(name)
        apply_1q(m, qs[0])

    p = np.abs(psi) ** 2
    idx = np.arange(1 << N_QUBIT)
    zs = []
    for q in range(N_QUBIT):
        bit = (idx >> (N_QUBIT - 1 - q)) & 1
        zs.append(float(np.sum(p * (1 - 2 * bit))))
    return np.array(zs)
