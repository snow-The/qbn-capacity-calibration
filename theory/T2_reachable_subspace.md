# T2. 為什麼狀態空間是指數的，可訓練參數卻是多項式的？

> **代號 TH1**｜理論文件 T2｜**RQ1（容量斷崖）的理論核心**｜★
> 教材代號：**G** = Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed.；
> **GS** = 同書 Instructor's Solution Manual；**A** = Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed.

---

## 問題陳述

T1 證明了 $n$ 個 qubit 的狀態空間是 $2^n$ 維。本文件要回答這個追問：

> **如果狀態空間是指數的，為什麼量子電路的可訓練參數只有多項式個？這個落差有多大？它在物理上是什麼意思？**

具體要推導三件事：

1. $n$ 個 qubit 上的么正群，其**物理上可分辨**的參數有幾個？（答案：$2^{2n}-1$）
2. 只放多項式個閘的電路，能觸及多大的子空間？（答案：至多等於參數個數）
3. 兩者的比值在本專案（5 qubit）是多少？

**先給結論**：$32^2-1=1023$ 對上 10 個可訓練角度，落差 **102.3 倍**。這就是 RQ1 所謂「可達子空間遠小於環境空間」的定量內容。

---

## 教科書基礎

| 書 | 章節 | 內容 | 本文件用在哪裡 |
|---|---|---|---|
| **G** | §3.6.1（L5355） | 「只有有限個 $N$ 個線性獨立狀態的系統，$\|S(t)\rangle$ 住在 $N$ 維向量空間，運算子是 $N\times N$ 矩陣——這是最簡單的量子系統」 | $N=2^n$ 的有限維框架 |
| **G** | §3.6.2（L5515–5529） | **算符的函數由冪級數定義**：$e^{\hat Q}\equiv1+\hat Q+\frac12\hat Q^2+\frac1{3!}\hat Q^3+\cdots$（Eq. 3.100） | $U=e^{-iHt/\hbar}$ 的意義 |
| **G** | §6.2（L11067–11100） | 平移算符 $\hat T(a)$ 是么正的（L11081）；**Problem 6.2（L11089）：$\hat Q$ Hermitian $\Rightarrow \hat U=\exp[i\hat Q]$ 么正** | 么正性與 Hermitian 生成元的對應 |
| **G** | §6.8 Translations in Time（L12122–12167） | **$\hat U(t)=\exp[-\frac{it}{\hbar}\hat H]$（Eq. 6.71）**，由 Taylor 展開推得（Eq. 6.68–6.69）；「$\hat H$ 是時間平移的生成元」；$\hat U(t)$ 是么正的（L12150） | 閘 = 么正 = 指數映射 |
| **G** | §6.8.1（L12168–12174） | Heisenberg 表象 $\hat Q_H(t)=\hat U^\dagger\hat Q\hat U$（Eq. 6.72） | 共軛變換 |
| **G** | §A.3（L20741–20976） | 矩陣、轉置伴隨、么正矩陣 | $N\times N$ 么正矩陣 |
| **G** | §A.6（L21339+） | Hermitian 變換 | 生成元的 Hermitian 性 |
| **A** | §2.2 Functions of Matrices（L4566–4638） | **Eq. 2.77** $\exp(\mathsf A)=\sum_j\frac1{j!}\mathsf A^j$；**Eq. 2.83** $\mathsf U=\exp(i\mathsf H)$ 在 $\mathsf H$ Hermitian 時么正，附完整證明；**Eq. 2.84** $\det(e^{\mathsf H})=e^{\operatorname{tr}\mathsf H}$；**Eq. 2.85** Baker–Hausdorff 公式 | 指數映射；跡與行列式的關係 |
| **A** | §5.3（L10897–11168） | **Eq. 5.42** 交換子 $[A,B]=AB-BA$；**Eq. 5.47** 伴隨 $\langle f\|Ag\rangle=\langle A^\dagger f\|g\rangle$；**Eq. 5.48** Hermitian；**Eq. 5.49** 么正 $U^\dagger=U^{-1}$；線性算符由矩陣元素完全決定（L11061） | 么正算符、算符代數 |
| **A** | §5.5（L11311–11432） | **么正變換**：$\mathbf c'=\mathsf U\mathbf c$，$\mathsf U^\dagger\mathsf U=1$（Eq. 5.71–5.73）；么正變換是正交旋轉在複空間的推廣 | 么正群 = 基底變換群 |
| **A** | §5.6（L11481–11522） | 算符的變換 **Eq. 5.76** $\mathsf A'=\mathsf U\mathsf A\mathsf U^\dagger=\mathsf U\mathsf A\mathsf U^{-1}$ | 共軛變換 |
| **A** | §6.4（L13021–13256） | Hermitian 矩陣對角化；**Spectral Decomposition（L13119）**；么正對角化 $S^{-1}MS$ | 譜分解、$\operatorname{tr}$ 的么正不變性 |
| **A** | §6.5（L13257+） | 正規矩陣 | 么正可對角化的條件 |
| **A** | **§17.7 Continuous Groups（L35107–35224）** | **★ 最關鍵**：L35113「推廣到 $n\times n$ 么正矩陣就是 $\mathrm{SU}(n)$ 與 $\mathrm{U}(n)$」；**L35115「一個連續群的 order 定義為指定其基礎表示所需的獨立參數個數……$\mathrm{SU}(n)$ 的 order 是 $n^2-1$」**；L35191「一個 Lie 群的獨立生成元個數等於該群的 order」；**Eq. 17.35–17.37** 生成元 $\mathsf U(\delta\varphi)=1+i\,\delta\varphi\,\mathsf S$、$\mathsf U(\varphi)=\exp(i\varphi\mathsf S)$；**Eq. 17.40** $\mathsf S=\mathsf S^\dagger$；**Eq. 17.41** $\operatorname{tr}\mathsf S=0$；Eq. 17.43 閉合關係 | **群維度定理與生成元形式** |
| **A** | §8.4 Variation method（L16250+）；§22.4（L47683+）、Rayleigh–Ritz（L47970） | 變分法、Rayleigh–Ritz | 為什麼「受限的參數族」是標準做法 |
| **GS** | Problem 3.25（L4163–4175） | 二能階系統的 $2\times2$ 矩陣對角化 | $N=2$ 的具體算例 |
| **GS** | Problem 3.24（L4155–4161） | $Q_{mn}=Q_{nm}^*$（Hermitian 矩陣元素） | 生成元的 Hermitian 性 |

---

## 推導

### 1. 閘就是么正變換；么正變換由 Hermitian 生成元取指數得到

**G §6.8** 給了閘與么正群的連結。從含時 Schrödinger 方程 $\hat H\Psi=i\hbar\frac{\partial}{\partial t}\Psi$ 出發，定義時間演化算符 $\hat U(t)$ 為 $\hat U(t)\Psi(x,0)=\Psi(x,t)$（Eq. 6.67）。G 用 Taylor 展開：

$$
\Psi(x,t)=\sum_{n=0}^{\infty}\frac{1}{n!}\left.\frac{\partial^n}{\partial t^n}\Psi(x,t)\right|_{t=0}t^n,
\qquad \frac{\partial^n}{\partial t^n}\Psi=\left(-\frac{i}{\hbar}\hat H\right)^{n}\Psi, \tag{G Eq. 6.68–6.69}
$$

因此（$H$ 不顯含時）

$$
\boxed{\ \hat U(t)=\exp\left[-\frac{it}{\hbar}\hat H\right]\ } \tag{G Eq. 6.71}
$$

G 同時註明「$\hat H$ 是時間平移的生成元」，且 $\hat U(t)$ 是么正的（見 **G Problem 6.2**）。**A §2.2 Eq. 2.83** 給了純代數的版本與證明：若 $\mathsf H^\dagger=\mathsf H$，則

$$
\mathsf U=\exp(i\mathsf H)\ \Longrightarrow\
\mathsf U^\dagger=\exp(-i\mathsf H^\dagger)=\exp(-i\mathsf H)=[\exp(i\mathsf H)]^{-1}=\mathsf U^{-1}. \tag{A Eq. 2.83}
$$

**A §17.7** 把它反過來寫成生成元形式（Eq. 17.35–17.36）：

$$
\mathsf U(\delta\varphi)=\mathbf 1+i\,\delta\varphi\,\mathsf S,
\qquad
\mathsf U(\varphi)=\lim_{N\to\infty}\left(1+\frac{i\varphi\mathsf S}{N}\right)^{N}=\exp(i\varphi\mathsf S). \tag{A Eq. 17.35–17.36}
$$

並由么正性得到生成元必須 Hermitian（Eq. 17.40）：$\mathsf S=\mathsf S^\dagger$。

**小結**：每個閘（可訓練旋轉、糾纏閘的參數化）都是 $\exp(i\theta\mathsf S)$ 的形式，$\mathsf S$ Hermitian。$n$ 個 qubit 的電路因此是么正群 $\mathrm U(2^n)$ 的一個元素，由 $N\times N$ 矩陣代表（$N=2^n$；**G §3.6.1 L5355** 已說明有限維系統就是 $N\times N$ 矩陣）。

### 2. $\mathrm U(N)$ 與 $\mathrm{SU}(N)$ 的實維度

**第一步：一般 $N\times N$ 么正矩陣有幾個實參數？**
一個複 $N\times N$ 矩陣有 $2N^2$ 個實參數。條件 $\mathsf U^\dagger\mathsf U=\mathbf 1$ 是一個 Hermitian 矩陣方程，含 $N^2$ 個**獨立**實條件（$\mathsf U^\dagger\mathsf U$ Hermitian，其對角 $N$ 個為實、非對角 $N(N-1)/2$ 個為複，共 $N+2\cdot\frac{N(N-1)}{2}=N^2$ 個實條件）。故

$$
\dim_{\mathbb R}\mathrm U(N)=2N^2-N^2=N^2 . \tag{2.1}
$$

**第二步：加上 $\det\mathsf U=1$ 扣掉 1 維。**
由 **A §2.2 Eq. 2.84** 的跡公式 $\det(e^{\mathsf H})=e^{\operatorname{tr}\mathsf H}$（A 註明其推導在 Eq. 6.27）。把 $\mathsf U$ 寫成 $\mathsf U=\exp(i\mathsf H)$（$\mathsf H$ Hermitian，第一步已證），則

$$
\det\mathsf U=\det(e^{i\mathsf H})=e^{\operatorname{tr}(i\mathsf H)}=e^{\,i\operatorname{tr}\mathsf H}.
$$

要求 $\det\mathsf U=1$ 即要求 $e^{i\operatorname{tr}\mathsf H}=1$，也就是 $\operatorname{tr}\mathsf H\in2\pi\mathbb Z$。在單位元附近（$\operatorname{tr}\mathsf H=0$）這**恰好是一個實條件**。故

$$
\boxed{\ \dim_{\mathbb R}\mathrm{SU}(N)=N^2-1\ } \tag{2.2}
$$

**A §17.7 L35115 直接給了這個結果**：「the order of the group $\mathrm{SU}(n)$ is $n^2-1$」。A 也說明（L35191）「獨立生成元個數 = 群的 order」。**Eq. 17.41** 對應同一件事：$\det\mathsf U=1\Rightarrow\operatorname{tr}\mathsf S=0$。

**第三步：物理上可分辨的是哪一個？**
全域相位不可觀測：$\mathsf U$ 與 $e^{i\alpha}\mathsf U$ 作用在態上給出**同一個**射線（ray）。因此物理上可分辨的變換群是**射影么正群**

$$
\mathrm{PU}(N)\cong\mathrm U(N)/\mathrm U(1)\cong\mathrm{SU}(N)/\mathbb Z_N .
$$

於是

$$
\boxed{\ \dim_{\mathbb R}\mathrm{PU}(N)=\dim_{\mathbb R}\mathrm U(N)-1=N^2-1=\dim_{\mathbb R}\mathrm{SU}(N)\ } \tag{2.3}
$$

**這是本文件最重要的一個式子，也是最容易講錯的地方。** 專案 `theory/README.md` 寫「么正群 $U(2^n)$ 的實維度是 $2^{2n}-1$」——嚴格說，$\dim_{\mathbb R}\mathrm U(N)=N^2$，而 $N^2-1$ 是 $\mathrm{SU}(N)$ 或 $\mathrm{PU}(N)$ 的維度。**兩者只差一個全域相位，而全域相位物理上不可觀測**，所以用在「可訓練容量」的討論上 $N^2-1$ 是正確的選擇。本文件一律用 $N^2-1$，並註明它是 $\mathfrak{su}(N)$／$\mathrm{PU}(N)$ 的維度。

**推論 2.1** 令 $N=2^n$：

$$
\dim_{\mathbb R}\mathfrak{su}(2^n)=(2^n)^2-1=\boxed{2^{2n}-1} . \tag{2.4}
$$

### 3. 本專案的數字

$n=5$ 時 $N=2^5=32$：

$$
\dim_{\mathbb R}\mathfrak{su}(32)=32^2-1=1024-1=\boxed{1023}. \tag{2.5}
$$

> **⚠️ 數字勘誤**：任務規格書與回報格式中出現的「$32^2-1=1013$」是**筆誤**。$32^2=1024$，減一為 **1023**。專案常數檔 `docs/_summary/00-專案規格常數.md`（**§二「硬性理論約束」表的密度矩陣實自由參數列**）與 `dev/qbn5_encoding.py` 的 `N_UNITARY_PARAMS`（`DIM ** 2 - 1`）都記載 **1023**，本文件與之一致。

順帶記錄同一算式的其他相關維度（$N=32$）：

| 對象 | 實維度 | 出處／理由 |
|---|---|---|
| $\mathfrak u(32)$ | $N^2=1024$ | (2.1) |
| $\mathfrak{su}(32)$／$\mathrm{PU}(32)$ | $N^2-1=\mathbf{1023}$ | (2.2)/(2.3)、**A §17.7 L35115** |
| 密度矩陣（跡 1、Hermitian） | $N^2-1=\mathbf{1023}$ | Hermitian $N\times N$ 為 $N^2$ 維，跡固定扣 1 |
| 純態流形 $\mathbb{CP}^{N-1}$ | $2N-2=62$ | $2N$ 個實參數扣歸一化與全域相位 |
| 一般 Hermitian 矩陣 | $N^2=1024$ | — |

### 4. 電路觸及多少？——可達流形的維度

現在換到「可訓練參數」那一側。

**設定**：電路是一串閘

$$
\mathsf U(\boldsymbol\theta)=\mathsf U_L\cdots\mathsf U_{k+1}\,\mathsf U_k(\theta_k)\,\cdots\mathsf U_1,
\qquad \boldsymbol\theta\in\mathbb R^{P}, \tag{2.6}
$$

其中 $P$ 是可訓練參數個數（每個參數屬於一個 $\exp(-i\theta_k\mathsf S_k/2)$ 形式的閘；非參數閘如 CX 是固定的）。本專案的閘序列見 `dev/qbn_circuit.py::qbn_state`：

$$
|0\rangle^{\otimes5}\ \xrightarrow{\ R_Y(\theta_i)\ \text{編碼（5 個，不可訓練）}\ }\
\xrightarrow{\ \text{環形 }CX\ (5\text{ 個})\ }\
\xrightarrow{\ R_Y(\phi_i),R_Z(\lambda_i)\ (10\text{ 個，可訓練})\ }
$$

`dev/qbn_circuit.py:155` 的 docstring 明載：「可訓練的旋轉層：每個 qubit 一個 RY 再一個 RZ，共 $2\times5=10$ 個參數」。故

$$
P_{\text{單層}}=2n=\boxed{10}\qquad(n=5). \tag{2.7}
$$

（`dev/qbn5_encoding.py::qbn_layer` 的 depth=2 版本有 $2\cdot n\cdot2=20$ 個，見該檔 L603。）

**定理 2.2（可達維度上界）**
固定初始態 $|\psi_0\rangle$，考慮參數映射

$$
\Phi:\ \mathbb R^{P}\longrightarrow\mathbb{CP}^{N-1},\qquad
\Phi(\boldsymbol\theta)=[\ \mathsf U(\boldsymbol\theta)|\psi_0\rangle\ ],
$$

其中 $[\cdot]$ 表示模掉全域相位的射線。則 $\Phi$ 的像（可達集）在任一正則點的**局部維度至多為 $P$**：

$$
\dim(\text{可達流形})\le P . \tag{2.8}
$$

*證明*：$\Phi$ 是 $\mathbb R^P$（$P$ 維流形）到 $\mathbb{CP}^{N-1}$ 的光滑映射。光滑映射在每一點的微分為線性映射 $d\Phi_{\boldsymbol\theta}:\mathbb R^P\to T_{[\psi]}\mathbb{CP}^{N-1}$，其秩至多為 $\dim\mathbb R^P=P$。由秩定理（rank theorem），像在該點附近同構於 $\mathbb R^{\operatorname{rank}d\Phi}$，故局部維度 $=\operatorname{rank}d\Phi_{\boldsymbol\theta}\le P$。$\square$

**微分的顯式形式**：對參數 $\theta_k$，

$$
\partial_k|\psi(\boldsymbol\theta)\rangle
=\mathsf U_L\cdots\mathsf U_{k+1}\,\big(\partial_k\mathsf U_k\big)\,\mathsf U_{k-1}\cdots\mathsf U_1|\psi_0\rangle . \tag{2.9}
$$

把 $P$ 個導數向量排成矩陣 $J\in\mathbb C^{N\times P}$（雅可比）。可達切空間是它們的**實**張量再模掉 $|\psi\rangle$ 的相位方向：

$$
\dim(\text{可達流形})=\operatorname{rank}_{\mathbb R}\big[\operatorname{Re}J\mid\operatorname{Im}J\big]-1 . \tag{2.10}
$$

（扣除 1 是因為 $|\psi\rangle$ 所在的相位方向落在張量內；若不在，則不需扣。）

**定義 2.3（富比尼–施帝度量）** 對應 (2.10) 的度量矩陣是

$$
G_{ij}=\operatorname{Re}\langle\partial_i\psi|\partial_j\psi\rangle
-\langle\partial_i\psi|\psi\rangle\langle\psi|\partial_j\psi\rangle,
\qquad \operatorname{rank}G=\dim(\text{可達流形}). \tag{2.11}
$$

**推論 2.4（本專案）** 由 (2.8)，

$$
\dim(\text{可達流形})\le P_{\text{單層}}=10
\quad\text{而}\quad
\dim_{\mathbb R}\mathfrak{su}(32)=1023 .
$$

兩者的比值

$$
\boxed{\ \frac{1023}{10}=102.3\ } \tag{2.12}
$$

也就是說，**么正群的 1023 個獨立方向上，這個電路只走得到 10 個。**

### 5. 為什麼這是「容量」的問題

把三個數字排在一起：

| 量 | 值 | 意義 |
|---|---|---|
| 狀態空間（複維度） | $2^n=32$ | 需要多少振幅描述一個態 |
| 純態流形（實維度） | $2N-2=62$ | 一個純態的自由度（模相位） |
| 么正群／密度矩陣（實維度） | $2^{2n}-1=1023$ | **理論上**最多能獨立控制的量 |
| 電路可訓練參數 | $P=10$（單層）／$20$（雙層） | **實際上**能控制的量 |
| 可達流形維度 | $\le P$ | 電路真正觸及的子空間 |

**「容量」的物理意義**：$\mathfrak{su}(2^n)$ 的 1023 是**環境空間**（ambient space）；電路能到達的集合（可達子空間）被 (2.8) 限制在 $P$ 維。RQ1 問的「容量」必須明確定義成後者，而不是前者——把 $2^n$ 當成容量，會得到「5 qubit 有 32 維容量」這種**高估**的結論。

**與變分法的關係**：這正是 **A §8.4（Variation method）** 與 §22.4（Rayleigh–Ritz）的標準局面——在一個**受限的參數族**裡找最優。A 的框架是「選一組帶參數的試驗函數，最小化期望值」；我們的電路就是一個（非線性）參數族，參數個數 $P$ 就是這個族的維度。

---

## 結論

1. $n$ 個 qubit 上的閘是么正變換 $\mathsf U=\exp(i\mathsf H)$，$\mathsf H$ Hermitian 且無跡（**G §6.8 Eq. 6.71**；**A §2.2 Eq. 2.83**、**§17.7 Eq. 17.36/17.40/17.41**）。
2. 物理上可分辨的么正變換群有 $2^{2n}-1$ 個實參數：
   $\dim_{\mathbb R}\mathfrak{su}(N)=N^2-1$，$N=2^n$（**A §17.7 L35115** 的 order 定理 + 跡條件 $N^2\to N^2-1$）。
3. 但一個含 $P$ 個可訓練參數的電路，其可達集是 $\mathbb R^P$ 的像，維度**至多 $P$**（定理 2.2）。
4. 本專案：$P=10$（單層，`dev/qbn_circuit.py:155`）對上 $1023$，比值 $\mathbf{102.3}$。
5. 因此「狀態空間 $2^n$ 維」與「可訓練容量」**不是同一件事**。$2^n$ 是描述一個態的代價；可訓練容量是 $P$，是多項式的。

---

## 對本專題的意義

**這是 RQ1 的理論核心**，具體提供三件可用的東西：

1. **「容量」的操作型定義。** RQ1 要掃描的「可訓練容量」應該是 $(n,L)\mapsto P=2nL$（線性於 qubit 數與深度），而**不是** $2^n$。本文件證明了兩者不可互換，並給出上界 (2.8)。
2. **斷崖的候選機制被縮小了。** 因為可達維度 $\le P$，增加容量**不可能**來自「探索更多希爾伯特空間」——增加 $n$ 或 $L$ 只是把參數族的維度往上推。RQ1 若觀察到非單調行為，機制只可能是：
   - **表達力不足**（$P$ 太小，參數族太窄）；
   - **最佳化變差**（參數變多後景觀變壞，見 T3 的梯度量測）；
   - **泛化變差**（容量相對於資料量過大）。
   本文件排除了「量子態空間本身很大所以應該更好」這個樸素猜測。
3. **與 T3 的分工。** T2 給的是**維度**上界（與梯度的好壞無關，是純幾何的）；T3 給的是**可訓練性**的動態考量。兩者合起來才是完整的 RQ1 論證。

**在實驗上的直接用途**：`dev/qbn5_encoding.py:604` 已經把 `su(32) 維度上界 = 1023` 印在報表裡，作為 ansatz 參數量（20）的對照。本文件補上那個對照**為什麼**成立。

---

## 數值驗證

腳本：`theory/verify/t1_t2_dimensions.py`（T2 部分）
執行：`uv run python projects/qbn-capacity-calibration/theory/verify/t1_t2_dimensions.py`

**實際輸出（節錄）**：

```
==========================================================================
T2【5】【6】su(N) 與 u(N) 的實維度（顯式建基底 + 秩檢定）
==========================================================================
  N=2   dim u(N) = 4     (N^2 = 4    )   dim su(N) = 3     (N^2-1 = 3)
  [PASS] N=2: dim su(N) = N^2-1 = 3
  [PASS] N=2: dim u(N) = N^2 = 4
  [PASS] N=2: 基底全 Hermitian，su(N) 基底全無跡
  N=4   dim u(N) = 16    (N^2 = 16   )   dim su(N) = 15    (N^2-1 = 15)
  N=8   dim u(N) = 64    (N^2 = 64   )   dim su(N) = 63    (N^2-1 = 63)
  N=32  dim u(N) = 1024  (N^2 = 1024 )   dim su(N) = 1023  (N^2-1 = 1023)
  [PASS] N=32: dim su(N) = N^2-1 = 1023
  [PASS] N=32: dim u(N) = N^2 = 1024
  → N = 2^5 = 32 時：dim su(32) = 1023，dim u(32) = 1024。

==========================================================================
T2【7】exp(iH) 么正、det(e^H) = e^{tr H}
==========================================================================
  [PASS] N=2: H Hermitian => U = exp(iH) 么正
  [PASS] N=2: det(e^H) = e^(tr H)（Arfken Eq. 2.84）
  [PASS] N=5: H Hermitian => U = exp(iH) 么正
  [PASS] N=5: det(e^H) = e^(tr H)（Arfken Eq. 2.84）
  [PASS] N=32: H Hermitian => U = exp(iH) 么正
  [PASS] N=32: det(e^H) = e^(tr H)（Arfken Eq. 2.84）

==========================================================================
T2【8】密度矩陣與純態流形的實維度
==========================================================================
  n=5: N = 32   一般 Hermitian 實維度 = 1024  （= N^2）  密度矩陣（跡 1）= 1023 （= N^2-1）  純態流形 = 62    （= 2N-2）
  [PASS] n=5: N^2-1 = 1023（對照專案常數 dev/qbn5_encoding.py:69 N_UNITARY_PARAMS）
  [PASS] n=5: 純態流形實維度 = 2N-2 = 62

==========================================================================
T2【9】★ 可達子空間維度：雅可比矩陣的秩
==========================================================================
  單層電路（與 dev/qbn_circuit.py 同構）：
    n   P=2n  rank_C(J)   rank_R  rank_FS   su(2^n)  su / rank_FS
    2      4          3        4        4        15           3.8
  [PASS] n=2: 可達維度 rank_FS = P = 4（參數化無冗餘）
    3      6          4        8        6        63          10.5
  [PASS] n=3: 可達維度 rank_FS = P = 6（參數化無冗餘）
    4      8          5       10        8       255          31.9
  [PASS] n=4: 可達維度 rank_FS = P = 8（參數化無冗餘）
    5     10          6       12       10      1023         102.3
  [PASS] n=5: 可達維度 rank_FS = P = 10（參數化無冗餘）
  [PASS] n=5: 可達維度遠小於 su(32) 的 1023 維   10 << 1023

  雙層電路（與 dev/qbn5_encoding.py::qbn_layer 同構，P = 4n）：
  n=5: P =  20  rank_C =  16  rank_R =  32  rank_FS =  20  su(32) = 1023
  [PASS] n=5: 雙層可達維度 rank_FS = P = 20
  [PASS] n=5: 雙層可達維度 << su(32) = 1023 維

  ★ 5 qubit 關鍵對照（本專案）：
      su(32) 維度（可訓練么正的上界，Arfken §17.7 的 N²−1） = 1023
      單層電路：可訓練參數 P = 10，可達維度 rank_FS = 10（dev/qbn_circuit.py:155）
      雙層電路：可訓練參數 P = 20，可達維度 rank_FS = 20（dev/qbn5_encoding.py:603）
      落差：su(32) 1023 維  vs  單層可達 10 維  →  1023/10 = 102.3 倍
      純態流形（模掉相位）也只有 2N−2 = 62 維。
  [PASS] ★ 1023 / 10 = 102.3（su(32) 與單層可訓練方向的落差）   1023 / 10 = 102.3
```

**驗證涵蓋**：

| 推導結果 | 驗證方式 | 結果 |
|---|---|---|
| (2.1) $\dim\mathrm U(N)=N^2$ | 顯式建 $\mathfrak u(N)$ 基底（$N^2$ 個 Hermitian 矩陣）並做數值秩檢定 | $N=2,4,8,32$ → $4,16,64,1024$ ✓ |
| (2.2) $\dim\mathrm{SU}(N)=N^2-1$ | 同上，去掉單位矩陣（無跡子空間） | $N=2,4,8,32$ → $3,15,63,1023$ ✓ |
| **A Eq. 2.83** $\exp(iH)$ 么正 | 隨機 Hermitian $H$，檢查 $\mathsf U\mathsf U^\dagger=\mathbf 1$ | 誤差 $\sim10^{-16}$ ✓ |
| **A Eq. 2.84** $\det(e^{\mathsf H})=e^{\operatorname{tr}\mathsf H}$ | 數值行列式 vs 指數化的跡 | $N=2,5,32$ 全過 ✓ |
| $N^2-1=1023$（本專案） | 與 `dev/qbn5_encoding.py:69` 的 `N_UNITARY_PARAMS` 對照 | 一致 ✓ |
| 純態流形 $2N-2=62$ | 維度計數 | ✓ |
| **(2.8) 可達維度 $\le P$** | 精確解析雅可比（(2.9)），(2.10)/(2.11) 的秩 | 單層 $P=10\to$ 秩 $=10$；雙層 $P=20\to$ 秩 $=20$ ✓ |

**關於三個秩的區別（本節最容易誤解的地方）**：腳本同時印出三個秩，它們的意義不同，我把它們的關係寫清楚：

- `rank_C`（雅可比在 $\mathbb C$ 上的秩）：$n=5$ 單層為 6。**這不是可達維度**，只是複結構的診斷量。
- `rank_R` $=\operatorname{rank}[\operatorname{Re}J\mid\operatorname{Im}J]$：$n=5$ 單層為 12。這是導數向量的**實**張量維度，仍含相位方向。
- `rank_FS` $=\operatorname{rank}G$（$G$ 見 (2.11)）：$n=5$ 單層為 **10**，雙層為 **20**。

**只有 `rank_FS` 是可達流形維度**，而它恰好等於參數個數 $P$——意思是這個參數化在該點**沒有冗餘**（飽和了定理 2.2 的上界）。三個秩的大小關係為

$$
\operatorname{rank\_FS}\;\le\;\operatorname{rank\_R}\;\le\;2\,P,
\qquad
\operatorname{rank\_C}\;\le\;P,
$$

與實測相符（$10\le12\le20$ 與 $6\le10$）。

---

## 待核實事項

- **么正群的「實維度」在指定教材中沒有以這個名字出現。** 已用關鍵字 `unitary group`、`SU(n)`、`U(n)`、`order`、`generators`、`Lie group` 搜尋：確切敘述在 **A §17.7 L35113（$\mathrm{SU}(n)$ 與 $\mathrm{U}(n)$ 的引介）** 與 **L35115（order of $\mathrm{SU}(n)$ is $n^2-1$）**。A 只給了 $\mathrm{SU}(n)$ 的 order；$\dim\mathrm U(N)=N^2$ 與 $\dim\mathrm{PU}(N)=N^2-1$ 是**本文件由 (2.1)/(2.3) 自行推導**並用數值秩檢定驗證的（見驗證表），**不是** A 的原文敘述。
- **$\mathrm{PU}(N)$ 與射影商的論證**（推導第 2 節第三步）在指定教材中沒有對應章節。已用關鍵字 `projective`、`ray`、`global phase`、`U(1)`、`quotient` 搜尋三本書，未找到。這是標準的量子資訊教科書內容，**本文件標為 TODO(核實)**：若要引用，應改引 Nielsen & Chuang 或同級教材，不應掛在 G/A/GS 名下。
- **$32^2-1$ 的筆誤**：規格書寫 1013，正確為 **1023**（見推導第 3 節的勘誤框）。已與 `docs/_summary/00-專案規格常數.md`（**§二「硬性理論約束」表**）及 `dev/qbn5_encoding.py` 的 `N_UNITARY_PARAMS` 交叉核對。
- **「閘 = $\exp(i\theta\mathsf S)$」對糾纏閘的適用性**：CNOT 在計算基底是置換矩陣，**不能**寫成單一 $\exp(i\theta \mathsf S)$ 形式（它是離散的，不由連續參數生成）。本文件的 $P$ 只計**可訓練旋轉**閘，CNOT 視為固定的么正，這與 `dev/qbn_circuit.py` 的實作一致。
