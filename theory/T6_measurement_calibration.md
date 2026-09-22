# T6. 測量理論與校準的關係：Born 法則與測量作為取樣

> **代號 TH1**｜理論文件 T6｜對應研究問題 RQ2（校準消融）
> 教材代號：**G** = Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed.；
> **GS** = 同書 Instructor's Solution Manual；**A** = Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed.

---

## 問題陳述

RQ2 要測量校準（calibration），而校準是**機率分布**的性質。本文件要回答：

1. **Born 法則**的教科書形式是什麼？如何寫成 $P(x)=\operatorname{Tr}[M_x\rho]$？
2. 為什麼「測量**天生就是取樣**」？
3. 這與古典貝氏神經網路（Bayesian Neural Network, BNN）需要跑 $T$ 次蒙地卡羅前向的差別在哪裡？
4. **對校準的具體後果**是什麼？（有限 shots 會不會污染 ECE？）

**核心結論**：量子測量是**從一個固定的分布 $p$ 反覆取樣**。因此它的不確定性是**偶然的（aleatoric）**、二項式的（標準誤 $\propto1/\sqrt{\text{shots}}$），而且**收斂到 $p$ 本身**——這與古典 BNN 需要 $T$ 份權重才有分布，在**結構上不同**。

---

## 教科書基礎

| 書 | 章節 | 內容 | 本文件用在哪裡 |
|---|---|---|---|
| **G** | §1.2 The Statistical Interpretation（L338–445） | 波函數的統計詮釋；$|\Psi|^2$ 是機率密度 | Born 法則的最初形式 |
| **G** | §3.3.1 Theorem 1/2（L4613–4647） | Hermitian 算符的特徵值為實、特徵函數正交 | 觀測量的可能值 |
| **G** | §3.4 Generalized Statistical Interpretation（L4791–4919） | **★ 核心**：測量 $Q$ 必得 $\hat Q$ 的一個特徵值；離散譜的機率是 $\|c_n\|^2$、$c_n=\langle f_n\|\Psi\rangle$（**Eq. 3.43**）；連續譜是 $\|c(z)\|^2dz$（**Eq. 3.44**）；**「測量後波函數坍縮到對應的特徵態」**（L4807）；完備性給 $\sum_n\|c_n\|^2=1$（Eq. 3.47）；期望值 $\langle Q\rangle=\sum_nq_n\|c_n\|^2$（Eq. 3.49） | **Born 法則**、坍縮、歸一化 |
| **G** | §3.4（L4855–4861） | 用廣義統計詮釋**重現**位置測量的原始詮釋：$c(y)=\Psi(y,t)$，故機率為 $\|\Psi(y,t)\|^2dy$ | 一般法則 $\to$ 特例的一致性 |
| **G** | §3.6.2 Eq. 3.91（L5437–5446） | 投影算符 $\hat P=\|\alpha\rangle\langle\alpha\|$ | $M_x=\|x\rangle\langle x\|$ |
| **G** | §3.6.2 Eq. 3.93（L5453–5463） | 完備性 $\sum_n\|e_n\rangle\langle e_n\|=\mathbf 1$ | $\sum_xM_x=\mathbf 1$（POVM 完備性） |
| **G** | §12.3.1 Eq. 12.16/12.20（L20225–20249） | $\rho_{ij}=\langle e_i\|\hat\rho\|e_j\rangle$；$\langle A\rangle=\operatorname{Tr}(\rho A)$ | **$P(x)=\operatorname{Tr}[M_x\rho]=\rho_{xx}$** |
| **G** | §12.4 No-Clone（L20433–20471） | 不可複製定理；「量子測量通常是**破壞性的**（destructive），因為它改變被測系統的狀態」 | 為什麼不能靠複製來增加資訊 |
| **G** | §12.5（L20473–20493） | 測量過程的角色；「沒有測量時波函數依 Schrödinger 方程確定性地演化」；**L20493 對 decoherence 的定義** | 么正 vs 測量的分界 |
| **A** | §5.4 Eq. 5.61（L11195–11221） | 期望值 $\langle A\rangle=\langle\psi\|A\|\psi\rangle$，並證明自伴算符給實數；$\langle A\rangle=\mathbf c^\dagger\mathsf A\mathbf c$ | 期望值的矩陣形式 |
| **A** | §6.4 Expectation Values（L13155+） | 由譜分解算期望值 | $\operatorname{Tr}(\rho A)$ 的譜觀點 |
| **A** | §5.5（L11311–11432） | 么正變換保持內積 | 機率守恆 |
| **A** | §23.1 Probability: Definitions（L48321–48578） | 機率公設、簡單性質 | 機率分布的語言 |
| **A** | **§23.2 Random Variables（L48580–48900）** | 隨機變數；**Computing Discrete Probability Distributions（L48646）**；**Moments of Probability Distributions（L48836）** | **離散分布與其動差** |
| **A** | §23.3 Binomial Distribution（L49080–49202） | **二項分布**；平均與變異數 | **$\operatorname{Var}=np(1-p)$，標準誤 $\propto1/\sqrt n$** |
| **A** | §23.5 Gauss' Normal Distribution（L49385–49516） | 常態分布；Poisson／二項的極限 | 大 $n$ 時的多項式 $\to$ 常態 |
| **A** | §23.5 Limits of Poisson and Binomial（L49446–49516） | 二項分布的極限行為 | 取樣誤差的量級 |
| **A** | **§23.7 Statistics（L49762–50314）** | **Error Propagation（L49766）**；Fitting Curves to Data（L49858）；**$\chi^2$ 分布（L49974）**；Student $t$（L50114） | 統計誤差與配適 |
| **GS** | §3 Formalism（L3775+） | 第 3 章習題解 | 形式論的具體算例 |
| **GS** | Problem 3.23（L4147–4153） | 投影算符冪等、特徵值 $\{0,1\}$ | $M_x$ 的性質 |
| **GS** | Problem 3.24（L4155–4161） | $Q_{mn}=Q_{nm}^*$ | $\rho$ 的 Hermitian 性 |

### ⚠️ 指定教材**沒有**的東西

| 概念 | 搜尋關鍵字 | G | A | GS |
|---|---|---|---|---|
| POVM | `POVM` | **0** | **0** | — |
| 期望校準誤差（ECE） | `calibration`、`ECE`、`expected calibration error` | 0（需另查） | 0 | 0 |
| 量子通道 | `Kraus`、`channel`、`completely positive` | **0** | **0** | **0** |

**因此**：
- **Born 法則本身在教材中完整具備**（**G §3.4**），這是本文件最紮實的部分。
- **$P(x)=\operatorname{Tr}[M_x\rho]$ 這個寫法**是把 **G Eq. 3.43**（$\|c_n\|^2$）與 **G Eq. 12.20**（$\langle A\rangle=\operatorname{Tr}(\rho A)$）**合起來**得到的；本文件在推導第 1 節逐步導出，並說明每一步來自哪一條。
- **POVM 的一般形式**不在教材中（`POVM` 在三本書 0 命中）。本文件只用到**投影測量** $M_x=\|x\rangle\langle x\|$（這是 **G Eq. 3.91** 的投影算符），並證明它是合法的 POVM，**不需要**引入一般 POVM 的理論。
- **ECE 與校準**不在教材中。本文件只從 Born 法則推出「測量 = 取樣」，再**用我們自己的數值實驗**量化它對 ECE 的影響；**ECE 的定義本身標為外部**（見待核實）。

---

## 推導

### 1. 從 Born 法則到 $P(x)=\operatorname{Tr}[M_x\rho]$

**第一步：Born 法則（G §3.4，Eq. 3.43）。**
G 的**廣義統計詮釋**原文（L4795）：

> "If you measure an observable $Q(x,p)$ on a particle in the state $\Psi(x,t)$, you are certain to get one of the eigenvalues of the hermitian operator $\hat Q$. If the spectrum of $\hat Q$ is discrete, the probability of getting the particular eigenvalue $q_n$ associated with the (orthonormalized) eigenfunction $f_n(x)$ is
> $$|c_n|^2,\quad\text{where}\quad c_n=\langle f_n|\Psi\rangle. \tag{G Eq. 3.43}$$"

對計算基底的投影測量，取 $\hat Q$ 為某個 qubit 的 $\hat Z$。$n$ 個 qubit 時，取觀測量為「所有 qubit 的 $Z$」，其共同特徵態就是計算基底 $\{|x\rangle\}_{x\in\{0,1\}^n}$，特徵值 $x$ 標記了結果。於是

$$
P(x)=|c_x|^2,\qquad c_x=\langle x|\psi\rangle=\alpha_x
\quad\Longrightarrow\quad
\boxed{\ P(x)=|\alpha_x|^2\ } \tag{6.1}
$$

——即 T1 的 (1.3) 中第 $x$ 個振幅的模平方。**這就是專案 `dev/qbn_sim.py::probabilities` 實作的 $|\alpha_i|^2$**（該檔 L277–283 明確註明「Born 規則的計算基底機率」）。

**第二步：用密度算符重寫（G Eq. 12.16 + 12.20）。**
對純態 $\rho=|\psi\rangle\langle\psi|$（**G Eq. 12.14**），由 **G Eq. 12.16**：

$$
\rho_{xx}=\langle x|\hat\rho|x\rangle=\langle x|\psi\rangle\langle\psi|x\rangle
=\alpha_x\alpha_x^{*}=|\alpha_x|^2=P(x). \tag{6.2}
$$

**更一般地**，對混合態 $\rho=\sum_kp_k|\Psi_k\rangle\langle\Psi_k|$（**G Eq. 12.28**），由 Born 法則與全機率公式，

$$
P(x)=\sum_kp_k\big|\langle x|\Psi_k\rangle\big|^2
=\sum_kp_k\langle x|\Psi_k\rangle\langle\Psi_k|x\rangle
=\langle x|\Big(\sum_kp_k|\Psi_k\rangle\langle\Psi_k|\Big)|x\rangle
=\langle x|\hat\rho|x\rangle=\rho_{xx}. \tag{6.3}
$$

**第三步：寫成跡的形式。**
取**投影測量**（**G Eq. 3.91** 的投影算符，取 $|\alpha\rangle=|x\rangle$）

$$
\boxed{\ M_x=|x\rangle\langle x|\ } \tag{6.4}
$$

則由跡的循環性（**A §2.2** 的跡性質）與 $M_x^2=M_x$（**GS Problem 3.23**），

$$
\boxed{\ P(x)=\operatorname{Tr}[M_x\rho]=\operatorname{Tr}\big[|x\rangle\langle x|\rho\big]
=\langle x|\rho|x\rangle=\rho_{xx}\ } \tag{6.5}
$$

最後一步是把 $\langle x|\rho|x\rangle$ 併回矩陣元（**G Eq. 12.16**）。

**性質 6.1（$M_x$ 是合法 POVM）** 由 **GS Problem 3.23**，$M_x=|x\rangle\langle x|$ 是投影算符：$M_x\ge0$（半正定）且 $M_x^2=M_x$。又由 **G Eq. 3.93** 的完備性（$\sum_n|e_n\rangle\langle e_n|=\mathbf 1$）：

$$
\sum_{x\in\{0,1\}^n}M_x=\sum_x|x\rangle\langle x|=\mathbf 1_{2^n} . \tag{6.6}
$$

故 $\{M_x\}$ 滿足 POVM 的兩條件（正性與完備性），且

$$
\sum_xP(x)=\sum_x\operatorname{Tr}[M_x\rho]=\operatorname{Tr}\Big[\Big(\sum_xM_x\Big)\rho\Big]=\operatorname{Tr}[\rho]=1, \tag{6.7}
$$

**歸一化由跡自動承擔，不需要 softmax。** 這對應專案常數檔 §二 的硬性約束第 2 條（「正規化由跡承擔，不可用 softmax」）。

### 2. 為什麼測量「天生就是取樣」

**命題 6.2** 給定一個固定的 $\rho$，在計算基底上做 $N$ 次獨立的投影測量，得到的計數 $\{n_x\}$ 服從**多項式分布**

$$
P(\{n_x\})=\frac{N!}{\prod_xn_x!}\prod_x\big[P(x)\big]^{n_x},
\qquad \sum_xn_x=N . \tag{6.8}
$$

*論證*：由 (6.5)，每一次測量都以機率 $P(x)$ 得到結果 $x$，且各次測量互相獨立。$N$ 次獨立、每次 $2^n$ 種結果的多項式分布即 (6.8)。

**推論 6.3（頻率收斂到 Born 機率）** 記 $\hat p_x=n_x/N$，則由 **A §23.3 二項分布**的動差公式（邊際上 $n_x\sim\mathrm{Bin}(N,P(x))$）：

$$
\mathbb E[\hat p_x]=P(x),\qquad
\boxed{\ \operatorname{Var}[\hat p_x]=\frac{P(x)\big(1-P(x)\big)}{N}\ }
\quad\Longrightarrow\quad
\text{標準誤}=\sqrt{\frac{P(x)(1-P(x))}{N}}\ \propto\ \frac{1}{\sqrt N}. \tag{6.9}
$$

由 **A §23.5**（二項分布的極限）與大數法則，$\hat p_x\to P(x)$。

**這就是「測量天生就是取樣」的精確內容**：(6.9) 的漲落是**二項式**的，**只取決於 $N$**，與電路本身無關；而且**期望值就是 $P(x)$**——也就是說，取樣收斂到**那一個**分布 $p$，不是收斂到某個分布族。**隨機性來自「讀出」，不來自「電路」。**

**這在結構上與古典 BNN 不同。** 古典 BNN 的預測分布是

$$
p_{\text{BNN}}(y\mid x)=\int p(y\mid x,\mathbf w)\,p(\mathbf w\mid\mathcal D)\,d\mathbf w
\approx\frac1T\sum_{t=1}^{T}p\big(y\mid x,\mathbf w^{(t)}\big), \tag{6.10}
$$

需要**$T$ 份權重樣本 $\mathbf w^{(t)}$**（$T$ 次前向、或存 $T$ 份權重）。量子電路只需要**一次**前向（得到 $\rho$ 或 $\alpha$），分布 $P(x)$ 就已經完全確定；增加 shots 只是在**估計**同一個 $P(x)$。

| | 量子測量 | 古典 BNN（MC 推論） |
|---|---|---|
| 分布從哪來 | 單一 $\rho$，$P(x)=\operatorname{Tr}[M_x\rho]$ | $T$ 份權重，$\frac1T\sum_tp(y\|x,\mathbf w^{(t)})$ |
| 需要幾次前向 | **1** | **$T$** |
| 額外成本 | shots $N$（測量次數） | $T$ 份權重／$T$ 次前向 |
| 漲落性質 | 二項式，$\propto1/\sqrt N$ | 蒙地卡羅，$\propto1/\sqrt T$ **加上**權重後驗的離散性 |
| 不確定性類型 | **偶然（aleatoric）**——$P(x)$ 是確定的 | 偶然 **+ 認知（epistemic）**——權重後驗本身就是分布 |
| 能不能靠增加次數消除 | **可以**（$N\to\infty$ 時 $\hat p\to P$ 精確） | **不能**（$T\to\infty$ 收斂到 (6.10) 的積分，但那個積分仍是分布） |

**最後一列是關鍵區別**：量子的取樣誤差是**可消除的估計誤差**（增加 shots 即可）；BNN 的 $T$ 是**認知不確定性的離散近似**，$T\to\infty$ 不會讓預測變成單點。

**T6 的數值驗證直接量了這件事**（【3】）：重複次數 $T$ 從 5 增到 100 時，逐態標準差與二項式預測的比值分別是 $1.0975$、$0.9572$、$1.0021$——**散布不隨重複次數改變**，正是「每次都是從同一個 $p$ 獨立取樣」的簽名。

### 3. 對校準的後果

**定義（外部，見待核實）** 等寬分箱（$M$ 箱）的**期望校準誤差（Expected Calibration Error, ECE）** 是

$$
\mathrm{ECE}=\sum_{b=1}^{M}\frac{|B_b|}{N}\Big|\operatorname{acc}(B_b)-\operatorname{conf}(B_b)\Big|, \tag{6.11}
$$

$B_b$ 是預測信心落在第 $b$ 箱的樣本集合。

**關鍵問題**：由 (6.9)，用**有限 shots** 估出來的 $\hat p$ 與真值 $p$ 差約 $1/\sqrt N$。這個誤差會不會**灌進 ECE**，讓我們誤判模型的校準品質？

**量級估計**：ECE 是 $|\operatorname{acc}-\operatorname{conf}|$ 的加權平均。若 confidence 有大小 $\epsilon\sim1/\sqrt N$ 的隨機誤差，則 ECE 的**系統性**位移大致是二階的（因為 $|\cdot|$ 在零附近不可微，但期望值仍以 $\epsilon^2$ 的尺度偏移），而 ECE 的**漲落**是一階的（$\sim\epsilon$）。以本專案 $N=4096$：

$$
\epsilon\approx\frac{1}{\sqrt{4096}}=\frac{1}{64}=0.0156 . \tag{6.12}
$$

**實際量測（見數值驗證【4】）**：ECE 的系統性位移只有 $-1.9\times10^{-5}$（相對模型自身 ECE $0.047706$ 是 **0.040%**），而 ECE 的**雜訊標準差**是 $0.000373$。兩者都遠小於模型自身的校準誤差。

> **結論（RQ2 的關鍵）**：在 $N=4096$ shots 下，**測量雜訊對 ECE 的貢獻可忽略**。因此 RQ2 的消融實驗若量到 ECE 的顯著變化，那是**模型效應**（去相位改變了 $P(x)$，見 T5 的 $0.05023467$），**不是**測量雜訊。
>
> **反過來說**：論文若要報「ECE $=0.007$」這種量級（如 Wang et al. 2026 的 BQNN-2），**必須同時聲明 shots 數**；否則無法區分「模型校準好」與「測量次數多」。

---

## 結論

1. **Born 法則**（**G §3.4 Eq. 3.43**）：$P(q_n)=|c_n|^2$，$c_n=\langle f_n|\Psi\rangle$。對計算基底的投影測量，$P(x)=|\alpha_x|^2$。
2. **跡形式**：取 $M_x=|x\rangle\langle x|$（**G Eq. 3.91**），則
   $$\boxed{P(x)=\operatorname{Tr}[M_x\rho]=\rho_{xx}}$$
   $\{M_x\}$ 是合法 POVM（正性來自 **GS Problem 3.23**，完備性來自 **G Eq. 3.93**），且**歸一化由跡自動給出**（(6.7)），不需 softmax。
3. **測量 = 從固定分布取樣**：$N$ 次測量的計數服從多項式分布 (6.8)，$\operatorname{Var}[\hat p_x]=P(x)(1-P(x))/N$（由 **A §23.3** 的二項分布動差），標準誤 $\propto1/\sqrt N$。
4. **與古典 BNN 的結構差異**：量子電路**一次前向**就確定 $P(x)$，$N$ 只影響估計精度；古典 BNN 需要 $T$ 份權重才有分布，且 $T\to\infty$ 不消除認可不確定性。
5. **對校準**：$N=4096$ 時取樣雜訊對 ECE 的系統性位移是 $-1.9\times10^{-5}$（模型的 $0.040\%$），**可忽略**。

---

## 對本專題的意義

**這是「量子測量作為不確定性來源」的理論基礎**，並直接支撐 RQ2 的方法論：

1. **不確定性分解的正當性。** 專案常數檔 §四規劃「預測熵 $H[\bar p]$（aleatoric 近似）＋ 互資訊 $I[y;\theta]$（epistemic）」。由 (6.9) 與 (6.10) 的對比：量子層的測量取樣貢獻的是**偶然不確定性**；而「epistemic」那一項若要存在，必須來自**權重／參數的分布**（例如多個 seed、多個初始化），**不能**來自重複測量同一個電路。**這一點必須在實驗設計裡寫清楚**，否則會把「取樣雜訊」誤當成「模型不確定性」。
2. **shots 的角色被釘死了。** 4096 shots 是**估計 $P(x)$ 的精度**（標準誤 $1.56\%$），不是模型容量的一部分。增加 shots 只會讓 $\hat p$ 更接近 $P$；它**不會**改變模型。這也呼應 T2：可訓練容量由參數 $P_{\text{param}}$ 決定，不是由 shots 決定。
3. **RQ2 的量測可行性已被驗證。** 去相位在正確位置造成的分布變化是 $0.05023467$（T5），而測量雜訊對 ECE 的貢獻是 $\sim10^{-5}$——**訊號比雜訊大約三個數量級**。因此 RQ2 的消融實驗在 $N=4096$ 下是有足夠檢定力的。
4. **歸一化不可用 softmax 的理論依據。** (6.7) 顯示 $\sum_xP(x)=1$ 由 $\sum_xM_x=\mathbf 1$ 與 $\operatorname{Tr}\rho=1$ **自動**成立。softmax 是非線性的，會破壞這個結構（專案常數檔 §二 硬性約束第 2 條）。本文件提供該約束的推導。
5. **與 T4/T5 的閉環。** T5 證明了去相位在尾端「隱形」是因為量測只讀對角元；T6 給出「量測只讀對角元」的**精確理由**：$P(x)=\operatorname{Tr}[M_x\rho]=\rho_{xx}$。三份文件合起來是 RQ2 的完整理論鏈：
   **$\rho$ 的對角元 $\to$ Born 法則 $\to$ 測量分布 $\to$ 校準指標**。

---

## 數值驗證

腳本：`theory/verify/t6_measurement_sampling.py`（**12/12 通過**）
執行：`uv run python projects/qbn-capacity-calibration/theory/verify/t6_measurement_sampling.py`

**實際輸出（節錄）**：

```
【1】Born 法則：P(x) = Tr[M_x rho] = rho_xx（兩條獨立路徑）
  [PASS] 態向量路徑 |alpha_i|^2 == 密度矩陣路徑 rho_ii   max|dp| = 2.776e-17
  [PASS] Tr[M_x rho] == rho_xx（Born 法則的顯式驗證）   max|dp| = 0.000e+00
  [PASS] 歸一化 sum_x P(x) = Tr[rho] = 1   sum = 1.000000000000000
  [PASS] M_x = |x><x| 是合法 POVM（M_x >= 0 且 sum_x M_x = I）
  32 維 Born 機率前 5 大 = [0.236703 0.133734 0.072994 0.043356 0.041561]

【2】測量 = 從**固定分布**取樣：多項式分布與 1/sqrt(shots)
     shots         TV 距離       max|dp|   1/sqrt(shots)   TV/(1/sqrt)
        64      0.274344      0.067631        0.125000        2.1948
       256      0.109443      0.024405        0.062500        1.7511
      1024      0.054985      0.010990        0.031250        1.7595
      4096      0.032424      0.015982        0.015625        2.0751
     16384      0.018363      0.005850        0.007812        2.3504
     65536      0.008058      0.002799        0.003906        2.0628
  [PASS] TV 距離隨 shots 單調下降（大致）   shots=64: 0.274344  ->  shots=65536: 0.008058
  [PASS] TV 距離 ~ C/sqrt(shots)（比值為 O(1) 常數，不過度漂移）   比值範圍 = [1.751, 2.350]
  [PASS] 測量是從**同一** p 取樣：經驗分布收斂到 p_sv（不是收斂到別的分布）   shots=65536 時 TV = 0.008058

【3】偶然 vs 認知不確定性：量子測量的漲落是純二項式
  關鍵測試：固定 ρ（單一電路、單一參數），重複『獨立的 shots 次測量』，
  看 32 維機率估計的**逐次散布**。若是純取樣雜訊，散布應恰為二項式大小
  sqrt(p(1-p)/shots)（shots=4096），而且**不隨重複次數改變**。
  （T=1 時逐次散布依定義為 0，故從 T=5 起量。）

    重複次數 T = 5    觀測逐態標準差上限 = 0.007289   二項式預測 = 0.006642   比值 = 1.0975
  [PASS] T=5: 散布 ≈ 二項式預測（純取樣雜訊，無認知成分）   比值 = 1.0975
    重複次數 T = 30   觀測逐態標準差上限 = 0.006357   二項式預測 = 0.006642   比值 = 0.9572
  [PASS] T=30: 散布 ≈ 二項式預測（純取樣雜訊，無認知成分）   比值 = 0.9572
    重複次數 T = 100  觀測逐態標準差上限 = 0.006656   二項式預測 = 0.006642   比值 = 1.0021
  [PASS] T=100: 散布 ≈ 二項式預測（純取樣雜訊，無認知成分）   比值 = 1.0021

【4】★ 有限 shots 對 ECE 的貢獻（RQ2 的雜訊底線）
  shots = 4096，M = 10 等寬分箱，蒙地卡羅 400 次。
  ECE 採逐基底態的二元校準定義（32 個二元預測，等寬 10 箱）。
    解析機率（無取樣雜訊）的 ECE            = 0.047706
    4096 shots 的 ECE 平均                  = 0.047687
    4096 shots 的 ECE 標準差（雜訊底線）    = 0.000373
    取樣造成的 ECE 系統性位移              = -0.000019
    位移 / 模型自身 ECE                    = 0.040%
  [PASS] 取樣雜訊對 ECE 的系統性位移可忽略（|位移| < 1e-3）   位移 = -0.000019
  [PASS] 雜訊底線（ECE 標準差）遠小於模型自身的 ECE   std = 0.000373  vs  模型 ECE = 0.047706

總結
  通過 12 / 12 項
```

### 驗證對照表

| 推導結果 | 驗證方式 | 結果 |
|---|---|---|
| (6.1) $P(x)=\|\alpha_x\|^2$ | 態向量路徑（`dev/qbn_sim.py`） | — |
| **(6.2)/(6.5) $P(x)=\rho_{xx}=\operatorname{Tr}[M_x\rho]$** | 三條獨立路徑比對：$\|\alpha_i\|^2$、$\rho_{ii}$、逐一算 $\operatorname{Tr}[M_x\rho]$ | $2.776\times10^{-17}$、$0.000\times10^0$ ✓ |
| (6.7) $\sum_xP(x)=1$ | 數值加總 | $1.000000000000000$ ✓ |
| **性質 6.1** $M_x\ge0$、$\sum_xM_x=\mathbf 1$ | 逐個特徵值 + 矩陣和 | ✓（與 **GS Problem 3.23**、**G Eq. 3.93** 一致） |
| **(6.9) 標準誤 $\propto1/\sqrt N$** | 6 個 shots 值的 TV 距離 vs $1/\sqrt{\text{shots}}$ | 比值 $[1.751,2.350]$（O(1) 常數）✓ |
| **命題 6.2 多項式分布、收斂到 $p$** | 經驗分布 vs 解析 $p$ | shots$=65536$ 時 TV $=0.008058$ ✓ |
| **「不隨重複次數改變」** | $T=5,30,100$ 的逐態標準差 vs 二項式預測 | 比值 $1.0975,0.9572,1.0021$ ✓ |
| **(6.11) ECE 的取樣雜訊貢獻** | 400 次蒙地卡羅 | 位移 $-1.9\times10^{-5}$（模型的 0.040%）、標準差 $3.73\times10^{-4}$ ✓ |

**一個方法論聲明（必須寫清楚）**：腳本裡的 ECE 用的是**逐基底態的二元校準定義**（把 32 個基底態視為 32 個二元預測），而不是分類器常用的「預測類別 vs 真實類別」。**因此表中「解析 ECE $=0.047706$」不是本專案分類器的 ECE**，只是這個診斷量的基線。這個定義足以回答本節的問題（「取樣雜訊貢獻多少」），因為 $N$ 的效應與 ECE 的具體定義無關；但**不可**把 $0.047706$ 拿去與 Wang et al. 的 $0.007$ 相比。真正的分類器 ECE 必須用 10 類的預測信心計算（專案常數檔 §四：$M=10$ 等寬分箱）。

---

## 待核實事項

1. **$P(x)=\operatorname{Tr}[M_x\rho]$ 的寫法**：這個**形式**在 G 中沒有逐字出現。已用 `Tr[M`, `trace`, `Born rule`, `measurement postulate` 等關鍵字搜尋 G。我把它當作 **G Eq. 3.43**（$\|c_n\|^2$，Born 法則）與 **G Eq. 12.20**（$\langle A\rangle=\operatorname{Tr}(\rho A)$）的**組合**推導（推導第 1 節逐步寫出），並在文中說明來源。這是**本文件的推導**，不是教材原文。
2. **POVM 的一般理論**：`POVM` 在三本書**0 命中**。本文件只用到投影測量 $M_x=|x\rangle\langle x|$（**G Eq. 3.91**），並在**性質 6.1** 中就地證明它的兩條件（正性用 **GS Problem 3.23**、完備性用 **G Eq. 3.93**），**未引入**一般 POVM 理論。若後續章節要用「學習式 POVM 讀出」（`dev/qbn5_encoding.py::POVMReadout`），應外引 Nielsen & Chuang §2.2.6。
3. **ECE 的定義 (6.11)**：**不在指定教材中**。已用 `calibration`、`expected calibration error`、`ECE`、`Brier` 搜尋三本書，未找到。標為**外部定義**（標準機器學習文獻：Guo et al. 2017, *On Calibration of Modern Neural Networks*）。本文件只**使用**它，不聲稱它來自 G/A/GS。
4. **古典 BNN 的蒙地卡羅推論 (6.10)**：不在指定教材中。標為外部（Gal & Ghahramani 2016 一類）。本文件只用它作**對照**，且對照的邏輯（1 次前向 vs $T$ 次前向）不依賴特定 BNN 論文。
5. **「偶然 vs 認知」的分類**：這是機器學習的術語（aleatoric/epistemic），三本物理教材沒有。本文件在 (6.9)/(6.10) 的對比中**自行定義**了它在這裡的意思（「可藉增加次數消除」vs「不可」），並在「對本專題的意義」第 1 點提醒：epistemic 項必須來自參數／初始化分布，不能來自重複測量。
6. **A §23.5 的「Limits of Poisson and Binomial」小節號**：A 的第 23 章在 OCR 轉錄中層級有 `### 23.5 GAUSS' NORMAL DISTRIBUTION`（L49385）與 `### Limits of Poisson and Binomial Distributions`（L49446，無編號）的混用。依 AGENTS.md 的規定「以目錄語義為準，不信標題層級」，本文件把 L49446 歸為 **§23.5 的子小節**。**TODO(核實)**：若需精確編號請回查 PDF。
7. **ECE 數值不可跨定義比較**：見「數值驗證」末尾的方法論聲明。腳本的 $0.047706$ 是逐基底態的診斷量，**不是**分類器 ECE，不可與 Wang et al. 的 $0.007$ 並列。
