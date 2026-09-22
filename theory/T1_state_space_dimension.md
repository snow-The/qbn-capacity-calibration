# T1. 為什麼 $n$ 個 qubit 的狀態空間是 $2^n$ 維？

> **代號 TH1**｜理論文件 T1｜對應研究問題 RQ1（容量斷崖）
> 教材代號：**G** = Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed.；
> **GS** = 同書 Instructor's Solution Manual；**A** = Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed.

---

## 問題陳述

本研究用 5 個 qubit 當輸出層。專案常數檔記載它的希爾伯特空間是

$$(\mathbb C^2)^{\otimes 5}\cong\mathbb C^{32},\qquad \text{維度}=32 .$$

本文件要回答的是：**這個 $2^n$ 從哪裡來？** 具體要澄清三件事：

1. 單一 qubit 的狀態空間是 2 維複向量空間，**如何**推廣到 $n$ 個 qubit？
2. 為什麼合併兩個量子系統用的是**張量積（tensor product，又稱直積）**，而不是**直和（direct sum）**？也就是說，為什麼是 $2^n$ 而不是 $2n$？
3. 這個「指數」與「多項式」的落差，在物理上是什麼意思？

第 3 點是 RQ1 的一半來源：狀態空間的大小是**指數**，但我們能控制的參數只有**多項式**個——這個落差是 T2 的主角，而本文件負責把「指數」那一半推導清楚。

---

## 教科書基礎

| 書 | 章節 | 內容 | 本文件用在哪裡 |
|---|---|---|---|
| **G** | §3.1（L4368–4470） | 希爾伯特空間的定義、內積 Eq. 3.6、正交歸一 Eq. 3.10、完備性 Eq. 3.11 | 狀態空間是複向量空間這件事 |
| **G** | §3.6.1（L5230–5416） | 基底與分量；**L5355 明確說「只有有限個 $N$ 個線性獨立狀態的系統，$\|S(t)\rangle$ 住在 $N$ 維向量空間」**；Eq. 3.77–3.86 | 有限維 $N$ 維空間的框架 |
| **G** | §3.6.2（L5417–5530） | Dirac 記號、投影算符 Eq. 3.91、完備性 $\sum_n\|e_n\rangle\langle e_n\|=1$ Eq. 3.93 | 張量積基底與單位算符 |
| **G** | §4.4（L7713–9058） | 自旋；$\|0\rangle,\|1\rangle$ 為 spin up/down 的基底（Eq. 4.149 一帶） | 單一 qubit 的 2 維空間 |
| **G** | §4.4.3（見 L8132、L8238） | 兩粒子的**合成態** $\|s_1s_2m_1m_2\rangle$ 與 Eq. 4.175／4.176 的單重態、三重態 | 合成系統的基底是「乘積」 |
| **G** | §5.1（L9769–9846） | **兩粒子波函數 $\Psi(\mathbf r_1,\mathbf r_2,t)$ 是兩個座標的函數** Eq. 5.1；乘積解 Eq. 5.9／5.11；**L9845：糾纏態的定義「不能寫成單粒子態的乘積」** | 複合系統的公設與糾纏 |
| **G** | §5.1.3（L10067–10093） | 完整狀態是位置部分**乘上**自旋部分 $\psi(\mathbf r)\chi$，兩粒子為 $\psi(\mathbf r_1,\mathbf r_2)\chi(1,2)$ Eq. 5.27–5.28 | 「自由度合併 = 相乘」 |
| **G** | §12.1 Problem 12.1（L19985–19997） | **證明** $\alpha\|\phi_a(1)\rangle\|\phi_b(2)\rangle+\beta\|\phi_b(1)\rangle\|\phi_a(2)\rangle$ 不能寫成 $\|\psi_r(1)\rangle\|\psi_s(2)\rangle$ | 糾纏態存在的證明 |
| **G** | §12.3.3（L20415–20431） | Subsystem density matrix（子系統密度矩陣）；單重態的電子只看正子時 $\rho=\mathrm{diag}(1/2,1/2)$ Eq. 12.40 | 從複合系統取邊際 |
| **G** | §A.1–A.3（L20505–20976） | 向量空間公設、內積、矩陣 | 向量空間的公理化背景 |
| **A** | §5.1（L10063–10412） | **Hilbert Space 的完整公設清單（L10171–10195）**；完備性與基底展開 L10185；Schwarz 不等式 Eq. 5.8；正交展式 Eq. 5.12；**Example 5.1.4 SPIN SPACE（L10309–10335）：4 個 spin-½ 粒子的自旋空間由 16 個單項式張開** | 希爾伯特空間公設；$2^n$ 的具體例子 |
| **A** | §4.1 Direct Product（L8653–8680） | **張量（直積）的定義**：把兩個張量的分量逐分量相乘，得到秩相加的新張量；Eq. 4.17 是兩個 rank-1 向量直積成 rank-2 張量 | 直積的數學定義 |
| **A** | §17.5 Direct Products（L34874–34960） | **L34878：「多粒子基底由『從每個單粒子基底各取一員』的所有乘積構成，這就叫直積」**；$K=K_1\otimes K_2$；Eq. 17.19（$2\times2\to4$ 個基底成員）；**L34920：$e\otimes e=A_1\oplus A_2\oplus E$（直積分解成直和）** | 直積 vs 直和的分野 |
| **GS** | Problem 3.25（L4163–4175） | 二能階系統 $H=\epsilon(\|1\rangle\langle1\|-\|2\rangle\langle2\|+\|1\rangle\langle2\|+\|2\rangle\langle1\|)$，$E=\pm\sqrt2\epsilon$ | 2 維空間的完整 worked example |
| **GS** | Problem 3.26（L4177–4192） | 3 維空間的內積與外積矩陣元素計算 | 有限維空間的具體運算 |
| **GS** | Problem 5.1（L7545–7577） | 兩粒子問題分離成 $\psi=\psi_r(\mathbf r)\psi_R(\mathbf R)$ | 複合系統「相乘」的 worked example |

---

## 推導

### 1. 單一 qubit：2 維複向量空間

由 **G §4.4**，電子的自旋狀態由二分量旋量（spinor）描述。取 $\hat S_z$ 的兩個本徵態為基底：

$$
|0\rangle\equiv|\uparrow\rangle=\begin{pmatrix}1\\0\end{pmatrix},\qquad
|1\rangle\equiv|\downarrow\rangle=\begin{pmatrix}0\\1\end{pmatrix},
$$

則任意自旋態是它們的**複**線性組合

$$
|\psi\rangle=a|0\rangle+b|1\rangle=\begin{pmatrix}a\\b\end{pmatrix},
\qquad a,b\in\mathbb C .
$$

由 **G §3.1 Eq. 3.10** 的歸一化條件（也在 **A §5.1 L10191**：$\langle f|f\rangle\ge0$ 且 $\|f\|=\langle f|f\rangle^{1/2}$）：

$$
\langle\psi|\psi\rangle=|a|^2+|b|^2=1 .
$$

$a,b$ 是兩個複數，但歸一化把它們限制在三維實球面（Bloch 球面）上。**狀態空間本身是 2 維複向量空間**：

$$
\mathcal H_1=\mathbb C^2,\qquad \dim_{\mathbb C}\mathcal H_1=2 .
$$

這裡的「維度」是**複**維度，這一點在 T2 會再回來（因為么正群的維度是**實**維度，兩者差一倍）。

### 2. 複合系統：為什麼是「相乘」而不是「相加」

這一步是整個推導的關鍵，而**教科書給的是公設**，不是定理。我們必須把它講清楚。

**第一步：從兩粒子的波函數看出來（G §5.1）。**
G 在 §5.1 開頭直接寫下兩粒子系統的狀態是

$$
\Psi(\mathbf r_1,\mathbf r_2,t) \tag{G Eq. 5.1}
$$

——**兩個座標的函數**。這不是「粒子 1 的函數加上粒子 2 的函數」，而是「同時依賴兩者」。G 接著寫下統計詮釋（Eq. 5.4）：

$$
|\Psi(\mathbf r_1,\mathbf r_2,t)|^2\,d^3\mathbf r_1\,d^3\mathbf r_2
$$

是「在 $d^3\mathbf r_1$ 找到粒子 1 **且**在 $d^3\mathbf r_2$ 找到粒子 2」的機率。注意「**且**」——這是聯合分布，對應的是乘積結構。

**第二步：無交互作用時的乘積解（G Eq. 5.9、5.11）。**
當 $V(\mathbf r_1,\mathbf r_2)=V_1(\mathbf r_1)+V_2(\mathbf r_2)$ 時 G 得到分離變數解

$$
\psi(\mathbf r_1,\mathbf r_2)=\psi_a(\mathbf r_1)\,\psi_b(\mathbf r_2), \tag{G Eq. 5.9}
$$

$$
\Psi(\mathbf r_1,\mathbf r_2,t)=\Psi_a(\mathbf r_1,t)\,\Psi_b(\mathbf r_2,t), \tag{G Eq. 5.11}
$$

且 $E=E_a+E_b$。**注意能量是「相加」而波函數是「相乘」**——這正是直和與直積的分野：能量（可觀測量的譜）走直和，狀態（向量）走直積。這個觀察值得畫線。

**第三步：一般解是乘積的線性組合，且這個空間的維度是乘積。**
G 立刻指出（L9839）：

> "But any linear combination of such solutions will still satisfy the (time-dependent) Schrödinger equation—for instance
> $$\Psi=\tfrac35\Psi_a(\mathbf r_1,t)\Psi_b(\mathbf r_2,t)+\tfrac45\Psi_c(\mathbf r_1,t)\Psi_d(\mathbf r_2,t)$$ (Eq. 5.12)"

於是複合系統的狀態空間由**所有** $\psi_a(\mathbf r_1)\psi_b(\mathbf r_2)$ 這種乘積張開。

**第四步：維度計數（本文件的主定理）。**

設單一系統的希爾伯特空間 $\mathcal H$ 有正交歸一基底 $\{|e_i\rangle\}_{i=1}^{d}$（對 qubit，$d=2$，基底是 $\{|0\rangle,|1\rangle\}$）。定義 $n$ 個系統的複合空間 $\mathcal H^{\otimes n}$ 為由下列 $d^n$ 個向量所張開的空間：

$$
|e_{i_1}\rangle\otimes|e_{i_2}\rangle\otimes\cdots\otimes|e_{i_n}\rangle,
\qquad i_1,\dots,i_n\in\{1,\dots,d\} . \tag{1.1}
$$

**引理 1.1（正交歸一性）** 由內積的張量積定義 $\langle u\otimes v|u'\otimes v'\rangle=\langle u|u'\rangle\langle v|v'\rangle$（這與 **G §3.2 Eq. 3.2** 的內積定義一致：分量逐項相乘後相加；亦見 **A §5.1 L10189–10195** 的純量積公設），這些向量滿足

$$
\langle e_{i_1}\cdots e_{i_n}|e_{j_1}\cdots e_{j_n}\rangle
=\prod_{k=1}^{n}\langle e_{i_k}|e_{j_k}\rangle
=\prod_{k=1}^{n}\delta_{i_k j_k}
=\delta_{i_1 j_1}\cdots\delta_{i_n j_n}. \tag{1.2}
$$

因此它們兩兩正交且歸一。

**引理 1.2（線性獨立）** 若 $\sum_{i_1\cdots i_n}c_{i_1\cdots i_n}|e_{i_1}\cdots e_{i_n}\rangle=0$，用 $\langle e_{j_1}\cdots e_{j_n}|$ 由左作用並用 (1.2)，得 $c_{j_1\cdots j_n}=0$ 對所有指標成立。故 (1.1) 的 $d^n$ 個向量線性獨立。

**引理 1.3（張開整個複合空間）** 這是**公設**（**A §17.5 L34878** 的說法：「多粒子基底由從每個單粒子基底各取一員的所有乘積構成」；**G §5.1** 的 Eq. 5.11–5.12 是同一件事的波函數版本）。我們採納它：$\mathcal H^{\otimes n}$ 由 (1.1) 張開。

**定理 1.4** $\dim_{\mathbb C}\mathcal H^{\otimes n}=d^{\,n}$。

*證明*：由引理 1.2 與 1.3，(1.1) 是一組有 $d^n$ 個元素的基底。任何基底的元素個數就是維度，故維度為 $d^n$。$\square$

（也可用歸納法：$\dim(\mathcal H^{\otimes n})=\dim(\mathcal H^{\otimes(n-1)})\cdot\dim\mathcal H$。）

**推論 1.5（本專案）** $d=2$（qubit），故

$$
\dim_{\mathbb C}(\mathbb C^2)^{\otimes n}=2^{\,n},
\qquad
\boxed{\ \dim_{\mathbb C}(\mathbb C^2)^{\otimes 5}=2^5=32\ }
$$

基底就是全部 32 個 5 位元字串 $\{|b_0b_1b_2b_3b_4\rangle\}$。任意狀態寫成

$$
|\psi\rangle=\sum_{b\in\{0,1\}^5}\alpha_b\,|b\rangle,
\qquad \sum_b|\alpha_b|^2=1,\quad \alpha_b\in\mathbb C . \tag{1.3}
$$

**A §5.1 的 Example 5.1.4（L10309）就是同一個計算的具體版本**：4 個 spin-½ 粒子的自旋空間由 $\alpha\alpha\alpha\alpha$ 型單項式張開，共 $2^4=16$ 個，課文用它示範正交化與展開。

### 3. 為什麼不是直和？——$2^n$ vs $2n$

**直和**的定義是形式配對 $|u\rangle\oplus|v\rangle$，維度**相加**：

$$
\dim(\mathcal H_1\oplus\mathcal H_2)=\dim\mathcal H_1+\dim\mathcal H_2 .
$$

若複合系統用直和，$n$ 個 qubit 就只有 $2n$ 維。兩者的差別：

| $n$ | 直積 $2^n$ | 直和 $2n$ | 比值 |
|---|---|---|---|
| 1 | 2 | 2 | 1 |
| 2 | 4 | 4 | 1 |
| 3 | 8 | 6 | 1.33 |
| 5 | **32** | **10** | 3.2 |
| 10 | 1024 | 20 | 51.2 |
| 50 | $1.13\times10^{15}$ | 100 | $1.13\times10^{13}$ |

**$2^n=2n$ 只在 $n=1,2$ 成立**——這正是 $n=2$ 容易誤導人的地方。從 $n=3$ 起兩者就分道揚鑣。

**物理上為什麼必須是直積？** 有兩個獨立論證：

**(a) 直和無法表達相關性（correlation）。**
直和的向量是 $|u\rangle\oplus|v\rangle$，它承載的資訊是「$u$ 這一塊」與「$v$ 這一塊」，兩塊之間**沒有聯合指標**。但量子力學要求存在**聯合**觀測量（例如 $\hat S_z^{(1)}\hat S_z^{(2)}$）。**G Eq. 5.4** 的 Born 機率 $|\Psi(\mathbf r_1,\mathbf r_2)|^2$ 本質上是**聯合**分布；在直和上無法定義聯合指標的函數。只有直積的係數 $\alpha_{b_1b_2}$（一個 $2\times2$ 的係數矩陣）才能表達「兩者的關聯」。

**(b) 直積的**分解**才用直和——兩者角色不同。**
這是最容易混淆的一點，而 **A §17.5 把它講得很清楚**（L34878–34920）：

- 複合系統的**基底**由直積構成（L34878 的定義），維度相乘。
- 但這個直積**表示**可能是可約的，而**可約的分解**才寫成直和。A 的 Example 17.5.2 給了具體數字：兩個 $E$ 對稱性的粒子，各有 2 維基底 $\varphi_a,\varphi_b$，乘積基底有 **4** 個成員

  $$\Phi_{aa}=\varphi_a(1)\varphi_a(2),\ \Phi_{ab},\ \Phi_{ba},\ \Phi_{bb}, \tag{A Eq. 17.19}$$

  而 A 算出

  $$e\otimes e=A_1\oplus A_2\oplus E,$$

  維度 $1+1+2=4$ ✓。**直積在前（$2\times2=4$），直和在後（$4=1+1+2$）。** 把這個順序搞反，就會得到「$2n$」的錯誤結論。

### 4. 糾纏：直積結構的直接後果

複合空間是直積，因此「每個粒子各自有明確狀態」不再是普遍真理。**G §5.1 L9845** 給了定義：

> "An entangled state is one that cannot be written as a product of single-particle states."

**G Problem 12.1（L19985）** 進一步證明：只要 $\alpha,\beta\neq0$，

$$
\alpha|\phi_a(1)\rangle|\phi_b(2)\rangle+\beta|\phi_b(1)\rangle|\phi_a(2)\rangle
\ \neq\ |\psi_r(1)\rangle|\psi_s(2)\rangle
\quad\text{對任何單粒子態} .
$$

我們把它寫成可計算的形式（G 的提示是「把 $|\psi_r\rangle,|\psi_s\rangle$ 展開成 $|\phi_a\rangle,|\phi_b\rangle$ 的線性組合」）。設

$$
|\psi_r\rangle=x_0|\phi_a\rangle+x_1|\phi_b\rangle,\qquad
|\psi_s\rangle=y_0|\phi_a\rangle+y_1|\phi_b\rangle .
$$

則

$$
|\psi_r\rangle|\psi_s\rangle
=x_0y_0|\phi_a\phi_a\rangle+x_0y_1|\phi_a\phi_b\rangle
+x_1y_0|\phi_b\phi_a\rangle+x_1y_1|\phi_b\phi_b\rangle .
$$

要等於 $\alpha|\phi_a\phi_b\rangle+\beta|\phi_b\phi_a\rangle$ 需要四個係數同時匹配：

$$
x_0y_0=0,\quad x_0y_1=\alpha,\quad x_1y_0=\beta,\quad x_1y_1=0 .
$$

由 $x_0y_0=0$：若 $x_0=0$ 則 $x_0y_1=\alpha$ 給 $\alpha=0$，矛盾；若 $y_0=0$ 則 $x_1y_0=\beta$ 給 $\beta=0$，矛盾。故無解。$\square$

把係數排成矩陣 $C=\begin{pmatrix}\alpha_{00}&\alpha_{01}\\ \alpha_{10}&\alpha_{11}\end{pmatrix}$，乘積態恰好對應 $\mathrm{rank}\,C=1$（因為 $C=\mathbf x\mathbf y^{\mathsf T}$）。這就是**舒密特秩（Schmidt rank）**；其一般形式可由 **A §6.4 的譜分解（Spectral Decomposition, L13119）** 得到：對任意係數矩陣 $C$ 做奇異值分解 $C=U\Sigma V^\dagger$，

$$
|\psi\rangle=\sum_i s_i\,|u_i\rangle_A|v_i\rangle_B,\qquad s_i\ge0,
$$

糾纏熵（T3 會用到）就是 $S=-\sum_i s_i^2\log_2 s_i^2$。

### 5. 從複合系統取邊際：子系統密度矩陣

若我們只看其中一部分，**G §12.3.3（L20415）** 給了做法。以單重態 $\frac{1}{\sqrt2}(|\uparrow\downarrow\rangle-|\downarrow\uparrow\rangle)$ 為例，只關心正子時

$$
\rho=\begin{pmatrix}1/2&0\\0&1/2\end{pmatrix} \tag{G Eq. 12.40}
$$

——**一個純的複合態，其子系統卻是完全混合態**。這是直積結構的另一個直接後果，也是 T4 的密度矩陣形式之所以必要的理由之一（在態向量語言裡無法表達「子系統的狀態」）。

---

## 結論

1. 單一 qubit 的狀態空間是 $\mathcal H_1=\mathbb C^2$（複維度 2），基底是 $\{|0\rangle,|1\rangle\}$（**G §4.4**）。
2. 複合系統的狀態空間是**張量積** $\mathcal H^{\otimes n}$，其基底由「每個單粒子基底各取一員的所有乘積」構成（**G §5.1 Eq. 5.11–5.12**；**A §17.5 L34878**）。由引理 1.1–1.3 與定理 1.4，維度是

   $$\boxed{\ \dim_{\mathbb C}(\mathbb C^2)^{\otimes n}=2^n\ }$$
3. 這**不是**直和。直和的維度是 $2n$，且無法承載聯合分布；直和是在**分解**直積表示時才出現（**A §17.5 L34920**：$e\otimes e=A_1\oplus A_2\oplus E$）。
4. 直積結構導致**糾纏**：存在不能寫成乘積的態（**G §5.1 L9845**、**G Problem 12.1**），等價於係數矩陣的秩 $>1$。
5. 本專案取 $n=5$，故維度 $=2^5=32$，與專案常數檔的 $(\mathbb C^2)^{\otimes5}\cong\mathbb C^{32}$ 一致。

---

## 對本專題的意義

**這是 RQ1「指數那一半」的來源。** 具體三點：

1. **容量直覺的來源。** 5 個 qubit 的狀態由 $2^5=32$ 個複振幅描述（歸一化後 62 個實參數，模掉全域相位；見 T2 的數值驗證）；密度矩陣則是 $32\times32$。相較之下，古典 5 維機率向量只有 4 個自由參數。**這個指數落差是「量子電路可能很大」這個直覺的全部來源。**
2. **但落差只在「狀態」，不在「控制」。** 2 的次方來自在每個 qubit 上各取一個基底成員——基底個數是乘積，而控制這些振幅的能力才是 T2 的主題。T1 的結論必須與 T2 合讀：**$2^n$ 是描述一個態所需要的，不是你能獨立設定的。**
3. **糾纏是直積結構的副產品，不是額外假設。** 因為複合空間是直積，所以有非乘積態；因為有非乘積態，所以有 RQ1 的兩難（T3）。這條推導鏈是：**直積 $\to$ 糾纏 $\to$ 張量網路可模擬性 $\to$ 沒有免費優勢。**

**在本專案的具體用法**：32 維基底 $\{|b_0\cdots b_4\rangle\}$ 就是輸出層的 32 個類別空間；讀出 $P(x)=\mathrm{Tr}[M_x\rho]$（T6）取的就是這 32 個基底上的對角元。所有後續文件都建立在 (1.3) 之上。

---

## 數值驗證

腳本：`theory/verify/t1_t2_dimensions.py`（T1 部分，與 T2 共用）
執行：`uv run python projects/qbn-capacity-calibration/theory/verify/t1_t2_dimensions.py`

**實際輸出（節錄）**：

```
==========================================================================
T1【1】張量積 vs 直和：2^n 與 2n 的差別
==========================================================================
    n     2^n (張量積)    2n (直和)      比值 2^n / 2n
    1             2             2             1.000
    2             4             4             1.000
    3             8             6             1.333
    4            16             8             2.000
    5            32            10             3.200
    6            64            12             5.333
...
    n=1   2^n = 2                  2n = 2
    n=2   2^n = 4                  2n = 4
    n=5   2^n = 32                 2n = 10
    n=10  2^n = 1024               2n = 20
    n=20  2^n = 1048576            2n = 40
    n=50  2^n = 1125899906842624   2n = 100
  [PASS] 2^n = 2n 只在 n=1,2 成立
  [PASS] n=5 時 2^n = 32 >> 2n = 10

==========================================================================
T1【2】顯式建構 (C^2)^{⊗n} 的基底
==========================================================================
  [PASS] n=1: 張量積基底有 2 個元素且線性獨立（秩 2）
  [PASS] n=2: 張量積基底有 4 個元素且線性獨立（秩 4）
  [PASS] n=3: 張量積基底有 8 個元素且線性獨立（秩 8）
  [PASS] n=5: 張量積基底有 32 個元素且線性獨立（秩 32）
  [PASS] n=2: 直和基底只有 4 個 = 2n（對照張量積 4）
  [PASS] n=5: 直和基底只有 10 個 = 2n（對照張量積 32）

==========================================================================
T1【3】乘積態的係數是係數的乘積；糾纏態不是乘積態
==========================================================================
  [PASS] |a>⊗|b> 的係數 = a_i b_j（kron 定義）   kron = [0.424264 0.424264 0.565685 0.565685]
  [PASS] 貝爾態的係數矩陣秩 = 2 > 1 → 不是乘積態   奇異值 = [0.707107 0.707107]
  [PASS] 乘積態的係數矩陣秩 = 1
  貝爾態若可分解則需 x0 y0 = 1/√2, x0 y1 = 0, x1 y0 = 0, x1 y1 = 1/√2。
  由 x0 y1 = 0 得 x0=0 或 y1=0；兩種都與 x0 y0 = 1/√2 ≠ 0 及 x1 y1 = 1/√2 ≠ 0 矛盾。
  [PASS] 貝爾態的舒密特秩 = 2（最大糾纏，1 ebit）   糾纏熵 = 1.0000000000 bit
```

**驗證涵蓋**：定理 1.4 的維度計數（$n=1,2,3,5$ 逐一顯式建基底並用數值秩檢定確認線性獨立）、直和與直積的基底個數差異、乘積態與糾纏態的係數矩陣秩（第 4 節的判準）、以及舒密特秩與糾纏熵的數值一致。

---

## 待核實事項

- **本文件沒有未核實的教科書出處。** §3.1、§3.6.1、§3.6.2、§4.4、§5.1、§12.1、§12.3.3、§A.1–A.3（G）與 §4.1、§5.1、§17.5（A）、Problem 3.25／3.26／5.1（GS）皆已回查原文行號。
- **「複合系統的狀態空間是張量積」在 G 中是公設而非定理**（G §5.1 直接寫下 $\Psi(\mathbf r_1,\mathbf r_2,t)$）。本文件在推導第 2 節明確標示了哪一步是公設（引理 1.3），沒有把它偽裝成證出來的結果。
- 舒密特分解（Schmidt decomposition）一詞在三本書中都**只以「Gram–Schmidt」出現**（已用關鍵字 `Schmidt` 搜尋：G 7 命中、A 55 命中、GS 1 命中，全部是 Gram–Schmidt 正交化，無一是 Schmidt 分解）。本文件改由 **A §6.4 的譜分解**推出同樣的結果，並在推導第 4 節說明是**本文件的推導**而非課文原文。
