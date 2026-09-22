# 理論基礎：用教科書解釋容量斷崖與校準消融

**負責人：Poyuan Chung**（物理系理論組）

---

## 這份文件要解決什麼

本專題有兩個核心研究問題，而它們**都需要物理解釋**，不能只給實驗數字：

| 研究問題 | 需要的物理解釋 |
|---|---|
| **RQ1 容量斷崖** | 為什麼量子電路的「狀態空間大小」與「可訓練容量」不是同一件事？為什麼容量過大反而劣化？ |
| **RQ2 校準消融** | 去相位算子對密度矩陣做了什麼？為什麼它會傷害校準？為什麼它必須插在么正層之前才有效？ |

**你的任務**：用指定的三本教科書，把上面每一項都推導出來，並且**每一個結論都要能指出教科書的章節或頁碼**。

---

## 指定教材

| 代號 | 書 | 本地檔案 | 大小 |
|---|---|---|---|
| **G** | Griffiths & Schroeter, *Introduction to Quantum Mechanics*, 3rd ed. | `.docs/Introduction to Quantum Mechanics 3rd Edition..md` | 1.49 MB |
| **GS** | 同書 *Instructor's Solution Manual* | `.docs/Instructors' Solution Manual to Introduction to Quantum -- David Jeffrey Griffiths, Darrell F_ Schroeter -- 3rd..md` | 1.65 MB |
| **A** | Arfken, Weber & Harris, *Mathematical Methods for Physicists*, 7th ed. | `.docs/Mathematical Methods for Physicists A Comprehensive Guide, Seventh edition.md` | 3.14 MB |

!!! warning "這三個檔案都是巨檔，禁止整檔讀取"
    * 單檔 > 7000 行，`read` 整檔會逾時。
    * **先做章節樹偵察**（秒級），再分塊讀取（每塊 300–800 行）：

    ```powershell
    # 1) 取得章節樹與行號
    Select-String -Path '<檔案>' -Pattern "^#{1,3} " |
      ForEach-Object { "$($_.LineNumber)`t$($_.Line)" }

    # 2) 分塊讀取
    Get-Content '<檔案>' -Encoding UTF8 -TotalCount $end | Select-Object -Skip ($start-1)
    ```

---

## 要交付的六個理論結果

每一項請寫成一個小節，結構固定：**問題 → 教科書基礎 → 推導 → 結論 → 對本專題的意義**。

### T1. 為什麼 $n$ 個 qubit 的狀態空間是 $2^n$ 維？
- **教科書基礎**：G 第 3 章（形式論）、A 的向量空間與希爾伯特空間章節
- **要推導**：從單一 qubit 的二維複向量空間，用**張量積**推廣到 $n$ 個 qubit
- **要指出**：為什麼這是「直積」不是「直和」（$2^n$ vs $2n$ 的差別）
- **對本專題的意義**：這是「指數」那一半的來源

### T2. 為什麼狀態空間是指數的，可訓練參數卻是多項式的？
- **教科書基礎**：G 的么正變換章節（$U = e^{-iHt/\hbar}$ 與閘的關係）
- **要推導**：$n$ 個 qubit 上的么正群 $U(2^n)$ 的實維度是 $2^{2n}-1$；
  但只放多項式個閘所能觸及的參數空間是多少維？
- **關鍵數字**：本專題的 5 qubit 範例——狀態空間 $32^2-1 = 1023$ 維，但電路只有 **10 個可訓練角度**
- **對本專題的意義**：**這是 RQ1 的理論核心**——「可達子空間」遠小於「環境空間」

### T3. 為什麼「可訓練」與「古典難解」互相衝突？
- **教科書基礎**：G 的糾纏章節、密度算符與熵
- **要推導**：淺層局部電路的糾纏熵上界 → 為什麼這使得張量網路方法能有效模擬
- **要說明**：深層高糾纏電路雖然古典難解，但會遭遇 barren plateau（梯度指數衰減）
- **對本專題的意義**：**這是「為什麼沒有量子優勢」的結構性解釋**

### T4. 去相位算子的數學定義
- **教科書基礎**：G 的密度算符章節（特別是「混合態」與「約化密度矩陣」）
- **要推導**：
  - 寫出去相位（dephasing）的 **Kraus 算符** $K_0 = |0\rangle\langle 0|$、$K_1 = |1\rangle\langle 1|$
  - 證明 $\mathcal{E}(\rho) = K_0\rho K_0^\dagger + K_1\rho K_1^\dagger$ **把非對角元歸零**
  - 驗證跡保性 $\mathrm{Tr}[\mathcal{E}(\rho)] = \mathrm{Tr}[\rho]$
- **對本專題的意義**：這是 RQ2 消融實驗所施加的算子

### T5. 為什麼去相位必須插在么正層之前才有效？
- **教科書基礎**：G 的算符代數、交換子
- **要推導**：
  - 證明 CNOT 與「計算基底去相位」**交換**（$\mathcal{E}_{\text{deph}} \circ \text{CNOT} = \text{CNOT} \circ \mathcal{E}_{\text{deph}}$）
  - 因此若去相位接在電路尾端（測量前），對測量結果**完全沒有影響**
  - 反之，含 $R_Y/R_Z$ 的層與去相位**不對易**，所以插在它前面才有效果
- **本地實測證據**（可直接引用）：

  | 去相位位置 | 32 維機率的最大變化 |
  |---|---|
  | 電路最尾端 | $1.4\times10^{-17}$（≈ 0） |
  | 中間、之後只接 CX | $1.4\times10^{-17}$（≈ 0） |
  | 中間、之後接含 $R_Y/R_Z$ 的完整層 | **0.0502** |

- **對本專題的意義**：**這是最容易做錯的一步**。做錯會誤判「量子性沒貢獻」

### T6. 測量理論與校準的關係
- **教科書基礎**：G 的測量公設、Born 法則
- **要推導**：$P(x) = \mathrm{Tr}[M_x \rho]$，並說明為什麼測量**天生就是取樣**
- **要連結**：這與古典 BNN 需要跑 $T$ 次蒙地卡羅前向（或存 $T$ 份權重）的差別
- **對本專題的意義**：這是「量子測量作為不確定性來源」的理論基礎

---

## 輸出格式

每個理論結果寫成一個 markdown 檔，放在
`projects/qbn-capacity-calibration/theory/T1_*.md` … `T6_*.md`

每檔的結構：

```markdown
# T1. <標題>

## 問題陳述
<這個理論結果要回答什麼>

## 教科書基礎
| 書 | 章節 | 內容 |
|---|---|---|
| G | 3.1 | ... |

## 推導
<完整的數學推導，用 LaTeX>

## 結論
<一段話總結>

## 對本專題的意義
<這個結論怎麼用在 RQ1 或 RQ2>

## 數值驗證（可選但強烈建議）
<用 Python 驗證推導的結果，附實際輸出>
```

!!! qbn-lab "強烈建議：每個推導都用 Python 驗證一次"
    純理論推導很容易出錯。本站已有可用的工具：
    * `dev/qbn_sim.py`：純 NumPy 狀態向量模擬器（自我測試 63/63）
    * `dev/qbn_circuit.py`：5 qubit QBN 電路
    * `dev/verify_ps_correct.py`：梯度驗證範例

    例如 T4 的驗證：
    ```python
    import numpy as np
    # 造一個有相干性的態
    plus = np.array([1, 1]) / np.sqrt(2)
    rho = np.outer(plus, plus.conj())
    print("去相位前非對角元 =", rho[0, 1])
    K0 = np.array([[1, 0], [0, 0]])
    K1 = np.array([[0, 0], [0, 1]])
    rho_d = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    print("去相位後非對角元 =", rho_d[0, 1])
    print("跡 =", np.trace(rho_d).real)
    ```

---

## 驗收標準

1. 每一項都能指出**教科書的章節編號**（不是「某本書裡有」）
2. 推導過程完整，沒有「顯然可知」的跳步
3. 至少 T4、T5 有 Python 數值驗證
4. 能對一個物理系背景的人講 30 分鐘而不被問倒
