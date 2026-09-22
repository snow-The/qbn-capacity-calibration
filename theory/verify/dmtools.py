"""dmtools.py — 密度矩陣／超算符工具箱（T1–T6 理論文件的獨立數值驗證用）。

設計原則：本檔**刻意不依賴** ``dev/qbn_sim.py`` 的內部實作，而是自己用
:math:`2^n \\times 2^n` 的密度矩陣直接做么正演化與量子通道。因此它同時是
``dev/qbn_sim.py``（態向量路徑）的**獨立交叉驗證**：兩條路徑若在無通道時
給出相同機率，才代表我們的推導沒有寫錯。

位元公約（與 ``dev/qbn_sim.py`` 一致，big-endian）
--------------------------------------------------
基底索引 :math:`i` 寫成 :math:`n` 位元二進位，**最左邊是 qubit 0**：

.. math:: i = \\sum_{q=0}^{n-1} b_q \\, 2^{\\,n-1-q}

因此「對 qubit ``t`` 作用的單閘」在張量積中的位置是第 ``t`` 個因子
（最左），對應 :math:`I_{2^t} \\otimes U \\otimes I_{2^{n-t-1}}`。

為何需要密度矩陣
----------------
去相位（dephasing，Tucci 的 ``cl`` 算子）**不是么正演化**，無法用態向量
表示；它必須作用在密度矩陣上。這是 T4/T5 兩份文件的核心。
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

# ----------------------------------------------------------------------
# 基礎：單閘、嵌入、置換
# ----------------------------------------------------------------------

_I2 = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def ry(theta: float) -> np.ndarray:
    r""":math:`R_Y(\theta)=\exp(-i\theta Y/2)`（與 ``cudaq.ry`` 同公約）。"""
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def ry_deriv(theta: float) -> np.ndarray:
    r""":math:`\mathrm{d}R_Y/\mathrm{d}\theta`（解析式，供 T2 的雅可比用）。"""
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[-s / 2, -c / 2], [c / 2, -s / 2]], dtype=complex)


def rz(theta: float) -> np.ndarray:
    r""":math:`R_Z(\theta)=\exp(-i\theta Z/2)=\mathrm{diag}(e^{-i\theta/2},e^{+i\theta/2})`。"""
    return np.array(
        [[np.exp(-1j * theta / 2), 0.0], [0.0, np.exp(1j * theta / 2)]],
        dtype=complex,
    )


def rz_deriv(theta: float) -> np.ndarray:
    r""":math:`\mathrm{d}R_Z/\mathrm{d}\theta`。"""
    return np.array(
        [[-0.5j * np.exp(-1j * theta / 2), 0.0],
         [0.0, 0.5j * np.exp(1j * theta / 2)]],
        dtype=complex,
    )


def embed1(U: np.ndarray, target: int, n: int) -> np.ndarray:
    """把 :math:`2\\times2` 的單閘 ``U`` 嵌入 ``n`` qubit 的 :math:`2^n\\times2^n` 空間。"""
    if not 0 <= target < n:
        raise ValueError(f"target {target} 超出 [0,{n})")
    return np.kron(np.kron(np.eye(2 ** target, dtype=complex), U),
                   np.eye(2 ** (n - target - 1), dtype=complex))


def perm_full(perm: Sequence[int], n: int) -> np.ndarray:
    """由基底索引置換 ``perm``（``perm[i]`` = 第 ``i`` 個基底被送到哪裡）建置換矩陣。"""
    dim = 2 ** n
    M = np.zeros((dim, dim), dtype=complex)
    for i, j in enumerate(perm):
        M[j, i] = 1.0
    return M


def cnot_full(control: int, target: int, n: int) -> np.ndarray:
    """整個 ``n`` qubit 空間中的 CNOT（在計算基底是**置換矩陣**）。"""
    dim = 2 ** n
    perm = np.arange(dim)
    bc = (perm >> (n - 1 - control)) & 1
    perm = perm ^ (bc << (n - 1 - target))
    return perm_full(perm, n)


def bit_of(index: int, q: int, n: int) -> int:
    """基底索引 ``index`` 中 qubit ``q`` 的位元。"""
    return (index >> (n - 1 - q)) & 1


def sign_of(index: int, q: int, n: int) -> int:
    r""":math:`Z` 在基底 ``index`` 上的特徵值 :math:`(-1)^{b_q}\\in\\{+1,-1\\}`。"""
    return 1 - 2 * bit_of(index, q, n)


def pauli_full(P: np.ndarray, target: int, n: int) -> np.ndarray:
    """把單 qubit Pauli 嵌入 ``n`` qubit 空間。"""
    return embed1(P, target, n)


# ----------------------------------------------------------------------
# 態、密度矩陣、部分跡、熵
# ----------------------------------------------------------------------

def pure_dm(psi: np.ndarray) -> np.ndarray:
    r""":math:`\rho=|\psi\rangle\langle\psi|`。"""
    psi = np.asarray(psi, dtype=complex).reshape(-1)
    return np.outer(psi, psi.conj())


def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    r""":math:`\rho\mapsto U\rho U^\dagger`。"""
    return U @ rho @ U.conj().T


def partial_trace(rho: np.ndarray, keep: Sequence[int], n: int) -> np.ndarray:
    r"""對 ``keep`` 以外的子系統取部分跡 :math:`\mathrm{Tr}_{\bar k}[\rho]`。"""
    keep = sorted(int(k) for k in keep)
    traced = [q for q in range(n) if q not in keep]
    R = rho.reshape((2,) * (2 * n))
    perm = keep + traced + [n + k for k in keep] + [n + t for t in traced]
    R = np.transpose(R, perm)
    dk, dt = 2 ** len(keep), 2 ** len(traced)
    R = R.reshape(dk, dt, dk, dt)
    return np.einsum("itjt->ij", R)


def vn_entropy(rho: np.ndarray, base: float = 2.0) -> float:
    r"""馮紐曼熵 :math:`S=-\mathrm{Tr}[\rho\log\rho]`（``base=2`` 時單位是 bit）。"""
    ev = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    ev = ev[ev > 1e-14]
    if ev.size == 0:
        return 0.0
    return float(-np.sum(ev * np.log(ev) / np.log(base)))


def purity(rho: np.ndarray) -> float:
    r""":math:`\mathrm{Tr}[\rho^2]`。"""
    return float(np.real(np.trace(rho @ rho)))


def probs_from_rho(rho: np.ndarray) -> np.ndarray:
    r"""Born 機率 :math:`P(i)=\rho_{ii}=\mathrm{Tr}[|i\rangle\langle i|\,\rho]`。"""
    return np.real(np.diag(rho))


# ----------------------------------------------------------------------
# 去相位通道（Tucci 的 cl 算子）
# ----------------------------------------------------------------------

def dephase_mask(n: int, qubits: Iterable[int] | None = None) -> np.ndarray:
    r"""去相位通道的**遮罩矩陣**（作用在向量化的 :math:`\rho` 上）。

    對子集 :math:`S`，通道為 :math:`\mathcal{D}_S(\rho)=\sum_{\mathbf b_S}
    P_{\mathbf b_S}\rho P_{\mathbf b_S}`，其中 :math:`P_{\mathbf b_S}` 把
    :math:`S` 上的位元投影到給定樣式、其餘 qubit 不動。作用在矩陣元上：

    .. math:: (\mathcal{D}_S(\rho))_{ij} = \rho_{ij}\prod_{q\in S}\delta_{b_q(i),b_q(j)}

    利用 :math:`\delta_{b_i b_j}=\tfrac12(1+s_i s_j)`（:math:`s_q=(-1)^{b_q}`），
    等價於「對 :math:`S` 上的 qubit 隨機施加 :math:`Z` 再平均」：

    .. math:: \mathcal{D}_S(\rho)=\frac{1}{2^{|S|}}\sum_{\mathbf s\in\{\pm1\}^{|S|}}
              Z_{\mathbf s}\,\rho\,Z_{\mathbf s}

    本函式回傳的是第一式的遮罩（``(dim^2, dim^2)`` 對角矩陣）。
    """
    dim = 2 ** n
    if qubits is None:
        qubits = range(n)
    qubits = list(qubits)
    s = np.stack([np.array([sign_of(i, q, n) for q in qubits]) for i in range(dim)])
    # agree[i,j] = 1 若 i,j 在 S 上所有位元都相同
    agree = np.prod((1 + s[:, None, :] * s[None, :, :]) / 2.0, axis=-1)
    return agree.reshape(-1)


def dephase(rho: np.ndarray, n: int, qubits: Iterable[int] | None = None) -> np.ndarray:
    r"""對 ``qubits`` 施加去相位通道，回傳新的密度矩陣。"""
    mask = dephase_mask(n, qubits)
    return (rho.reshape(-1) * mask).reshape(2 ** n, 2 ** n)


def dephase_sum_form(rho: np.ndarray, n: int, qubits: Iterable[int] | None = None) -> np.ndarray:
    r"""去相位的**求和形式** :math:`\sum_{\mathbf b}P_{\mathbf b}\rho P_{\mathbf b}`。

    這是 :func:`dephase` 的獨立實作（走 Kraus／投影子求和，不走遮罩），
    兩者必須給出相同結果；在本檔的自我測試中會互相比對。
    """
    if qubits is None:
        qubits = list(range(n))
    qubits = sorted(int(q) for q in qubits)
    dim = 2 ** n
    out = np.zeros_like(rho)
    s = np.stack([np.array([sign_of(i, q, n) for q in qubits]) for i in range(dim)])
    for pat in range(2 ** len(qubits)):
        # 投影子 P_pat = prod_q (1 + s_q(p) Z_q)/2
        target = np.array([(pat >> (len(qubits) - 1 - k)) & 1 for k in range(len(qubits))])
        sel = np.all(s == (1 - 2 * target)[None, :], axis=1)
        P = np.zeros((dim, dim), dtype=complex)
        P[np.arange(dim)[sel], np.arange(dim)[sel]] = 1.0
        out += P @ rho @ P.conj().T
    return out


def kraus_dephase_1q() -> tuple[np.ndarray, np.ndarray]:
    r"""回傳單 qubit 去相位的 Kraus 算符 :math:`K_0=|0\rangle\langle0|`、:math:`K_1=|1\rangle\langle1|`。"""
    K0 = np.array([[1, 0], [0, 0]], dtype=complex)
    K1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return K0, K1


# ----------------------------------------------------------------------
# 超算符（column-stacking 向量化）——T5 的「交換子」用
# ----------------------------------------------------------------------

def superop_unitary(U: np.ndarray) -> np.ndarray:
    r"""么正通道 :math:`\rho\mapsto U\rho U^\dagger` 的超算符。

    採 column-stacking：:math:`\mathrm{vec}(A\rho B)=(B^{\mathsf T}\otimes A)\mathrm{vec}(\rho)`，
    故 :math:`\hat{\mathcal U}=(U^\dagger)^{\mathsf T}\otimes U=U^{*}\otimes U`。
    """
    return np.kron(U.conj(), U)


def superop_dephase(n: int, qubits: Iterable[int] | None = None) -> np.ndarray:
    r"""去相位通道的超算符（對角矩陣，等價於 :func:`dephase_mask`）。"""
    return np.diag(dephase_mask(n, qubits))


def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    r""":math:`[A,B]=AB-BA`。"""
    return A @ B - B @ A
