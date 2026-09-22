# arXiv 投稿準備

**目標**：把本專案投上 arXiv，取得可引用的識別碼。

> 本文件所有規則均引自 arXiv 官方文件（`info.arxiv.org`），非二手資訊。
> 最後查證日期：2026-09-16。

---

## 一、兩個會擋住你的關卡（先處理這兩個）

### 關卡 1：背書（endorsement）——**第一次投稿必須有**

arXiv 官方規定：

> 「arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category.」

**取得背書的兩條路**：

| 路徑 | 條件 | 對你是否可行 |
|---|---|---|
| **A. 自動取得** | 有**機構 email**（學校信箱）**且**已「認領」過自己參與的論文 | ⚠️ 若你之前沒投過 arXiv，這條走不通 |
| **B. 個人背書** | 找一位在該領域**已發表過數篇 arXiv 論文**的學者幫你背書 | ✅ **你應該走這條** |

**B 的具體流程**（arXiv 官方步驟）：

1. 開始一個新投稿，選定你要投的類別
2. 檢查信箱，會收到**背書請求信**，內含一個可給背書人的連結
3. 在 arXiv 上找該領域的相關論文，在摘要頁底部點 **「Which authors of this paper are endorsers?」**
4. 從該頁的 **Submission history** 標題下方找到對方的 email
5. 把第 2 步的**背書請求信**寄給對方

**誰適合當你的背書人**（官方原話）：

> 「a good choice for graduate students would be your thesis advisor or another professor in your department/institution working in your field who is also an active author on arXiv」

→ **你的指導老師**，或 **Poyuan 的物理系老師**（若有 arXiv 發表紀錄）。

**⚠️ 官方禁用事項**：
- 「it is inappropriate to email large numbers of potential endorsers at once」
- 「or to repeatedly email the same endorser」

**背書人的責任**（官方原話，你要理解對方的顧慮）：

> 「You should know the person that you endorse **or** you should see the paper that the person intends to submit.」
> 「**The endorsement process is not peer review.**」
> 「You should not endorse the author if the author is unfamiliar with the basic facts of the field, or if the work is entirely disconnected with current work in the area.」

→ **所以寄請求時，附上你的稿子與一段簡短說明**，讓對方能判斷「這是不是該領域的工作」。

**類別選擇**：`quant-ph`（量子物理）或 `cs.LG`（機器學習）。
本專案的主體是「量子電路的受控檢驗」，**`quant-ph` 較合適**。
⚠️ 注意：`quant-ph` 的背書**只適用於 `quant-ph`**，換類別要重新背書。

### 關卡 2：★ 語言——**arXiv 的 metadata 必須是英文**

這是本專案**目前最大的障礙**，而且很多人不知道：

| 項目 | 要求 |
|---|---|
| **標題（Title）** | **必須英文** |
| **摘要（Abstract）** | **必須英文** |
| 正文 | 可以非英文，但有額外要求（見下） |

arXiv 有 **Non-English submissions** 專頁，對非英文正文有規範。
**實務上**：非英文正文的論文在 arXiv 上很少見，且部分類別不接受。

**可行策略（三選一）**：

| 策略 | 做法 | 建議 |
|---|---|---|
| **A. 全英文** | 正文改寫成英文 | ⭐ **最推薦**。arXiv 的讀者不讀中文，中文稿等於沒有曝光 |
| B. 英文 metadata + 中文正文 | 標題、摘要英文；正文中文 | ⚠️ 需先查該類別是否接受，且審核可能被打回 |
| C. 中英雙語 | 英文正文 + 中文附錄 | 折衷，工作量大 |

**本專案的 Typst 模板已備有英文標題**（`Capacity Cliff and Calibration Ablation in a Hybrid Quantum--Classical Classifier`），
摘要已改為英文（2026-09-23）。

---

## 二、投稿前檢查清單

### 必要項目

- [ ] **英文標題與摘要**（見關卡 2）
- [ ] **作者與 affiliation 正確**（含機構 email；arXiv 的機構 email 有助於日後自動取得背書資格）
- [ ] **取得背書**（見關卡 1）
- [ ] **類別選定**（`quant-ph`，可另加 `cs.LG` cross-list）
- [ ] **授權條款選定**（arXiv 提供多種 CC 授權；本專案建議 CC BY 4.0，與多數期刊相容）
- [ ] **檔案格式**（見下）

### 檔案格式

| 方式 | 說明 | 建議 |
|---|---|---|
| **TeX/LaTeX 原始碼** | arXiv 原生格式，可自動產生 HTML 版 | ⭐ 但本專案用 Typst |
| **PDF** | arXiv 接受，但**不建議**（無法產生 HTML、metadata 較差） | 可用 |

**Typst → arXiv 的實務做法**：

```powershell
typst compile paper.typ          # 產生 paper.pdf
# 然後在 arXiv 用 PDF 投稿
```

⚠️ **PDF 投稿的限制**（arXiv 官方明說）：
- 不會產生 arXiv 的 HTML 版本
- 提交時若 TeX 原始碼可用，arXiv 建議提供原始碼

**若日後要投期刊**（IEEE Access 等），它們多數接受 PDF，所以 Typst 路線沒問題。

### 內容要求

- [ ] **第一兩頁就要寫清楚主要結果與假設**（arXiv 與 Quantum 都有此要求，且對審閱者友善）
  → 模板已有「貢獻摘要」框
- [ ] **作者貢獻聲明**（多數期刊強制；先寫好省得以後改）
- [ ] **LLM 使用揭露**（**若你用了 AI 協助，必須揭露**）

### ★ LLM 使用披露（arXiv 與 Quantum 都有要求）

**arXiv 官方要求**（info.arxiv.org/help/moderation/index.html，「Policy for authors’ use of generative AI language tools」，2026-09-23 查證）：

> we continue to require authors to **report in their work any significant use of sophisticated tools**, such as instruments and software; we now include in particular **text-to-text generative AI** among those that should be reported consistent with subject standards for methodology.

> by signing their name as an author of a paper, they each individually take full responsibility for all its contents, **irrespective of how the contents were generated**.

> generative AI language tools **should not be listed as an author**.

**Quantum 期刊**（quantum-journal.org/instructions/authors/，2026-09-23 逐字查證）：AI 使用範圍要写進 **author contribution statement**，例如：文法检查、改写、文字生成、圖像生成、書目查找、**程式碼與計算生成**），且明言「If no AI was used in producing the work, authors are welcome to state this.」。

> ⚠️ **更正 2026-09-23**：本檔原先写「arXiv 目前無強制」，**那是錯的**——arXiv 的 Content Moderation 政策把 text-to-text 生成式 AI 明列為應回報的工具。因此，本專案**不能不写**披露。

**本專案要揭露的範圍**（誠實填寫）：

- 文獻抽取與整理（10 篇論文的 OCR 抽取筆記）
- 程式碼產生與除錯（CUDA-Q 探測腳本、NumPy 模擬器、評估工具）
- 文字草稿與改寫
- 圖表產生

模板已加入對應段落。

---

## 三、投稿後

| 項目 | 說明 |
|---|---|
| **多久上線** | 通常 1–2 個工作日（需過 moderation） |
| **識別碼** | 格式 `arXiv:YYMM.NNNNN`，例：`arXiv:2609.12345` |
| **可引用性** | arXiv 的識別碼**可被引用**，且多數期刊接受引用 arXiv 預印本 |
| **取得正式 DOI** | arXiv 本身**不發 DOI**；若要正式 DOI 需投期刊 |
| **更新版本** | 可隨時上傳新版本（`v2`、`v3`）；**已發表的版本不能刪除**，只能 withdraw |

!!! warning "arXiv 的識別碼不是 DOI"
    你原本問「只要能混到 DOI 編號就好」——**arXiv 給的是 arXiv ID，不是 DOI**。
    但它在實務上可被引用，而且**多數台灣學校的畢業門檻認定 arXiv 預印本為學術成果**（請自行向系辦確認）。

    **若要正式 DOI**，arXiv 之後仍需投一個有 DOI 的期刊或會議。

---

## 四、如果要正式 DOI：arXiv 之後的下一步

| 管道 | 週期 | 費用 | 備註 |
|---|---|---|---|
| **IEEE Access** | 4–6 週 | ~US$1,950 | 最穩；F9 綜述點名為 QNLP 主要管道 |
| MDPI *Entropy* | 4–6 週 | ~CHF 2,600 | 主題最對口；先查校系觀感 |
| Scientific Reports | 8–12 週 | ~US$2,690 | 基準論文發表處 |
| IEEE QCE（會議） | 3–4 月 | ~US$800 | 對 PoC 型量子 ML 友善 |
| 國內研討會 | 視情況 | 低 | 對「專題等級」最實際 |

**❌ 不建議 Quantum（open journal）**：雖然免費，但其明文規定
「**Correct but incremental work is below threshold**」——本專案的定位過不了。
（詳細分析見對話記錄；重點是它還要求「顯著超越現況」。）

---

## 五、行動順序（建議）

1. **【現在】** 把標題與摘要翻成英文（正文可暫留中文，但英文版要並行進行）
2. **【現在】** 補上作者貢獻聲明與 LLM 使用揭露（模板已備位）
3. **【本週】** 確認指導老師或 Poyuan 的老師是否願意、且有資格背書
4. **【論文完成後】** 開始 arXiv 新投稿 → 取得背書碼 → 請對方背書
5. **【上線後】** 再決定要不要投期刊拿正式 DOI

---

## 附錄：獨立編譯驗證要用對引擎（2026-09-22 補）

驗證 `submission.zip` 能否在乾淨目錄獨立編譯時，**必須用 xelatex**，與 `build_tex.bat` 一致：

```bash
# 解壓到乾淨目錄後
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper.tex
```

**結果（2026-09-23 重測）**：`rc=0`、**18 頁**、0 overfull、0 float-too-large、
0 LaTeX error、0 undefined control sequence。

> ⚠️ **不要用 `latexmk -pdf`（pdflatex）來做這個驗證。**
> pdflatex 會走 `graphicx → epstopdf-base → grfext.sty` 這條路徑；`grfext` 在 MiKTeX 是獨立套件，
> 本機**沒安裝**，而 `mpm --install=grfext` 會因網路逾時失敗（`Sorry, but: Timeout was reached`），
> 於是編譯會停在 `! LaTeX Error: File 'grfext.sty' not found.`。
> **那是測試指令的問題，不是論文的問題**——arXiv 用完整 TeX Live，graphicx 的這條依賴本來就滿足。
> 已用 xelatex 重驗通過。若哪天真的要用 pdflatex 驗，先讓 MiKTeX 連上網裝 grfext。

---

## arXiv 端的編譯引擎：**在 Review Files 步驗選 xelatex**

arXiv 官方文件（info.arxiv.org/help/00README.html）說明：支援的 `compiler` 值包含 `xelatex`；
但同時明說**不建議投稿前手動建立 `00README.json`**——
arXiv 會在 **Review Files** 步驗自動生成它。

**所以正確做法**：上傳後在 Review Files 步驗把編譯器選成 `xelatex`，並當場檢視編譯日誌。

**為什麼不能赌 pdflatex**：本包載入 `microtype` + `[T1]{fontenc}`；2026-09-23 在筆電實測
`pdflatex paper.tex` 直接失敗（`pdfTeX error (font expansion): auto expansion is only possible with scalable fonts`， rc=1，未生成 PDF）。
arXiv 的 TeX Live 字型較完整、**可能**没事，但沒必要赌——選 xelatex 是零成本。

附註：arXiv **不會**跑 bibtex，所以必須自己附 `.bbl`。本包已附 `paper.bbl`（18 筆），合規。

