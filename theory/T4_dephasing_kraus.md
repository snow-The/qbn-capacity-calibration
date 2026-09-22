# T4. 去相位算子的數學定義：Kraus 算符與非對角元歸零

> **代號 TH1**｜理論文件 T4｜對應研究問題 RQ2（校準消融）
> 教材代號：**G** = Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed.；
> **GS** = 同書 Instructor's Solution Manual；**A** = Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed.

---

## 問題陳述

RQ2 要把量子層「古典化」以測量量子性的邊際貢獻。所用的算子是**去相位（dephasing）**，Tucci 稱之為 `cl`（classicizing）。本文件要回答：

1. 去相位的 **Kraus 算符**是什麼？
2. 證明 $\mathcal E(\rho)=K_0\rho K_0^\dagger+K_1\rho K_1^\dagger$ **把非對角元歸零**；
3. 驗證**跡保性** $\operatorname{Tr}[\mathcal E(\rho)]=\operatorname{Tr}[\rho]$；
4. 這個通道作用在 $n$ 個 qubit 上時長什麼樣？

**先給結論**：對計算基底去相位，$n$ 個 qubit 的通道就是**取密度矩陣的對角部分**：

$$\mathcal E(\rho)=\operatorname{diag}(\rho)\qquad\text{即}\qquad \mathcal E(\rho)_{ij}=\rho_{ij}\,\delta_{ij}.$$

---

## 教科書基礎

| 書 | 章節 | 內容 | 本文件用在哪裡 |
|---|---|---|---|
| **G** | §12.3.1（L20203–20309） | **密度算符 $\hat\rho\equiv\|\Psi\rangle\langle\Psi\|$（Eq. 12.14）**；矩陣元 $\rho_{ij}=\langle e_i\|\hat\rho\|e_j\rangle$（Eq. 12.16）；性質 $\rho^2=\rho$（Eq. 12.17）、$\rho^\dagger=\rho$（Eq. 12.18）、$\operatorname{Tr}\rho=1$（Eq. 12.19）、$\langle A\rangle=\operatorname{Tr}(\rho A)$（Eq. 12.20） | 密度算符的定義與四條性質 |
| **G** | §12.3.2（L20311–20399） | **混合態 $\hat\rho\equiv\sum_k p_k\|\Psi_k\rangle\langle\Psi_k\|$（Eq. 12.28）**；$0\le p_k\le1$、$\sum_kp_k=1$（Eq. 12.30）；$\rho^\dagger=\rho$、$\operatorname{Tr}\rho=1$、$\langle A\rangle=\operatorname{Tr}(\rho A)$（Eq. 12.31–12.33）；**純態才冪等：$\rho^2\neq\rho$（Eq. 12.35）** | 混合態；「去相位把純態變成混合態」 |
| **G** | §12.3.2 Example 12.2（L20367–20383） | 電子各半機率為 spin up/down：$\rho=\operatorname{diag}(1/2,1/2)$，且 $\rho^2\neq\rho$ | **單 qubit 去相位的目標態** |
| **G** | §12.3.3（L20415–20431） | 子系統密度矩陣；糾纏態的單邊 $\rho=\operatorname{diag}(1/2,1/2)$（Eq. 12.40） | 去相位 vs 部分跡的關係 |
| **G** | §12.5（L20473–20493） | **L20493 定義 decoherence**：「宏觀系統受到環境不斷轟擊，subject to continuous "measurement" and the attendant collapse……這個現象叫 decoherence」 | 去相位的**物理動機** |
| **G** | §3.6.2 Eq. 3.91（L5437–5446） | **投影算符 $\hat P\equiv\|\alpha\rangle\langle\alpha\|$**；$\hat P\|\beta\rangle=(\langle\alpha\|\beta\rangle)\|\alpha\rangle$ | **Kraus 算符就是投影算符** |
| **G** | §3.6.2 Eq. 3.93/3.96（L5453–5477） | 完備性 $\sum_n\|e_n\rangle\langle e_n\|=1$、$\int\|e_z\rangle\langle e_z\|dz=1$ | **Kraus 完備性 $\sum_kK_k^\dagger K_k=1$ 的原型** |
| **G** | §3.2.1 Eq. 3.20（L4526–4532） | 伴隨 $\langle f\|\hat Qg\rangle=\langle\hat Q^\dagger f\|g\rangle$ | $K^\dagger$ |
| **G** | §3.3.1（L4613–4656） | Hermitian 算符的譜：實性、正交性、完備性 | $\rho$ 的譜分解 |
| **A** | §5.3 Eq. 5.47–5.49（L10973–10993） | 伴隨 Eq. 5.47；Hermitian Eq. 5.48；**么正 $U^\dagger=U^{-1}$ Eq. 5.49** | 算符代數 |
| **A** | §5.3 Basis Expansions（L11017–11113） | 算符由矩陣元素完全決定（L11061）；$A=\sum_{\nu\mu}\|\varphi_\nu\rangle a_{\nu\mu}\langle\varphi_\mu\|$（Eq. 5.57）；伴隨 $A^\dagger=\sum_{\nu\mu}\|\varphi_\nu\rangle a^*_{\mu\nu}\langle\varphi_\mu\|$（Eq. 5.60） | **$\rho$ 與 $K$ 的矩陣元素運算** |
| **A** | §5.4（L11195–11278） | 自伴算符；期望值 Eq. 5.61；$a_{\nu\mu}=a^*_{\mu\nu}$（Eq. 5.62）；**Example 5.4.3(c)（L11273–11277）：$AB$ 自伴 iff $A,B$ 交換** | $\rho$ 的 Hermitian 性 |
| **A** | §6.4（L13021–13256） | **譜分解（L13119）**；么正對角化；**Positive Definite and Singular Operators（L13187）** | 密度矩陣的半正定性與譜 |
| **A** | §2.2 Eq. 2.84（L4610–4616） | $\det(e^{\mathsf H})=e^{\operatorname{tr}\mathsf H}$（跡公式） | 跡的運算 |
| **GS** | **Problem 3.23（L4147–4153）** | **投影算符冪等 $P^2=P$ 的完整證明，並導出特徵值為 $\{0,1\}$** | **Kraus 算符 $K_0,K_1$ 的性質** |
| **GS** | Problem 3.24（L4155–4161） | $Q_{mn}=Q_{nm}^*$ | 密度矩陣的 Hermitian 性 |
| **GS** | Problem 3.26（L4177–4192） | 外積矩陣元素的具體計算（$A=\|\alpha\rangle\langle\beta\|$） | $K\rho K^\dagger$ 的逐項運算 |

### ⚠️ 指定教材**沒有**的東西

| 概念 | 搜尋關鍵字 | G | A | GS |
|---|---|---|---|---|
| Kraus 算符 | `Kraus` | **0** | **0** | **0** |
| 完全正性（complete positivity） | `completely positive` | **0** | **0** | **0** |
| Choi 矩陣 | `\bChoi\b`（詞界） | **0** | **0** | **0** |
| 量子通道 | `channel`、`quantum operation`、`superoperator` | **0** | **0** | — |
| POVM | `POVM` | **0** | **0** | — |

**因此本文件的做法**：Kraus 表示法本身**不是**從指定教材來的。但它的每一個積木都在教材裡：

- $K_b$ 是**投影算符** → **G Eq. 3.91** + **GS Problem 3.23**
- 完備性 $\sum_bK_b^\dagger K_b=1$ 是**完備性關係** → **G Eq. 3.93**
- 通道作用在 $\rho$ 上的**形式** $\sum_bK_b\rho K_b^\dagger$ 是**共軛變換** → **A Eq. 5.76**（$\mathsf A'=\mathsf U\mathsf A\mathsf U^\dagger$）加上混合態的**凸組合** → **G Eq. 12.28**
- 跡保性來自 $\operatorname{Tr}$ 的循環性 → **G Eq. 12.19**、**A §2.2 Eq. 2.84**

也就是說：**本文件把 Kraus 表示法「組裝」出來，並標明組裝的方法，而不是假稱教材裡有。** 外部引用見文末。

---

## 推導

### 1. 密度算符的回顧（G §12.3）

**純態**（**G Eq. 12.14**）：$\hat\rho=|\Psi\rangle\langle\Psi|$，性質（Eq. 12.17–12.20）

$$
\rho^2=\rho,\qquad \rho^\dagger=\rho,\qquad \operatorname{Tr}\rho=1,\qquad
\langle A\rangle=\operatorname{Tr}(\rho A). \tag{4.1}
$$

**混合態**（**G Eq. 12.28**）：$\hat\rho=\sum_kp_k|\Psi_k\rangle\langle\Psi_k|$，$p_k\ge0$、$\sum_kp_k=1$，性質（Eq. 12.31–12.33、12.35）

$$
\rho^\dagger=\rho,\qquad \operatorname{Tr}\rho=1,\qquad \langle A\rangle=\operatorname{Tr}(\rho A),
\qquad \rho^2\neq\rho\ (\text{非純態}). \tag{4.2}
$$

由 (4.1)/(4.2)，$\rho$ 是 Hermitian、半正定、跡 1 的算符（半正定性見 **A §6.4 L13187**）。在正交歸一基底 $\{|e_i\rangle\}$ 下（**G Eq. 12.15**）

$$
\rho_{ij}=\langle e_i|\hat\rho|e_j\rangle,\qquad
\rho_{ii}=P(e_i) \tag{4.3}
$$

（最後一等式由 Born 法則，見 T6）。**本文件後續所有「非對角元」都指 $\rho_{ij}$，$i\neq j$。**

### 2. 單 qubit 去相位的 Kraus 算符

對一個 qubit，取計算基底 $\{|0\rangle,|1\rangle\}$。定義

$$
\boxed{\ K_0=|0\rangle\langle0|=\begin{pmatrix}1&0\\0&0\end{pmatrix},
\qquad
K_1=|1\rangle\langle1|=\begin{pmatrix}0&0\\0&1\end{pmatrix}\ } \tag{4.4}
$$

**這是投影算符**（**G Eq. 3.91** 的 $\hat P=|\alpha\rangle\langle\alpha|$ 取 $|\alpha\rangle=|0\rangle,|1\rangle$）。

**性質 4.1（投影算符）** $K_b^\dagger=K_b$ 且 $K_b^2=K_b$，特徵值為 $\{0,1\}$。

*證明*：$K_0^\dagger=(|0\rangle\langle0|)^\dagger=|0\rangle\langle0|=K_0$（用 **G Eq. 3.20** 的伴隨定義，或 **A Eq. 5.60**）。
$K_0^2=|0\rangle\langle0|0\rangle\langle0|=|0\rangle\underbrace{\langle0|0\rangle}_{1}\langle0|=|0\rangle\langle0|=K_0$。
這與 **GS Problem 3.23（L4149–4153）** 的計算逐字相同：GS 用 $P^2|\beta\rangle=P|\beta\rangle$ 對任意 $|\beta\rangle$ 證明 $P^2=P$，再令 $P|\gamma\rangle=\lambda|\gamma\rangle$ 得 $\lambda^2=\lambda$，故特徵值為 $0,1$。$\square$

**性質 4.2（完備性）**

$$
K_0^\dagger K_0+K_1^\dagger K_1=K_0+K_1=|0\rangle\langle0|+|1\rangle\langle1|=\mathbf 1_2. \tag{4.5}
$$

*證明*：由性質 4.1，$K_b^\dagger K_b=K_b^2=K_b$。而 $|0\rangle\langle0|+|1\rangle\langle1|=\mathbf 1$ 正是**完備性關係**（**G Eq. 3.93**：$\sum_n|e_n\rangle\langle e_n|=1$，G 說這是「表達完備性最簡潔的方式」）。$\square$

**性質 4.3（正交）** $K_0K_1=|0\rangle\langle0|1\rangle\langle1|=0$。

### 3. 通道的定義與「非對角元歸零」

**定義 4.4（去相位通道）** 對密度算符 $\rho$ 定義

$$
\boxed{\ \mathcal E(\rho)=K_0\,\rho\,K_0^\dagger+K_1\,\rho\,K_1^\dagger\ } \tag{4.6}
$$

**這個形式的來源**：單一么正演化是 $\rho\mapsto U\rho U^\dagger$（**A Eq. 5.76** 的算符變換、**G §12.3.2** 的系綜影像）。當我們**不知道**實際發生的是 $K_0$ 還是 $K_1$（各以某機率），系綜的密度算符就是各支的**凸組合**——這正是 **G Eq. 12.28** 的 $\hat\rho=\sum_kp_k|\Psi_k\rangle\langle\Psi_k|$ 的算符版本。(4.6) 取 $K_b$ 等權重，下面會看到這對應「以等機率隨機施加 $Z$ 再平均」。

**定理 4.5（非對角元歸零）** 設 $\rho=\begin{pmatrix}a&c\\c^*&b\end{pmatrix}$（Hermitian），則

$$
\mathcal E(\rho)=\begin{pmatrix}a&0\\0&b\end{pmatrix}=\operatorname{diag}(\rho). \tag{4.7}
$$

*證明*：逐步計算，不跳步。

先算 $K_0\rho$：

$$
K_0\rho=|0\rangle\langle0|\,\rho
=\begin{pmatrix}1&0\\0&0\end{pmatrix}\begin{pmatrix}a&c\\c^*&b\end{pmatrix}
=\begin{pmatrix}a&c\\0&0\end{pmatrix}.
$$

再右乘 $K_0^\dagger=K_0$：

$$
K_0\rho K_0^\dagger
=\begin{pmatrix}a&c\\0&0\end{pmatrix}\begin{pmatrix}1&0\\0&0\end{pmatrix}
=\begin{pmatrix}a&0\\0&0\end{pmatrix}. \tag{4.8}
$$

同理

$$
K_1\rho=\begin{pmatrix}0&0\\0&1\end{pmatrix}\begin{pmatrix}a&c\\c^*&b\end{pmatrix}
=\begin{pmatrix}0&0\\c^*&b\end{pmatrix},
\qquad
K_1\rho K_1^\dagger=\begin{pmatrix}0&0\\c^*&b\end{pmatrix}\begin{pmatrix}0&0\\0&1\end{pmatrix}
=\begin{pmatrix}0&0\\0&b\end{pmatrix}. \tag{4.9}
$$

相加：

$$
\mathcal E(\rho)=\begin{pmatrix}a&0\\0&0\end{pmatrix}+\begin{pmatrix}0&0\\0&b\end{pmatrix}
=\begin{pmatrix}a&0\\0&b\end{pmatrix}.
$$

非對角元 $c,c^*$ 兩項都變成 0。$\square$

**等價的指標形式**：由 $K_b=|b\rangle\langle b|$，

$$
\mathcal E(\rho)=\sum_{b\in\{0,1\}}|b\rangle\langle b|\,\rho\,|b\rangle\langle b|
=\sum_b\underbrace{\langle b|\rho|b\rangle}_{=\rho_{bb}}|b\rangle\langle b|
=\sum_b\rho_{bb}|b\rangle\langle b|. \tag{4.10}
$$

故 $\mathcal E(\rho)$ 是**對角的**，且對角元就是原本的對角元。

**推論 4.6（遮罩形式與部分去相位）** 對 $n$ 個 qubit，去相位作用在 qubit 子集 $S$ 上時

$$
\big(\mathcal E_S(\rho)\big)_{ij}
=\rho_{ij}\prod_{q\in S}\delta_{\,b_q(i),\,b_q(j)}
=\rho_{ij}\prod_{q\in S}\frac{1+s_q(i)s_q(j)}{2}, \tag{4.11}
$$

其中 $b_q(i)$ 是基底索引 $i$ 的第 $q$ 個位元、$s_q(i)=(-1)^{b_q(i)}$。也就是「$i$ 與 $j$ 在 $S$ 上所有位元都相同時保留，否則歸零」。$S=$ 全部 qubit 時即 $\operatorname{diag}(\rho)$。

**推論 4.7（隨機 $Z$ 塗鴉表示）** 由 (4.11) 的 $\delta_{b_ib_j}=\frac12(1+s_is_j)$，

$$
\mathcal E_S(\rho)=\frac{1}{2^{|S|}}\sum_{\mathbf s\in\{\pm1\}^{|S|}}Z_{\mathbf s}\,\rho\,Z_{\mathbf s},
\qquad Z_{\mathbf s}=\prod_{q\in S}Z_q^{[s_q=-1]} . \tag{4.12}
$$

**這個形式很有用**：它說明去相位就是「以等機率隨機施加 $Z$，然後平均掉」。本文件在數值上驗證 (4.11) 與 (4.12) 給出同一個 $\rho$。

### 4. 跡保性

**定理 4.8** $\operatorname{Tr}[\mathcal E(\rho)]=\operatorname{Tr}[\rho]$。

*證明（兩條路，都寫出來）*：

**路徑一（用 (4.7)）**：跡只取對角元，$\operatorname{Tr}[\operatorname{diag}(\rho)]=\sum_i\rho_{ii}=\operatorname{Tr}[\rho]$。$\square$

**路徑二（用循環性，不假設 $\rho$ 的形式）**：$\operatorname{Tr}$ 有循環性 $\operatorname{Tr}(ABC)=\operatorname{Tr}(CAB)$（**A §2.2 "Transpose, Adjoint, Trace" L4218 一帶**給的性質；亦由 **A Eq. 2.84** 的跡運算支持）。故

$$
\operatorname{Tr}[K_b\rho K_b^\dagger]=\operatorname{Tr}[K_b^\dagger K_b\,\rho]
=\operatorname{Tr}[K_b\,\rho] \quad(\text{用性質 4.1}).
$$

於是

$$
\operatorname{Tr}[\mathcal E(\rho)]
=\sum_b\operatorname{Tr}[K_b\rho K_b^\dagger]
=\sum_b\operatorname{Tr}[K_b\rho]
=\operatorname{Tr}\Big[\Big(\underbrace{\sum_bK_b}_{=\,\mathbf 1}\Big)\rho\Big]
=\operatorname{Tr}[\rho]. \qquad\square
$$

**注意**：路徑二只用到**完備性** (4.5) 與**循環性**，完全不需要 $\rho$ 是對角的。**這正是 Kraus 表示法「跡保 $\iff$ $\sum_kK_k^\dagger K_k=\mathbf 1$」的一般定理在 (4.4) 這個特例上的體現。**

**推論 4.9** 跡保性使 $\mathcal E(\rho)$ 仍是合法密度算符（跡 1）。配合定理 4.5（對角）與 $\rho_{ii}\ge0$（$\rho$ 半正定），半正定性與 Hermitian 性也保持。

### 5. $n$ 個 qubit：張量積 Kraus 算符

對 $n$ 個 qubit，把每個 qubit 的通道**張量積**起來。由 (4.4)，指標 $\mathbf b=(b_0,\dots,b_{n-1})\in\{0,1\}^n$ 對應

$$
K_{\mathbf b}=K_{b_0}\otimes K_{b_1}\otimes\cdots\otimes K_{b_{n-1}}
=\big(|b_0\rangle\langle b_0|\big)\otimes\cdots\otimes\big(|b_{n-1}\rangle\langle b_{n-1}|\big)
=|\mathbf b\rangle\langle\mathbf b| . \tag{4.13}
$$

共 $2^n$ 個 Kraus 算符。完備性由 (4.5) 的張量積直接得到：

$$
\sum_{\mathbf b\in\{0,1\}^n}K_{\mathbf b}^\dagger K_{\mathbf b}
=\sum_{\mathbf b}|\mathbf b\rangle\langle\mathbf b|=\mathbf 1_{2^n}. \tag{4.14}
$$

通道

$$
\mathcal E(\rho)=\sum_{\mathbf b\in\{0,1\}^n}|\mathbf b\rangle\langle\mathbf b|\,\rho\,|\mathbf b\rangle\langle\mathbf b|
=\sum_{\mathbf b}\rho_{\mathbf b\mathbf b}\,|\mathbf b\rangle\langle\mathbf b|
=\operatorname{diag}(\rho), \tag{4.15}
$$

**與單 qubit 完全同構：$n$ 個 qubit 的計算基底去相位就是把 $\rho$ 的非對角元全部歸零。** 本專案 $n=5$ 時有 $2^5=32$ 個 Kraus 算符。

### 6. 去相位做了什麼、沒做什麼

**做了**：
- 殺掉所有非對角元（同調性，coherence）。
- 純態 $\to$ 混合態：純度 $\operatorname{Tr}[\rho^2]$ 從 1 下降（**G Eq. 12.35** 的判準）。
- $\langle X\rangle,\langle Y\rangle\to0$（它們完全來自非對角元）。
- **不可逆**：$\mathcal E\circ\mathcal E=\mathcal E$（冪等），無法從 $\operatorname{diag}(\rho)$ 還原 $\rho$。

**沒做**：
- **不改變計算基底的機率**：$P(i)=\rho_{ii}$（**G Eq. 12.16**、(4.3)）不受影響。**這是 T5 與 RQ2 實驗設計的全部關鍵。**
- 不改變 $\langle Z\rangle$（$Z$ 是對角的）。
- **不讓量子態變成古典機率向量**——它仍然是密度矩陣，只是對角的。

**物理動機**：**G §12.5 L20493** 對 decoherence 的描述——環境不斷「測量」系統、造成坍縮，使「古典」態在統計上被偏好。去相位就是這個過程的最簡模型（去掉環境，只留效果）。

---

## 結論

對計算基底，單 qubit 去相位的 Kraus 算符是 $K_0=|0\rangle\langle0|$、$K_1=|1\rangle\langle1|$（**投影算符**；性質見 **GS Problem 3.23**），滿足完備性 $\sum_bK_b^\dagger K_b=\mathbf 1$（**G Eq. 3.93** 的原型）。通道

$$\mathcal E(\rho)=K_0\rho K_0^\dagger+K_1\rho K_1^\dagger=\operatorname{diag}(\rho)$$

**恰好把非對角元歸零、保留對角元**，且**保跡**（定理 4.8，兩條獨立證明）。對 $n$ 個 qubit，Kraus 算符是 $2^n$ 個張量積投影算符 $|\mathbf b\rangle\langle\mathbf b|$，通道仍是 $\operatorname{diag}(\rho)$。

---

## 對本專題的意義

**這是 RQ2 消融實驗所施加的算子。** 四個具體後果：

1. **「古典化」有精確的操作定義。** 去相位不是「換一個模型」，而是對同一個 $\rho$ 施加 (4.15)。因此「全量子 vs 古典化」是一個**唯一變因**的乾淨消融：不換模型、不換資料、不換參數（呼應 Tucci 的論證）。
2. **⚠️ 尾端去相位在量測上隱形（最重要的實作警告）。** 由 (4.15)，去相位後 $P(i)=\rho_{ii}$ 與去相位前**完全相同**。因此若把去相位接在電路最尾端（緊接量測），32 維量測機率**一字不改**，實驗會誤判「量子性沒有貢獻」。本專案實測值 $1.4\times10^{-17}$（見 T5 與 README）正是這個定理的數值體現。
3. **要量到效果，必須讓去相位之後還有「會混基底」的閘。** 這是 T5 的主題。
4. **對校準的意義（RQ2 的核心論證）**：去相位把 $\rho$ 變成 $\operatorname{diag}(\rho)$，也就是**丟掉同調性**。而校準（calibration）關心的是預測機率與真實頻率的一致程度。若電路後續仍有 $R_Y/R_Z$ 型閘，去相位會改變最終機率分布（T5 實測 $0.0502$），進而改變 ECE。**因此去相位確實可以傷害校準——但只有在插對位置時。**

---

## 數值驗證

腳本：`theory/verify/t4_kraus_dephasing.py`（**27/27 通過**）
執行：`uv run python projects/qbn-capacity-calibration/theory/verify/t4_kraus_dephasing.py`

**實際輸出（節錄）**：

```
【1】Kraus 算符的定義與完備性（單 qubit）
  K0 = |0><0| =
    [[1. 0.]
     [0. 0.]]
  K1 = |1><1| =
    [[0. 0.]
     [0. 1.]]
  [PASS] 完備性 sum_k K_k^dag K_k = I   max|sum - I| = 0.000e+00
  [PASS] K_k 是投影子且 Hermitian（K^2=K, K^dag=K）
  [PASS] K0 K1 = 0（Kraus 算符互相正交）

【2】|+> 態：非對角元歸零
  去相位前 rho =
    [[0.5+0.j 0.5+0.j]
     [0.5+0.j 0.5+0.j]]
  去相位後 rho =
    [[0.5+0.j 0. +0.j]
     [0. +0.j 0.5+0.j]]
  [PASS] 非對角元 rho_01: 0.5 -> 0   rho_01: 0.500000+0.000000j -> 0.000e+00+0.000e+00j
  [PASS] 對角元不變（rho_00 = rho_11 = 0.5）   diag = [0.5 0.5]
  [PASS] 跡保性 Tr[E(rho)] = Tr[rho] = 1   Tr = 1.000000000000000
  [PASS] Hermitian 保持
  [PASS] 正性（最小特徵值 >= 0）   lambda_min = 5.000e-01
  [PASS] 純度下降 Tr[rho^2]: 1 -> 0.5   Tr[rho^2] = 1.000000 -> 0.500000
  [PASS] 冪等性 D(D(rho)) = D(rho)   max|D^2 - D| = 0.000e+00

【3】一般態與任意 qubit 數：n qubit 的張量積 Kraus 算符
  [PASS] 一般態：非對角元全歸零   max|offdiag| = 0.000e+00
  [PASS] n=5：2^n = 32 個 Kraus 算符的完備性   max|sum - I| = 0.000e+00
  [PASS] K_b 等於單 qubit Kraus 的張量積（big-endian 約定）   b = 10110

【4】三種等價形式的互相驗證（遮罩 / 投影子求和 / 隨機 Z 塗鴉）
  [PASS] 遮罩形式 == 投影子求和形式   max|diff| = 0.000e+00
  [PASS] 遮罩形式 == 隨機 Z 塗鴉形式   max|diff| = 1.110e-16
  [PASS] 三者都等於 diag(rho)（去相位的閉式解）   max|D(rho) - diag(rho)| = 0.000e+00
  [PASS] 部分去相位 S=[0]：兩形式一致   max|diff| = 0.000e+00
  [PASS] 部分去相位 S=[0, 2]：兩形式一致   max|diff| = 0.000e+00
  [PASS] 部分去相位 S=[0, 1, 2, 3]：兩形式一致   max|diff| = 0.000e+00

【5】完全正性（Choi 矩陣半正定）
  [PASS] Choi 矩陣 Hermitian
  [PASS] Choi 矩陣半正定（=> 通道完全正）   lambda_min(J) = 0.000e+00
  [PASS] 對照組：轉置映射 T 的 Choi 矩陣有負特徵值（正但非完全正）   lambda_min(J_T) = -1.000e+00

【6】計算基底機率不變：P(i) = Tr[M_i rho] = rho_ii
  [PASS] 去相位前後 32 維 Born 機率完全相同   max|dp| = 0.000e+00
  <X_0>: -0.026754 -> +0.000e+00
  <Y_0>: -0.194131 -> +0.000e+00
  <Z_0>: +0.018062 -> +0.018062
  [PASS] <X>,<Y> 歸零（同調性被抹除）
  [PASS] <Z> 完全不變（Z 是對角的）

【7】與 dev/qbn_sim.py 態向量路徑交叉驗證（5 qubit QBN 電路）
  [PASS] 態向量路徑（qbn_sim）vs 密度矩陣路徑（dmtools）機率一致   max|dp| = 2.776e-17
  [PASS] 5 qubit 電路：去相位後 Born 機率不變（尾端去相位隱形）   max|dp| = 0.000e+00
  純度 Tr[rho^2]: 1.000000000000 -> 0.124403595787
  糾纏熵 S(qubit 0): 0.82663319 bit -> 0.98681319 bit
  糾纏熵 S(qubits 0,1): 1.08699262 bit -> 1.97536710 bit

總結
  通過 27 / 27 項
```

**驗證對照表**：

| 推導結果 | 驗證方式 | 結果 |
|---|---|---|
| 性質 4.1 $K_b^2=K_b$、$K_b^\dagger=K_b$、特徵值 $\{0,1\}$ | 直接矩陣運算 | ✓（與 **GS Problem 3.23** 一致） |
| 性質 4.2 完備性 (4.5) | $K_0^\dagger K_0+K_1^\dagger K_1$ vs $\mathbf 1$ | $0.000\times10^0$ ✓ |
| **定理 4.5 非對角元歸零 (4.7)** | $|+\rangle$ 態的 $\rho_{01}:0.5\to0$ | ✓ |
| 對角元不變 | $\operatorname{diag}$ 比較 | ✓ |
| **定理 4.8 跡保性** | $\operatorname{Tr}[\mathcal E(\rho)]$ | $1.000000000000000$ ✓ |
| 冪等（不可逆） | $\mathcal E^2=\mathcal E$ | $0$ ✓ |
| (4.13)/(4.14) $n=5$ 的 32 個 Kraus 算符 | 完備性 + 張量積結構（$b=10110$） | ✓ |
| (4.11) 遮罩 vs (4.12) 隨機 $Z$ 塗鴉 | 兩獨立實作比較 | $1.110\times10^{-16}$ ✓ |
| (4.15) 閉式解 $\mathcal E(\rho)=\operatorname{diag}(\rho)$ | 三形式全部比對 | $0$ ✓ |
| 部分去相位（(4.11) 的 $\prod_{q\in S}$） | $S=[0],[0,2],[0,1,2,3]$ | 全 ✓ |
| 保跡、保 Hermitian、保正性 | 特徵值與 Hermitian 檢查 | $\lambda_{\min}=0.5\ge0$ ✓ |
| **完全正性**（外部性質，見待核實） | Choi 矩陣半正定；對照：轉置映射 $\lambda_{\min}=-1<0$ | ✓ |
| 分布不變（T5 的關鍵前提） | 32 維 Born 機率 | $0.000\times10^0$ ✓ |
| $\langle X\rangle,\langle Y\rangle\to0$、$\langle Z\rangle$ 不變 | Pauli 期望值 | $-0.026754\to0$、$-0.194131\to0$、$0.018062$ 不變 ✓ |
| **與 `dev/qbn_sim.py` 交叉驗證** | 態向量路徑 vs 本檔密度矩陣路徑 | $2.776\times10^{-17}$ ✓ |

**一個必須誠實指出的細節**：去相位**不會降低**單邊約化熵（實測 $\rho_0$ 的熵 $0.8266\to0.9868$、$\rho_{01}$ 的 $1.0870\to1.9754$，都是**上升**）。原因是：約化熵不是「同調性的量」；$\rho$ 的非對角元承載的是「純態整體的糾纏」，而古典混態同樣可以有大的邊際熵。**去相位殺掉的是同調性，判準應該用 $\langle X\rangle,\langle Y\rangle\to0$ 與純度下降，不是用約化熵。** 我在文件裡明講這一點，是為了避免後續章節誤用熵當作「去相位有沒有作用」的判準。

---

## 待核實事項

1. **Kraus 表示法本身不在指定教材中。** 已用關鍵字 `Kraus`、`channel`、`quantum operation`、`superoperator`、`POVM`、`completely positive` 搜尋 G、A、GS，**全部 0 命中**（`\bChoi\b` 亦然）。本文件的作法是**用教材的積木組裝**（投影算符 G Eq. 3.91、完備性 G Eq. 3.93、混合態凸組合 G Eq. 12.28、共軛變換 A Eq. 5.76、跡的循環性），並在推導第 3 節明講「這個形式的來源」。**若要正式引用 Kraus 表示法，應引 Nielsen & Chuang, *Quantum Computation and Quantum Information*, §8.2；本文件不把它掛在 G/A/GS 名下。**
2. **完全正性（complete positivity）**：`completely positive` 在三本書 0 命中。本文件的數值驗證用 Choi 矩陣半正定性來檢驗它（並用轉置映射作對照組，$\lambda_{\min}=-1$，示範「正但非完全正」）。同樣應外引 Nielsen & Chuang §8.2.3。
3. **「以等機率隨機施加 $Z$ 再平均」的塗鴉（twirling）解釋 (4.12)**：不在指定教材中。本文件只把它當作 (4.11) 的一個**推論**並用數值驗證其等價，未引用外部來源。
4. **推導第 3 節「單一么正演化是 $\rho\mapsto U\rho U^\dagger$」**：**A Eq. 5.76** 是算符的基底變換，與「時間演化」是同一種共軛變換（**G §6.8.1 Eq. 6.72** 的 Heisenberg 表象也是同一形式）。本文件把這個連結寫明，但注意 A Eq. 5.76 原本的語境是**基底變換**，不是通道。
