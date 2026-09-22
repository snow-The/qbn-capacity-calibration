# T5. 為什麼去相位必須插在么正層之前才有效？★

> **代號 TH1**｜理論文件 T5｜對應研究問題 RQ2（校準消融）｜**最易做錯的一步**
> 教材代號：**G** = Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed.；
> **GS** = 同書 Instructor's Solution Manual；**A** = Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed.

---

## 問題陳述

T4 證明了計算基底去相位 $\mathcal E(\rho)=\operatorname{diag}(\rho)$。本文件要回答 RQ2 實驗設計裡**最容易做錯**的一步：

> **為什麼去相位接在電路尾端量不到效果，必須插在么正層之前？**

要證三件事：

1. **CNOT 與計算基底去相位交換**：$\mathcal E\circ\text{CNOT}=\text{CNOT}\circ\mathcal E$。更一般地，**任何「么模仿塊矩陣」（monomial matrix）** 都與 $\mathcal E$ 交換。
2. **推論**：若去相位之後只接這一類閘，則最終的 32 維量測機率**完全不變**——所以尾端去相位在量測上**隱形**。
3. **反之**，$R_Y$（以及任何會在計算基底成員之間造出疊加的閘）與 $\mathcal E$ **不對易**，所以插在它**之前**才有效果。

**本地實測數據（本文件的核心證據）**：

| 去相位插入位置 | 32 維機率的最大變化 |
|---|---|
| 電路最尾端（緊接量測） | $1.4\times10^{-17}$（$\approx0$） |
| 中間，之後只接 CX | $1.4\times10^{-17}$（$\approx0$） |
| 中間，之後接含 $R_Y/R_Z$ 的完整層 | $\mathbf{0.0502}$ |

---

## 教科書基礎

| 書 | 章節 | 內容 | 本文件用在哪裡 |
|---|---|---|---|
| **A** | §5.3 Commutation of Operators（L10925–10949） | **交換子 $[A,B]=AB-BA$（Eq. 5.42）**；$[A,B]=-[B,A]$、$[A,B+C]=[A,B]+[A,C]$、$k[A,B]=[kA,B]=[A,kB]$（Eq. 5.44）；Example 5.3.1（Eq. 5.45）$[x,p^2]=2ip$ 的**逐步推導示範** | **交換子的語言（本文件的主工具）** |
| **A** | §5.3 Functions of Operators（L11165–11168） | 算符的函數；**Baker–Hausdorff 公式 Eq. 2.85** | 指數形式的閘 |
| **A** | §2.2 Eq. 2.85（L4634–4638） | $\exp(-\mathsf T)\mathsf A\exp(\mathsf T)=\mathsf A+[\mathsf A,\mathsf T]+\frac1{2!}[[\mathsf A,\mathsf T],\mathsf T]+\cdots$ | 「交換 $\iff$ 展開只留零階項」 |
| **A** | §2.2 Eq. 2.80（L4582–4588） | **Euler 恆等式 $\exp(i\sigma_k\theta)=\mathbf 1_2\cos\theta+i\sigma_k\sin\theta$**（由 $\sigma_k^2=1$ 收集奇偶次項導出） | $R_Y,R_Z$ 的封閉形式 |
| **A** | §2.2 Eq. 2.83（L4602–4608） | $\mathsf U=\exp(i\mathsf H)$ 么正 | $R_Y,R_Z$ 么正 |
| **A** | §5.4 Example 5.4.3(c)（L11273–11277） | **$AB$ 自伴 iff $A,B$ 交換**；「注意我們先把 $A$ 移到左邊（因為它自伴所以不需要 dagger），它就成了隨後移動 $B$ 時 $B$ 必須作用的對象」 | 交換性與算符次序的關係 |
| **A** | §5.6 Eq. 5.76（L11497–11509） | $\mathsf A'=\mathsf U\mathsf A\mathsf U^\dagger=\mathsf U\mathsf A\mathsf U^{-1}$（么正相似變換） | 共軛變換 |
| **A** | §5.5 Eq. 5.71–5.73（L11357–11375） | 么正變換 $\mathbf c'=\mathsf U\mathbf c$，$\mathsf U^\dagger\mathsf U=1$ | 基底變換 |
| **A** | §5.7 Invariants（L11593+） | 么正變換保持的本徵性質 | 跡、譜的么正不變性 |
| **A** | §6.4（L13021–13256） | 譜分解（L13119）；么正對角化；**Simultaneous Diagonalization（L13095）** | 可同時對角化 $\iff$ 交換 |
| **G** | §3.6.2 Eq. 3.91/3.93（L5437–5477） | 投影算符 $\hat P=\|\alpha\rangle\langle\alpha\|$；完備性 $\sum_n\|e_n\rangle\langle e_n\|=1$ | 去相位的 Kraus 算符與完備性（T4） |
| **G** | §12.3.1 Eq. 12.16（L20225–20229） | $\rho_{ij}=\langle e_i\|\hat\rho\|e_j\rangle$；$\rho_{ii}=P(e_i)$ | **量測只讀對角元** |
| **G** | §12.3.2 Eq. 12.26（L20301–20307） | 密度算符的演化 $i\hbar\frac{d\hat\rho}{dt}=[\hat H,\hat\rho]$；**Problem 12.4(b)** | 演化與交換子 |
| **G** | §4.4（L7713+） | 自旋、Pauli 矩陣、$R_Y$ 型旋轉 | $R_Y$ 的定義 |
| **G** | §6.8.1 Eq. 6.72（L12170–12174） | Heisenberg 表象 $\hat Q_H=\hat U^\dagger\hat Q\hat U$ | 共軛變換的量子力學用法 |
| **G** | §3.4 Eq. 3.43–3.44（L4791–4806） | 廣義統計詮釋：$P(q_n)=\|c_n\|^2$，$c_n=\langle f_n\|\Psi\rangle$；**「測量後波函數坍縮」** | 為什麼只有對角元可觀測 |
| **GS** | Problem 3.23（L4147–4153） | 投影算符 $P^2=P$、特徵值 $\{0,1\}$ | 去相位的 Kraus 算符（T4） |
| **GS** | Problem 3.24（L4155–4161） | $Q_{mn}=Q_{nm}^*$ | Hermitian 矩陣元素 |
| **GS** | **Problem 3.33（L4301+）** | **Sequential measurements（連續測量）** | 次序為什麼有意義 |

### ⚠️ 指定教材**沒有**的東西

已用關鍵字搜尋確認：`Kraus`、`channel`、`quantum operation`、`superoperator`、`POVM`、`completely positive`、`\bChoi\b` 在三本書**全部 0 命中**。

**因此**：「通道」與「超算符」的語言不是從教材來的。但本文件的**主要工具——交換子**——是**A §5.3 Eq. 5.42** 的原文內容，且 A 的 **Example 5.3.1（Eq. 5.45）** 示範了完全相同的手法（把 $AB-BA$ 插入 $BA$ 重排成可辨識的交換子）。本文件照著這個手法做。

---

## 推導

### 0. 記號

由 T4，計算基底去相位是線性映射（**通道**）

$$
\mathcal E(\rho)=\sum_{b\in\{0,1\}^n}P_b\,\rho\,P_b,\qquad
P_b=|\mathbf b\rangle\langle\mathbf b|,\qquad
\mathcal E(\rho)=\operatorname{diag}(\rho). \tag{5.1}
$$

（$n$ 個 qubit 時 $b$ 跑 $2^n$ 個值；此處 $\mathbf b$ 是位元字串，$P_b$ 是秩一投影算符。）對么正 $U$ 定義么正通道

$$
\mathcal U(\rho)=U\rho\,U^\dagger . \tag{5.2}
$$

**問題**：$\mathcal E\circ\mathcal U\overset{?}{=}\mathcal U\circ\mathcal E$？等價地：$[\mathcal E,\mathcal U]=0$？

### 1. 核心引理：么模仿塊矩陣與去相位交換

**定義 5.1（么模仿塊矩陣，monomial matrix）** 一個 $d\times d$ 矩陣 $U$ 若每一列與每一行**恰有一個**非零元素，稱為么模仿塊矩陣。等價地

$$
U=D_\phi\,\Pi,\qquad D_\phi=\operatorname{diag}(e^{i\phi_1},\dots,e^{i\phi_d}),\quad
\Pi\ \text{是置換矩陣}. \tag{5.3}
$$

（$U$ 么正 $\Rightarrow$ 那些非零元素的模為 1，故可寫成 (5.3)。）

**引理 5.2** 若 $U$ 是么模仿塊矩陣，則 $UP_bU^\dagger=P_{\pi(b)}$，其中 $\pi$ 是由 (5.3) 中 $\Pi$ 誘導的基底置換。

*證明*：先把 $U$ 作用在 $|\mathbf b\rangle$ 上。由 (5.3)，

$$
U|\mathbf b\rangle=D_\phi\Pi|\mathbf b\rangle=D_\phi|\pi(\mathbf b)\rangle=e^{i\phi_{\pi(\mathbf b)}}|\pi(\mathbf b)\rangle .
$$

因此

$$
UP_bU^\dagger=U|\mathbf b\rangle\langle\mathbf b|U^\dagger
=\Big(e^{i\phi_{\pi(\mathbf b)}}|\pi(\mathbf b)\rangle\Big)\Big(e^{-i\phi_{\pi(\mathbf b)}}\langle\pi(\mathbf b)|\Big)
=|\pi(\mathbf b)\rangle\langle\pi(\mathbf b)|=P_{\pi(\mathbf b)} .
\qquad\square
$$

**注意相位 $e^{\pm i\phi}$ 自動抵消**——因為投影算符是秩一的，前後相位互為共軛。這是這個引理能成立的關鍵。

**定理 5.3（交換性）** 若 $U$ 是么模仿塊矩陣，則

$$
\boxed{\ \mathcal E\big(U\rho U^\dagger\big)=U\,\mathcal E(\rho)\,U^\dagger
\quad\text{對所有}\ \rho\ } \tag{5.4}
$$

即 $\mathcal E\circ\mathcal U=\mathcal U\circ\mathcal E$。

*證明*：由 (5.1) 與引理 5.2，

$$
\mathcal E\big(U\rho U^\dagger\big)
=\sum_bP_b\,U\rho U^\dagger\,P_b
=\sum_b U\Big(\underbrace{U^\dagger P_bU}_{=\,P_{\pi^{-1}(b)}}\Big)\rho
\Big(\underbrace{U^\dagger P_bU}_{=\,P_{\pi^{-1}(b)}}\Big)^\dagger U^\dagger
=U\left[\sum_bP_{\pi^{-1}(b)}\,\rho\,P_{\pi^{-1}(b)}\right]U^\dagger .
$$

因為 $\pi$ 是 $\{0,1\}^n$ 上的**一一對應**，$\{P_{\pi^{-1}(b)}:b\}$ 與 $\{P_b:b\}$ 是同一個集合，故括號內 $=\mathcal E(\rho)$。於是 (5.4) 成立。$\square$

**這一步用了什麼**：只是「對一個集合重新索引」。**沒有用到任何關於 $\rho$ 的假設。**

**推論 5.4（CNOT 的特例）** CNOT 作用在計算基底上把 $|\mathbf b\rangle\mapsto|\mathbf b\oplus e_t\rangle$（若控制位為 1），故是**置換矩陣**，也就是么模仿塊矩陣（$\phi\equiv0$）。因此

$$
\boxed{\ \mathcal E\big(\text{CNOT}\,\rho\,\text{CNOT}^\dagger\big)
=\text{CNOT}\,\mathcal E(\rho)\,\text{CNOT}^\dagger\ } \tag{5.5}
$$

**這正是專案要求證明的核心命題。** 同樣的論證對 $X$、$Z$、$S$、$T$、$CZ$、SWAP、$R_Z$ 全部成立（見數值驗證【1】：全部 `max|D U − U D| = 0`）。

### 2. 推論：尾端去相位在量測上隱形

**定理 5.5** 設電路分成兩段：$U$（么正），之後接一段**只由么模仿塊閘組成**的 $V$（例如只由 CNOT 組成），最後在計算基底量測。則去相位插在 $U$ 與 $V$ **之間**時，量測機率**完全不變**：

$$
P_{\text{after}}(i)=P_{\text{before}}(i)\qquad\text{對所有}\ i .
$$

*證明*：最終密度算符分別是

$$
\text{after}:\quad \rho_a=V\,\mathcal E\big(U\rho_0U^\dagger\big)\,V^\dagger,
\qquad
\text{before}:\quad \rho_b=V\,\big(U\rho_0U^\dagger\big)\,V^\dagger .
$$

用定理 5.3（$V$ 是么模仿塊），$\rho_a=\mathcal E\big(VU\rho_0U^\dagger V^\dagger\big)=\mathcal E(\rho_b)$。

量測機率是對角元（**G Eq. 12.16** / Eq. 3.43：$P(i)=\rho_{ii}$），而 $\mathcal E$ **保留對角元**（T4 定理 4.5）：

$$
P_{\text{after}}(i)=\big[\mathcal E(\rho_b)\big]_{ii}=\big[\rho_b\big]_{ii}=P_{\text{before}}(i). \qquad\square
$$

**特例（電路最尾端）** 取 $V=\mathbf 1$（空的），立即得到：**去相位接在電路最尾端時，量測機率完全不變。** 這就是本地實測 $1.4\times10^{-17}$ 的定理版本。

> **⚠️ 這是 RQ2 實驗設計的致命陷阱。**
> 若把去相位接在尾端，量到的差異是數值誤差等級（實測 $1.4\times10^{-17}$），
> 就會得到「量子性沒有貢獻」的**錯誤結論**。
> **正確做法：把去相位插在含有 $R_Y$ 的層之前。**

### 3. 反例：$R_Y$ 不交換

**引理 5.6** $R_Y(\theta)=\exp(-i\frac\theta2Y)$ 不是么模仿塊矩陣（當 $\theta\notin\pi\mathbb Z$）。

*證明*：由 **A Eq. 2.80** 的 Euler 恆等式（A 的推導是「用 $\sigma_k^2=1$ 把 $\theta$ 的奇偶次項分別收集」），取 $\sigma_k=Y$：

$$
R_Y(\theta)=\mathbf 1_2\cos\frac\theta2-i\,Y\sin\frac\theta2
=\begin{pmatrix}\cos\frac\theta2&-\sin\frac\theta2\\[2pt] \sin\frac\theta2&\cos\frac\theta2\end{pmatrix}.
$$

當 $\sin\frac\theta2\neq0$ 時，第一列有**兩個**非零元素，違反定義 5.1。$\square$

**$R_Z$ 反而交換。** 由 $R_Z(\theta)=\operatorname{diag}(e^{-i\theta/2},e^{+i\theta/2})$，它是對角的，故是么模仿塊矩陣（$\Pi=\mathbf 1$），由定理 5.3 **$R_Z$ 與 $\mathcal E$ 交換**。

> **精確化（本文件必須指出的一點）**：專案 README 寫「必須把去相位插在含 $R_Y/R_Z$ 的層之前」。嚴格的說法是：**$R_Z$ 單獨與去相位交換，$R_Y$ 不交換**。那一層之所以「有效」，是因為它含有 $R_Y$。若某一層只有 $R_Z$ 與 CX，則去相位插在它前面**同樣量不到效果**。本文件的數值驗證【1】確認 $R_Z(0.7)$ 的交換子範數為 $0.000\times10^0$，$R_Y(0.7)$ 為 $3.221\times10^{-1}$。

**最小反例（兩條路徑）** 取初態 $|+\rangle=\frac{1}{\sqrt2}(|0\rangle+|1\rangle)$，閘 $R_Y(\theta)$，$\theta=\pi/4$。

*路徑 A（先 $R_Y$ 再去相位）*：
先 $R_Y(\theta)|+\rangle$，振幅為

$$
\begin{pmatrix}\cos\frac\theta2&-\sin\frac\theta2\\ \sin\frac\theta2&\cos\frac\theta2\end{pmatrix}
\frac{1}{\sqrt2}\begin{pmatrix}1\\1\end{pmatrix}
=\frac{1}{\sqrt2}\begin{pmatrix}c-s\\ s+c\end{pmatrix},
\qquad c\equiv\cos\frac\theta2,\ s\equiv\sin\frac\theta2 .
$$

再**去相位**（殺掉非對角元，只留 $|\cdot|^2$ 在對角線上）：

$$
P^{(A)}=\left(\frac{(c-s)^2}{2},\ \frac{(s+c)^2}{2}\right)
=\left(\frac{1-\sin\theta}{2},\ \frac{1+\sin\theta}{2}\right),
$$

最後一步用了 $c^2+s^2=1$ 與 $2cs=\sin\theta$。

*路徑 B（先去相位再 $R_Y$）*：
$|+\rangle$ 的密度算符是 $\rho=\frac12\begin{pmatrix}1&1\\1&1\end{pmatrix}$。去相位殺掉非對角元：

$$
\mathcal E(\rho)=\frac12\begin{pmatrix}1&0\\0&1\end{pmatrix}=\frac{\mathbf 1_2}{2}.
$$

而 $\frac{\mathbf 1}{2}$ 在**任何**么正變換下不變：$R_Y\frac{\mathbf 1}{2}R_Y^\dagger=\frac{\mathbf 1}{2}R_YR_Y^\dagger=\frac{\mathbf 1}{2}$。故

$$
P^{(B)}=\left(\tfrac12,\ \tfrac12\right).
$$

*兩者的差*：

$$
\big|P^{(A)}_0-P^{(B)}_0\big|=\left|\frac{1-\sin\theta}{2}-\frac12\right|=\frac{\sin\theta}{2}
\ \xrightarrow{\ \theta=\pi/4\ }\ \frac{1}{2\sqrt2}=0.353553 . \tag{5.6}
$$

**這就是「順序有意義」的最小例子**：路徑 B 的結果是「完全無資訊」的均勻分布，因為去相位把 $|+\rangle$ 變成了最大混合態 $\frac{\mathbf 1}{2}$，而最大混合態不含任何方向資訊。本文件的數值驗證【4】量到 $P^{(A)}=(0.146447,0.853553)$、$P^{(B)}=(0.500000,0.500000)$，差 $0.353553$，與 (5.6) 相符。

### 4. 超算符語言：把交換子寫成矩陣

上面的定理 5.3 是算符層級的。我們也可以把它寫成**超算符**（作用在向量化的 $\rho$ 上）的**交換子**，這樣「交換子是否為零」就是一個可數值計算的矩陣問題。

**定義 5.7（向量化與超算符）** 採 column-stacking：把 $\rho$ 的**行**依序堆成向量 $\operatorname{vec}(\rho)$。則

$$
\operatorname{vec}(A\rho B)=(B^{\mathsf T}\otimes A)\operatorname{vec}(\rho) . \tag{5.7}
$$

於是

$$
\widehat{\mathcal U}=(U^\dagger)^{\mathsf T}\otimes U=U^{*}\otimes U,
\qquad
\widehat{\mathcal E}=\sum_bP_b\otimes P_b . \tag{5.8}
$$

**交換子條件**：$\mathcal E\circ\mathcal U=\mathcal U\circ\mathcal E\iff[\widehat{\mathcal E},\widehat{\mathcal U}]=0$，其中（**A Eq. 5.42**）

$$
[\widehat{\mathcal E},\widehat{\mathcal U}]
=\widehat{\mathcal E}\widehat{\mathcal U}-\widehat{\mathcal U}\widehat{\mathcal E} . \tag{5.9}
$$

**數值結果**（$n=2$，超算符是 $16\times16$）：

$$
\big\|[\widehat{\mathcal E},\widehat{\mathcal U}_{\text{CNOT}}]\big\|_F=0.000000,\quad
\text{非零元素 }0\text{ 個};
\qquad
\big\|[\widehat{\mathcal E},\widehat{\mathcal U}_{R_Y(0.7)}]\big\|_F=1.288435,\quad
\text{非零元素 }16\text{ 個}.
$$

**這是「CNOT 交換、$R_Y$ 不交換」在交換子語言下的直接體現。**

### 5. 所以正確的電路該長什麼樣

由定理 5.5 與引理 5.6，RQ2 的消融實驗必須滿足：

$$
\underbrace{\cdots\big[R_Y,R_Z\big]}_{\text{第 }0\text{ 層}}\ \longrightarrow\
\boxed{\ \text{去相位}\ }\ \longrightarrow\
\underbrace{\big[R_Y,R_Z\big]\big[\text{CX}\big]}_{\text{第 }1\text{ 層}}\ \longrightarrow\ \text{量測}
$$

也就是：**去相位之後必須還有含 $R_Y$ 的閘**。若之後只剩 CX（或只有 $R_Z$ 與 CX），差異恆為 0。

---

## 結論

1. 若 $U$ 是**么模仿塊矩陣**（置換 × 對角相位），則 $[\mathcal E,\mathcal U]=0$（定理 5.3）。**CNOT 是置換矩陣，故屬此類**（推論 5.4）。
2. **推論**：若去相位之後只接這一類閘，最終量測機率不變（定理 5.5）。**去相位接在電路尾端時，量測上完全隱形。**
3. $R_Y$ 不是么模仿塊矩陣（引理 5.6，由 **A Eq. 2.80** 的 Euler 恆等式），故與 $\mathcal E$ 不對易；最小反例的機率差是 $\sin\theta/2$，$\theta=\pi/4$ 時為 $0.353553$。
4. **$R_Z$ 是對角的，反而與 $\mathcal E$ 交換**——所以「有效」的關鍵是那層裡的 $R_Y$，不是 $R_Z$。
5. 因此去相位**必須插在含 $R_Y$ 的層之前**。

---

## 本地實測數據

以下數據來自本專案既有的實作與紀錄。**我另外用獨立的密度矩陣實作重跑了一次，結果逐位相同。**

### 5.1 數據來源與一處**出處勘誤**

> **引用紀律**：本節以**章節名稱＋關鍵字**定位，不使用行號。
> 理由：本專案的 README 與常數檔仍在編輯中，行號引用必然腐化
> （T5 初稿引用的 L39–40、L149 在本檔寫成後已被編輯位移）。
> 專案對**不再變動的 OCR 原文**才使用行號引用。

| 項目 | 位置（章節式） |
|---|---|
| 專案 README 的記載 | `projects/qbn-capacity-calibration/README.md` → **§一「RQ2：校準消融」→「實驗設計的關鍵陷阱」方塊**：記載去相位在尾端的機率差異為 $1.4\times10^{-17}$，且須插在含 $R_Y$ 的層之前（實測 $0.0502$） |
| **產生這些數字的程式** | **`dev/qbn5_encoding.py`** 的【4】節「去相位消融（Tucci 的 cl 算子）」——這是數字的**源頭** |
| 其他紀錄 | `docs/assets/diagrams/qbn-pipeline.architecture.json`、`docs/assets/diagrams/qbn-pipeline.html`（架構圖的結論卡） |
| 更正後的資產表位置 | `projects/qbn-capacity-calibration/README.md` → **§六「可用的既有資產」→「去相位陷阱的實測」列**（已加更正註記） |

> **⚠️ 已更正的指引錯誤（保留記錄，避免重蹈）。**
> 本專案早期的任務規格與 README 資產表，都把去相位實測數據指向
> `docs/_summary/00-專案規格常數.md` §6。
> 但實際查閱後確認：**§6 是「硬體環境事實（已實測）」**，內容是 Windows／WSL2／CUDA-Q 的
> 環境資訊與 §6.1／6.1.1／6.2 的 API 與位元序實測，**不含去相位數據**。
> （§6.2 的 $4.16\times10^{-17}$ 是 **bit-reversal 交叉驗證**的誤差，不是去相位誤差；
> §6.1.1 的 $1.34\times10^{-11}$ 是**參數平移**的誤差。兩者都與去相位無關，極易被誤引。）
> **正確出處為 README §一 與 `dev/qbn5_encoding.py` 的【4】節。** README 資產表已更正。

### 5.2 實際重跑 `dev/qbn5_encoding.py` 的輸出

指令：`uv run python dev/qbn5_encoding.py`（需 `PYTHONIOENCODING=utf-8`，否則 Windows 主控台會因 `32²` 的 `²` 字元丟 `UnicodeEncodeError`）

```
【4】去相位消融（Tucci 的 cl 算子）：全量子 vs 古典化
--------------------------------------------------------------------------
  (a) 直接量測的 32 維機率：
      全量子  vs 去相位 的最大絕對差 = 1.388e-17   ← 理論上必須是 0

  (b) 同調性敏感的觀測量（去相位應該殺掉 X、Y）：
      qubit        <X> 量子      <X> 去相位      <Y> 量子      <Y> 去相位      <Z> 量子      <Z> 去相位
      0          0.015939     0.000000   -0.017320     0.000000   -0.018223    -0.018223
      1          0.110048     0.000000   -0.035962     0.000000   -0.182428    -0.182428
      2          0.018469     0.000000    0.109024     0.000000   -0.078840    -0.078840
      3          0.042965     0.000000   -0.016215     0.000000    0.093343     0.093343
      4         -0.063438     0.000000   -0.020234     0.000000    0.035658     0.035658
      → 去相位後 |<X>|,|<Y>| 的最大殘值 = 0.000e+00

  (c) 純度與糾纏熵：
      純度 Tr[ρ²]：量子 1.0000000000 → 去相位 0.0636508580
      糾纏熵 S(qubits [0])：量子 0.99936070 bit → 去相位 0.99976043 bit
      糾纏熵 S(qubits [0, 1])：量子 1.75319378 bit → 去相位 1.97306934 bit
      糾纏熵 S(qubits [0, 1, 2])：量子 1.75687214 bit → 去相位 2.94103768 bit

  (d) 『去相位擺在哪裡』決定看不看得出來——三個設定的完整比較：
      (1) 去相位在【最末端】：最大機率差 = 1.388e-17   ← 必須是 0（量測只讀對角線）
      (2) 去相位在【中間】，之後只接 10 個 CX：最大機率差 = 1.388e-17   ← 仍是 0（CX 是基底置換，與去相位交換）
      (3) 去相位在【中間】，之後接完整第 2 層（RY+RZ+CX）：
          最大機率差 = 0.05023467   ← 這才是可觀測的消融效果
          前 5 大差異 = ['0.050235', '0.041307', '0.035387', '0.029310', '0.028844']
          全變分距離 (1/2)·Σ|Δp| = 0.19299447
          受影響的基底態個數 (|Δp|>1e-9) = 32 / 32
```

**三個設定的判讀**：

| 設定 | 量測值 | 對應的定理 | 結論 |
|---|---|---|---|
| (1) 最末端 | $1.388\times10^{-17}$ | 定理 5.5 取 $V=\mathbf 1$ | **隱形**。數值誤差等級。 |
| (2) 中間 + 只接 CX | $1.388\times10^{-17}$ | 定理 5.5 取 $V=$ CX 乘積（推論 5.4） | **仍然隱形**。 |
| (3) 中間 + 完整層 | $\mathbf{0.05023467}$ | 引理 5.6（含 $R_Y$） | **可觀測**。全部 32 個基底態都受影響。 |

**這就是「$1.4\times10^{-17}$ vs $0.0502$」的完整解釋**：前者是定理保證的零（只留下浮點誤差），後者是真實的物理效應。兩者相差 15 個數量級。

---

## 數值驗證

腳本：`theory/verify/t5_commutator_placement.py`（**25/25 通過**）
執行：`uv run python projects/qbn-capacity-calibration/theory/verify/t5_commutator_placement.py`

**實際輸出（節錄）**：

```
【1】么模仿塊矩陣的判準：哪些閘與去相位交換？
  單閘                        么模仿塊？       max|D U - U D| (n=2, 全基底)
  I                         True                        0.000e+00
  X                         True                        0.000e+00
  Z                         True                        0.000e+00
  S = diag(1,i)             True                        0.000e+00
  T = diag(1,e^{i pi/4})    True                        0.000e+00
  RZ(0.7)                   True                        0.000e+00
  H                         False                       5.000e-01
  RY(0.7)                   False                       3.221e-01
  RX(0.7) = H RZ H          False                       3.221e-01
  [PASS] RZ(0.7) 是么模仿塊且與去相位交換   max = 0.000e+00
  [PASS] H 非么模仿塊且與去相位**不**交換   max = 5.000e-01
  [PASS] RY(0.7) 非么模仿塊且與去相位**不**交換   max = 3.221e-01

【2】CNOT 與計算基底去相位交換（專案要求的核心命題）
  [PASS] CNOT(control=0, target=1) 與去相位交換   max|D U - U D| = 0.000e+00
  [PASS] CNOT(control=1, target=0) 與去相位交換   max|D U - U D| = 0.000e+00
  [PASS] CNOT(control=0, target=2) 與去相位交換   max|D U - U D| = 0.000e+00
  [PASS] CNOT(control=2, target=1) 與去相位交換   max|D U - U D| = 0.000e+00
  [PASS] CZ 與去相位交換   max = 0.000e+00
  [PASS] SWAP 與去相位交換   max = 0.000e+00

【3】明確實作的超算符交換子（n=2，16x16）
  [D, U_RY] 的 Frobenius 範數   = 1.288435   非零元素個數 = 16
  [D, U_CNOT] 的 Frobenius 範數 = 0.000e+00   非零元素個數 = 0
  [PASS] [D, U_CNOT] = 0（超算符層級）
  [PASS] [D, U_RY] != 0（超算符層級）   ||[D,U_RY]||_F = 1.288435

【4】最小反例：為什麼「先去相位」與「後去相位」不同？
  初態 |+>，θ = π/4，R_Y(θ) 與去相位的兩種順序：
    路徑 A（先 R_Y 再去相位）機率 = [0.146447, 0.853553]
    路徑 B（先去相位再 R_Y）機率 = [0.500000, 0.500000]
    最大差 = 0.353553
  解析：先去相位把 |+> 變成 I/2，而 I/2 在任何么正下都不變 → (1/2, 1/2)；
        先 R_Y 則振幅 = ((c-s)/√2, (s+c)/√2)，
        機率 = ((1-sinθ)/2, (1+sinθ)/2) = (0.146447, 0.853553)（與上列路徑 A 相符）。
  理論差 = |1/2 - (1-sinθ)/2| = sinθ/2 = 0.353553
  [PASS] 兩種順序的機率不同（順序有意義）   max|dp| = 0.353553
  [PASS] 路徑 A 與解析式 ((1∓sinθ)/2) 相符
  [PASS] 先去相位 → R_Y 的結果是 (1/2,1/2)（古典混態對 R_Y 不敏感）

【5】重現本地實測：5 qubit QBN 電路的三種去相位插入位置
  電路結構完全依照 dev/qbn5_encoding.py 的 qbn_layer（L178-192）：
    |0>^5 -- RY(θ_i) 角度編碼 --+-- [ RY(φ) RZ(λ) ] -- [ 環形 CX ] --+--
                                +---------- 重複 depth=2 次 ----------+
    第 0 層接 RING_STEP1，第 1 層接 RING_STEP2（兩條 5-cycle 交替）。
  輸入與權重取自 dev/qbn5_encoding.py::_demo_inputs（x5 固定、種子 42）。
  三種插入位置的 32 維機率最大絕對差（本檔獨立密度矩陣實作）：
    (1) 最末端（緊接量測）          = 0.000e+00
    (2) 中間，之後只接 10 個 CX     = 0.000e+00
    (3) 中間，之後接完整第 1 層     = 0.05023467
        前 5 大差異 = ['0.050235', '0.041307', '0.035387', '0.029310', '0.028844']
        全變分距離 (1/2)Σ|Δp| = 0.19299447
        受影響基底態 (|Δp|>1e-9) = 32 / 32
        純度：全量子 1.0000000000 → 去相位 0.0636508580
        去相位後 Σp_i² = 0.0636508580
        去相位後 <X_0>,<Y_0> 最大殘值 = 0.000e+00
  [PASS] (1) 尾端去相位：最大機率差 = 0（尾端去相位在量測上隱形）   0.000e+00   （專案實測 1.388e-17；README 記載 1.4e-17）
  [PASS] (2) 中間去相位 + 只接 CX：最大機率差 = 0（CX 與去相位交換）   0.000e+00   （專案實測 1.388e-17）
  [PASS] (3) 中間去相位 + 完整層：最大機率差為 O(0.01~0.1)（可觀測）   0.05023467   （專案實測 0.05023467；README 記載 0.0502）
  [PASS] (3) 全部 32 個基底態都受影響   32/32

【6】交換子的代數推論（為什麼么模仿塊閘『看不到』去相位）
  [PASS] 任意態、任意么模仿塊閘：兩條路徑的機率向量完全相同   max|dp| = 0.000e+00

總結
  通過 25 / 25 項
```

### 驗證對照表

| 推導結果 | 驗證方式 | 結果 |
|---|---|---|
| **定理 5.3**（么模仿塊交換） | 對所有基底 $\|i\rangle\langle j\|$ 逐一比較兩條路徑 | $0.000\times10^0$ ✓ |
| **推論 5.4**（CNOT 交換） | 4 組 (control, target) 全部檢查，另加 CZ、SWAP | 全 $0.000\times10^0$ ✓ |
| **引理 5.6**（$R_Y$ 不交換） | $H$、$R_Y(0.7)$、$R_X(0.7)$ | $5.000\times10^{-1}$、$3.221\times10^{-1}$、$3.221\times10^{-1}$ ✓ |
| $R_Z$ 交換（精確化） | $R_Z(0.7)$ | $0.000\times10^0$ ✓ |
| **超算符交換子 (5.9)** | $n=2$ 的 $16\times16$ 矩陣 | $\|[\mathcal E,\mathcal U_{\text{CNOT}}]\|_F=0$；$\|[\mathcal E,\mathcal U_{R_Y}]\|_F=1.288435$ ✓ |
| **最小反例 (5.6)** $\sin\theta/2$ | $P^{(A)}$、$P^{(B)}$ 與解析式 | $0.353553$ ✓ |
| **定理 5.5**（尾端/中間+CX 隱形） | 重跑專案電路設定 (1)(2) | $0.000\times10^0$ ✓ |
| **設定 (3) 可觀測** | 獨立密度矩陣實作，用專案示範輸入 | $\mathbf{0.05023467}$——**與 `dev/qbn5_encoding.py` 逐位相同** ✓ |
| 全變分距離 | $0.5\sum_i\|\Delta p_i\|$ | $0.19299447$，與專案輸出一致 ✓ |

**獨立性說明**：`t5_commutator_placement.py` **不使用** `dev/qbn5_encoding.py` 的通道實作，而是自己用 $32\times32$ 密度矩陣直接算（`dmtools.py`）。它與專案腳本給出**逐位相同**的 $0.05023467$ 與 $0.19299447$，這是最強的交叉驗證。

---

## 對本專題的意義

**這是最容易做錯的一步，而且做錯不會報錯——只會得到錯誤的結論。**

1. **對 RQ2 實驗設計的直接約束。** 去相位的位置**必須**滿足「之後還有含 $R_Y$ 的閘」。三種插法的正確預期是：

   | 插法 | 正確預期 | 若做錯會誤判 |
   |---|---|---|
   | 尾端 | 差異 $\approx0$（定理保證） | 「量子性沒貢獻」 |
   | 中間 + 只接 CX | 差異 $\approx0$（定理保證） | 「量子性沒貢獻」 |
   | 中間 + 之後有 $R_Y$ | 差異 $O(0.01\text{–}0.1)$ | — |

   **前兩列是「零的定理」，不是「實驗失敗」。** 報告時必須說明它們是**預期中的零**，否則會被誤讀成「去相位無效」。

2. **「量子性有貢獻」的可觀測定義。** 由定理 5.5，去相位只有在「之後還有非么模仿塊閘」時才可觀測。因此 RQ2 的假設 H2（去相位降低校準品質）**必須**在那個位置檢驗。實測為 $0.05023467$（32 維機率的最大變化），全變分距離 $0.19299447$，**32 個基底態全部受影響**。

3. **與 T4 的分工。** T4 給「去相位是什麼」（$\operatorname{diag}$）；T5 給「它什麼時候看得見」。兩者合起來才構成 RQ2 的完整理論基礎。

4. **對校準（ECE）的量化影響。** 去相位後純度雖從 1 掉到 $0.0636508580$，但**量測分布不變**（$P(i)=\rho_{ii}$ 不變）；只有當後續有 $R_Y$ 時分布才改變 $0.0502$。因此 RQ2 的 ECE 變化量必須在那個設定下測量。**附帶提醒（見 T6）**：4096 shots 的測量雜訊對 ECE 的貢獻只有 $\sim10^{-5}$ 量級，遠小於這個 $0.05$ 的效應——所以 RQ2 量到的 ECE 變化是**模型效應**，不是測量雜訊。

---

## 待核實事項

1. **通道／超算符的語言不在指定教材中。** 已用 `Kraus`、`channel`、`quantum operation`、`superoperator`、`POVM`、`completely positive`、`\bChoi\b` 搜尋 G、A、GS，**全部 0 命中**。本文件的**交換子工具**是 **A §5.3 Eq. 5.42** 的原文，論證手法照 **A Example 5.3.1（Eq. 5.45）**；但「么模仿塊矩陣」這個名詞與定理 5.3 是**本文件自行命名與推導**，不是教材原文。
2. **`\bChoi\b` 的搜尋**：初次以 `Choi` 搜尋得到 G 14 命中、A 88 命中，經查**全部是英文單字 "choice" 的子字串**，非 Choi 矩陣。加上詞界 `\bChoi\b` 後為 **0 命中**。此為關鍵字搜尋的陷阱，特別記錄。
3. **去相位實測數據的出處勘誤**：見「本地實測數據」5.1 節的 TODO 框。本專案早期的任務規格與 README 資產表，都把去相位實測數據指向 `docs/_summary/00-專案規格常數.md` **§六**，但**§六 實際內容是「硬體環境事實」，不含去相位數據**（其中 §6.2 的 $4.16\times10^{-17}$ 是 bit-reversal 交叉驗證誤差、§6.1.1 的 $1.34\times10^{-11}$ 是參數平移誤差，兩者都容易被誤引）。正確出處是 **README §一「RQ2」的「實驗設計的關鍵陷阱」方塊** 與**產生數字的 `dev/qbn5_encoding.py`【4】節**。README 資產表已更正。
4. **專案 README 的措辭精確化**：README 寫「含 $R_Y/R_Z$ 的層」。嚴格說，**$R_Z$ 單獨與去相位交換**（它是對角的，屬么模仿塊矩陣），有效的原因是那層裡的 **$R_Y$**。本文件在推導第 3 節加了精確化說明，並有數值證據（$R_Z$ 交換子 $=0$）。建議 README 改寫成「含 $R_Y$（或其他會混基底的閘，如 $R_X$、$H$）的層」。
5. **$1.4\times10^{-17}$ vs $1.388\times10^{-17}$**：README 記載 $1.4\times10^{-17}$（兩位有效數字），實跑 `dev/qbn5_encoding.py` 得到 $1.388\times10^{-17}$。兩者一致，本文件並列兩者以免混淆。**這個數字是浮點誤差，不是物理量**——定理 5.5 保證它「應該是 0」。
6. **`dev/qbn5_encoding.py` 在 Windows 需設定 UTF-8 編碼**：不設 `PYTHONIOENCODING=utf-8` 會在第 604 行的 `32²` 字元處丟 `UnicodeEncodeError`（主控台預設 gbk）。這是環境問題，不影響數學。
