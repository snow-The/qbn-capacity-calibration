# MTEB 分類任務調查

> **調查代號**：MT1
> **調查日期**：2026-04（依 GitHub `main` 分支與 HF API 即時查詢）
> **用途**：為「混合量子-古典分類器的容量斷崖與校準消融」專題選定實驗資料集
> **前端模型**：`minishlab/potion-multilingual-128M`（靜態嵌入、256 維、101 語言）
> **主要對手**：`hotchpotch/bekko-embedding-v1-a25m`（384 維，可 Matryoshka 截斷）

---

## 一、調查方法與來源

本節記錄**實際執行過的查詢**與**實際取得的結果**。所有數字皆可回溯至下列 URL。

### 1.1 權威來源（任務定義）

| # | 來源 | URL | 取得什麼 |
|---|---|---|---|
| S1 | MTEB 分類任務目錄（GitHub API） | `https://api.github.com/repos/embeddings-benchmark/mteb/contents/mteb/tasks/classification` | 57 個語言子目錄清單 |
| S2 | MTEB 分類任務總索引 | `https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/tasks/classification/__init__.py` | 57 個 `from .xxx import *` |
| S3 | 多語言分類任務索引 | `.../classification/multilingual/__init__.py` | 45 個任務類別名稱 |
| S4 | 中文分類任務索引 | `.../classification/zho/__init__.py` | 13 個任務類別名稱 |
| S5 | 分類任務抽象基底類別 | `https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/abstasks/classification.py` | **評估協定的權威定義**（見 §五） |
| S6 | 全部分類任務原始碼掃描 | PowerShell 逐檔抓取 281 個 `.py` | 全庫任務類別總數與中文相關檔案 |

### 1.2 資料集事實（HF API）

| # | 來源 | 用途 |
|---|---|---|
| S7 | `https://datasets-server.huggingface.co/splits?dataset=<id>` | 確認 **split 名稱**與 config 是否存在 |
| S8 | `https://datasets-server.huggingface.co/size?dataset=<id>&config=<cfg>` | 確認**樣本數**（逐 split） |
| S9 | `https://datasets-server.huggingface.co/first-rows?dataset=<id>&config=<cfg>&split=<s>` | **實地檢視文本**，判定繁簡 |
| S10 | `https://huggingface.co/datasets/mteb/<id>/raw/main/README.md` | MTEB 自動產生的描述統計（標籤數、train/test 重疊） |

### 1.3 模型事實

| # | 來源 | 用途 |
|---|---|---|
| S11 | `https://huggingface.co/api/models/intfloat/multilingual-e5-small` | 對手的 `model-index` 實測分數 |
| S12 | `https://huggingface.co/intfloat/multilingual-e5-small/raw/main/config.json` | `hidden_size`、`max_position_embeddings` |
| S13 | `https://huggingface.co/hotchpotch/bekko-embedding-v1-a25m/raw/main/config.json` | 對手模型維度與上下文長度 |
| S14 | `https://huggingface.co/hotchpotch/bekko-embedding-v1-a25m/raw/main/1_Pooling/config.json` | 池化方式與維度 |
| S15 | `docs/_extract/F10-static-word-embeddings-sentence.md`（本地） | `potion-multilingual-128M` 規格與 MTEB 欄位警告 |

### 1.4 失敗的方法（記錄下來避免重複嘗試）

| 方法 | 結果 | 替代方案 |
|---|---|---|
| GitHub Code Search API（`/search/code?q=cmn-Hant`） | **HTTP 401**（需認證） | 改用 S6：逐檔抓取 + 本地 regex 掃描 |
| `platform_search`、`search_arxiv` | 本專案已證實不可靠，**未使用** | 直接抓原始碼與 API |
| `splits?dataset=mteb/mtop_intent` | **404** | MTOP 直接讀原始碼即可 |
| `size?dataset=mteb/sib200.v2&config=zho_Hant` | **404** | 標為 `TODO(核實)` |

### 1.5 掃描結果總計

| 項目 | 數值 | 來源 |
|---|---|---|
| `mteb/tasks/classification/` 下的 `.py` 檔數 | **281** | S6 |
| 其中定義的任務類別總數 | **580** | S6（regex `^class\s+\w+`） |
| 語言子目錄數／**含中文的檔案數** | **57** ／ **10** | S1、S6 |
| 英語／多語言／中文子目錄任務數 | 257 ／ 45 ／ 13 | S6 |

> **重要**：580 這個數字**包含**大量非文本模態任務（影像、音訊、影片），例如
> `eng/` 底下有 `mnist_classification.py`、`food101_classification.py`、`speech_commands.py`。
> **純文字分類**任務遠少於此數。本專案前端是靜態**文字**嵌入，
> 因此**只能使用 `modalities=["text"]` 的任務**。

---

## 二、分類任務總表

> **製表原則**：580 個任務不可能逐一列出且無實益。
> 本表列出 (a) **全部含中文的任務**、(b) 本專案可能用到的**代表性子集**。
> 「指標」欄位若為 `accuracy`，代表 `main_score="accuracy"`；
> 但 MTEB **同時**回報 macro-F1 等（詳見 §五）。
> 「樣本數」若標 `(單一語言)`，指**該語言 config** 的樣本數，非全庫總和。

### 2.1 含中文的任務（★ 本專案關鍵）

| 任務名 | HF repo（MTEB 定義的 `path`） | 語言標籤 | 含繁體中文 | 指標 | split | 樣本數 | 來源 |
|---|---|---|---|---|---|---|---|
| **MassiveIntentClassification** | `mteb/amazon_massive_intent` | `zh-TW: cmo-Hant`、`zh-CN: cmo-Hans` + 49 語 | **是（zh-TW，實測確認）** | accuracy | `train`/`validation`/`test` | zh-TW：11514 / 2033 / **2974** | S6、S7、S8、S9 |
| **MassiveScenarioClassification** | `mteb/amazon_massive_scenario` | 同上 51 語 | **是（zh-TW，實測確認）** | accuracy | `train`/`validation`/`test` | zh-TW：11514 / 2033 / **2974** | S6、S7、S8、S9 |
| **SIB200Classification** | `mteb/sib200` | `zho_Hant: zho-Hant`、`yue_Hant: yue-Hant` + 200+ 語 | **是（zho-Hant，實測確認）** | accuracy | `train`/`validation`/`test` | zho_Hant：172 / 24 / **24** | S6、S7、S8、S9 |
| **SIB200Classification.v2** | `mteb/sib200.v2` | 同上（共用 `_LANGS`） | **是（zho-Hant）** | accuracy | `test` | `TODO(核實)`（API 404） | S6 |
| **YueOpenriceReviewClassification** / `.v2` | `izhx/yue-openrice-review` / `mteb/yue_openrice_review` | `yue-Hant` | **是（粵語繁體，非台灣中文）** | accuracy | `test` | 原始 2326 → **分層抽樣** | S6、S8 |
| AmazonReviewsClassification | `mteb/AmazonReviewsClassification` | `zh: cmn-Hans` + en/de/es/fr/ja | **否（僅簡體）** | accuracy | `train`/`validation`/`test` | zh：200000 / 5000 / **5000** | S6、S7、S8 |
| MultilingualSentimentClassification | `mteb/multilingual_sentiment`（路徑待核） | 多語，含 `cmn-Hans` | **否（僅簡體）** | accuracy | 依 config | 逐語言 | S6 |
| MultiHateClassification | `mteb/multi-hatecheck` | `cmn: cmn-Hans` + 10 語 | **否（僅簡體）** | accuracy | `test` | 每語言抽 1000 train + 1000 test | S6 |
| LanguageClassification | 見 `multilingual/language_classification.py` | `cmn-Hans` | **否（僅簡體）** | accuracy | 見原始碼 | 見原始碼 | S6 |
| MInDS14 | `multilingual/m_in_ds14.py` | `zh-CN` | **否（僅簡體）** | accuracy | 見原始碼 | 見原始碼 | S6 |
| TNews / `.v2` | `C-MTEB/TNews-classification` / `mteb/t_news` | `cmn-Hans` | **否（僅簡體）** | accuracy | `validation` | 49490/9579/8841 | S4、S8 |
| IFlyTek / `.v2` | `C-MTEB/IFlyTek-classification` / `mteb/i_fly_tek` | `cmn-Hans` | **否（僅簡體）** | accuracy | `validation` | 11288/2412/2279 | S4、S8 |
| JDReview / `.v2` | `C-MTEB/JDReview-classification` / `mteb/jd_review` | `cmn-Hans` | **否（僅簡體）** | accuracy | `test` | 3064 / **388** | S4、S8 |
| OnlineShopping | `C-MTEB/OnlineShopping-classification` | `cmn-Hans` | **否（僅簡體）** | accuracy | `test` | 696 / **99** | S4、S8 |
| Waimai / `.v2` | `C-MTEB/waimai-classification` / `mteb/waimai`（**404**） | `cmn-Hans` | **否（僅簡體）** | accuracy | `test` | 8000 / **1000** | S4、S8 |
| MultilingualSentiment / `.v2` | `C-MTEB/MultilingualSentiment-classification` / `mteb/multilingual_sentiment` | `cmn-Hans` | **否（僅簡體）** | accuracy | `validation`/`test` | 117488 / 2983 / **2897** | S4、S8 |

### 2.2 代表性非中文任務（對照組候選）

| 任務名 | HF repo | 語言 | 指標 | split | 樣本數 | 來源 |
|---|---|---|---|---|---|---|
| MTOPIntentClassification | `mteb/MTOPIntentClassification` | en, de, es, fr, hi, th（**無中文**） | accuracy | `validation`/`test` | 未查 | S6 |
| MTOPDomainClassification | `mteb/MTOPDomainClassification` | 同上（**無中文**） | accuracy | `validation`/`test` | 未查 | S6 |
| AmazonCounterfactualClassification | `mteb/amazon_counterfactual` | en, de, ja（**無中文**） | accuracy | `test` | 未查 | S6、S11 |
| Banking77Classification | `mteb/banking77` | eng | accuracy | `test` | 10K–100K | S6 |
| AmazonPolarityClassification | `mteb/amazon_polarity` | eng | accuracy | `test` | 1M–10M | S6 |
| ImdbClassification | `mteb/imdb` | eng | accuracy | `test` | 10K–100K | S6 |

### 2.3 已排除：MASSIVE 的越南語「複製品」

`mteb/tasks/classification/vie/` 下有 14 個任務，其中包含
`massive_intent_vn_classification.py`、`massive_scenario_vn_classification.py`、
`mtop_intent_vn_classification.py` 等——這些是**越南語版本**，與中文無關，
但**證明 MTEB 允許為單一語言建立 MASSIVE 的衍生任務**。
若未來我們要為**台灣中文**建立專屬子集，這是可參考的模板。

---

## 三、含繁體中文的候選（★ 重點）

### 3.1 判定方法（為什麼可信）

**不採用「語言標籤推論」**，而是用 BCP-47 的**文字系統子標籤**（script subtag）：

| 標記 | 意義 | 判定 |
|---|---|---|
| `cmo-Hant` | 中文語族（cmo = Chinese macrofamily）+ **漢字（繁體）** | ★ 繁體 |
| `cmn-Hans` | 官話 + **簡體字** | 簡體 |
| `zho-Hant` | 中文 + **繁體字** | ★ 繁體 |
| `zho-Hans` | 中文 + **簡體字** | 簡體 |
| `yue-Hant` | 粵語 + 繁體字 | 繁體（但**非台灣中文**） |

**進一步實地驗證**（S9，`first-rows` API 直取實際文本）：

`mteb/amazon_massive_intent`，`config=zh-TW`，`split=test`：

```
[alarm_set]            這週早上五點叫醒我
[audio_volume_mute]    安靜
[iot_hue_lightchange]  我們需要的粉紅色
[iot_hue_lighton]      黑暗降臨
[iot_hue_lightoff]     關掉臥室電燈
[iot_cleaning]         這裡很髒製造一點噪音
```

`config=zh-CN`，`split=test`（以下為**逐字引用的資料集原文**，保留簡體以資對照，
非本檔行文用字）：

```
[alarm_set]            这周五点叫我起床
[audio_volume_mute]    安静
[iot_hue_lightchange]  我们想要粉红色
[iot_hue_lighton]      天暗下来了
[iot_hue_lightoff]     小王关闭了卧室里的灯
[iot_cleaning]         这里很脏弄出点声音来
```

**結論（可直接引用）**：
- `zh-TW` 的文本**確實是繁體中文**，且用語是**台灣用法**（「這週」「叫醒我」「關掉」）。
- `zh-CN` 的文本**確實是簡體中文**，且語序有重寫（「小王关闭了卧室里的灯」vs「關掉臥室電燈」），
  兩者是**獨立的在地化（localized）語料**，不是同一份文本的簡繁轉換。
- 這對本專案是**好消息**：`zh-TW` 是**真正的原生繁體語料**，不是「簡體轉繁體」的偽繁體。

`mteb/sib200`，`config=zho_Hant`，`split=train`：

```
抗議活動的組織者表示，柏林、科隆、漢堡和漢諾威等德國城市約有 10 萬人參與。
根據巴基斯坦憲法第 247 條，這些官員需負責治理與提供司法服務。
但總理約翰·霍華德表示，該法案只是為了保護醫院的設施不被塔斯馬尼亞政府降級，為此撥出額外的 4,500 萬澳幣。
因此馬薩至少會缺席 2009 年賽季的剩餘賽事。
但第一架真正的望遠鏡是 16 世紀末才在歐洲被製造出來的。
```

**結論**：SIB200 的 `zho_Hant` 也是**真實繁體**（「條」「萬」「望遠鏡」「賽季」皆為繁體）。
其來源是 **FLORES-200 的新聞文本**（Wikipedia 風格），與 MASSIVE 的口語指令語域完全不同。

### 3.2 MASSIVE 的 `zh-TW` 設定——逐項確認

使用者要求的「三點」逐一回答：

| 問題 | 答案 | 證據 |
|---|---|---|
| **是否真的有 `zh-TW`（繁體）而不只是 `zh`？** | **是，確實有 `zh-TW`** | `massive_intent_classification.py` 的 `_LANGUAGES` 末尾：`"zh-TW": ["cmo-Hant"]` |
| **若只有 `zh`，那是簡體還是繁體？** | 兩者**都有**，且是**兩個獨立 config**：`zh-CN`（`cmo-Hans`）與 `zh-TW`（`cmo-Hant`） | 同上；S7 確認兩個 config 都存在 |
| **樣本數與 split 名稱** | `train` / `validation` / `test`；zh-TW：11514 / 2033 / **2974** | S7（splits）、S8（size） |

**額外的獨立佐證**（使用者提到的線索，已驗證成立）：

`intfloat/multilingual-e5-small` 的 HF `model-index` **確實收錄 `MassiveIntentClassification (zh-TW)`**（S11）：

```json
{
  "dataset": {
    "config": "zh-TW",
    "name": "MTEB MassiveIntentClassification (zh-TW)",
    "revision": "31efe3c427b0bae9c22cbb560b8f15491cc6bed7",
    "split": "test",
    "type": "mteb/amazon_massive_intent"
  },
  "metrics": [
    {"type": "accuracy", "value": 62.53530598520511},
    {"type": "f1",       "value": 61.71131132295768}
  ],
  "task": {"type": "Classification"}
}
```

同一個 `model-index` 也收了 `zh-CN`（accuracy **68.238**）。
**注意這個落差**：同一個模型在簡體上 68.24、在繁體上 62.54，**相差 5.70 個百分點**。
這是「`zh` 標籤不代表繁體」的**直接實證**，可直接寫進書中當作動機。

> ⚠️ **MTEB revision 差異警告**：e5 的 `model-index` 記錄的 revision 是
> `31efe3c427b0bae9c22cbb560b8f15491cc6bed7`，但**目前 MTEB `main` 分支**的
> `massive_intent_classification.py` 寫的是 `4672e20407010da34463acc759c162ca9734bca6`。
> **兩者不同**。引用分數時**必須註明來源 revision**，否則不可比。
> 這正是 `F10` 文件提醒的「不同欄位不可直接相减」的同類陷阱——**不同 revision 亦不可直接相比**。

### 3.3 逐個候選說明

| 候選 | repo / config | 判定 | 理由與風險 |
|---|---|---|---|
| **A. MassiveIntentClassification (zh-TW)** | `mteb/amazon_massive_intent` / `zh-TW` | ✅ **首選** | 口語助理意圖分類，59–60 類。test 2974 筆足以做 ECE；有獨立 `validation` 可選超參與 temperature scaling；有 `train` 11514 供探針；有簡體對照。**風險**：類別極不平衡（`general_greet` 全庫 51 筆 vs `calendar_set` 10659 筆），accuracy 被大類主導，**必須並列 macro-F1** |
| **B. MassiveScenarioClassification (zh-TW)** | `mteb/amazon_massive_scenario` / `zh-TW` | ✅ **首選（難度對照）** | 同語料、同樣本數（11514/2033/2974），但只有 **18 類**。與 A **配對比較**可隔離「類別數」變數。18 類接近 5 qubit 的 32 維輸出空間，是容量斷崖的關鍵實驗點。**風險**：與 A 共用語料，不能當獨立資料集宣稱 |
| **C. SIB200Classification (zho-Hant)** | `mteb/sib200` / `zho_Hant` | △ **僅作語域對照** | FLORES-200 新聞文本主題分類，實測為真實繁體。**⛔ 致命風險**：test 僅 **24 筆**、train 僅 **172 筆**；預設 `samples_per_label=8` 在 172 筆上抽不滿；24 筆無法算 ECE。且 v1 的 `eval_splits=["train","validation","test"]` 會**把 train 當評估集**，協定不尋常（v2 已修為 `["test"]`）。**不建議作主要資料集** |
| **D. YueOpenriceReviewClassification** | `izhx/yue-openrice-review` / `mteb/yue_openrice_review` | △ **不建議** | `yue-Hant` 是**粵語**繁體（「好食」「唔」「嘅」），非台灣中文；`eval_splits=["test"]` 單一 split 且程式碼做分層抽樣（`samples_per_label=32`）。**台灣讀者會誤以為它是中文任務**——這正是「憑印象用錯子集」的陷阱 |
| **E. AmazonReviewsClassification (zh)** | `mteb/AmazonReviewsClassification` / `zh` | ❌ | `zh` 明載 `cmn-Hans`（**簡體**）。可作簡體對照組。**注意**：使用者提到的 `mteb/amazon_reviews_multi` 確實存在（210000 筆），但 MTEB 任務定義指向的是 `mteb/AmazonReviewsClassification`，**兩者是不同 repo** |
| **F. 全部 CMTEB 中文任務** | `zho/cmteb_classification.py` | ❌ | **13 個類別全部標記 `cmn-Hans`**，無一例外。且 `JDReview.v2`（388 筆）、`OnlineShopping`（99 筆）樣本過小 |
| **G. MTOP 系列** | `mteb/MTOPIntentClassification`、`MTOPDomainClassification` | ❌ **無中文** | `_LANGUAGES = {en, de, es, fr, hi, th}`——**完全不含中文**。使用者原本的假設**不成立**，記錄為否定結果 |
| **H. SIBFLEURS** | `mteb/sib-fleurs-multilingual-mini` | ❌ **音訊** | `EVAL_LANGS_MAP` **確實含 `"zho_Hant"`（Chinese (Traditional)）**，乍看是候選；但 metadata 明載 `modalities=["audio"]`、`input_column_name="audio"`、`is_cross_validation=True`。**文字嵌入無法使用**（掃描時曾被 regex 誤命中，特此記錄） |

---

## 四、候選子集的維度與長度需求

> 本節回應「維度與長度需求」的補充要求。

### 4.1 詞彙定義

- **「建議維度」**：此子集要達到「可與 leaderboard 比較」所需的最小嵌入維度。
  MTEB 分類任務本身**不強制**任何維度——任何 `EncoderProtocol` 模型都能跑。
  因此下表「建議維度」指的是**本專案的實驗設計需求**，不是 MTEB 的硬性要求。
- **「句子長度分佈」**：來自 MTEB 自動產生的描述統計（S10），
  為**全庫平均**（跨 51 語言），非 zh-TW 專屬。
- **「是否需要前綴」**：模型端的**硬性要求**，若不一致則比較不公平。

### 4.2 維度與長度需求表

| 子集 | 建議維度（本專案） | 句子長度分佈 | 是否需要前綴 |
|---|---|---|---|
| **MassiveIntentClassification (zh-TW)** | **256**（與 potion 原生維度一致，主實驗）<br>另跑 64 / 128 做**維度消融** | 全庫 avg **34.5** 字元，max 495，min 1（S10）<br>→ 極短文本，適合靜態嵌入 | **三方皆不需要**<br>（見 §4.3） |
| **MassiveScenarioClassification (zh-TW)** | 同上（同語料） | 同上（同語料） | 三方皆不需要 |
| **SIB200Classification (zho-Hant)** | 256（無 leaderboard 可較，僅內部比較） | `TODO(核實)`——S10 的 README 未提供 zho_Hant 專屬長度統計 | 三方皆不需要 |
| **AmazonReviewsClassification (zh，簡體對照)** | 256 | 全庫 avg 未查；原文截斷至 **2000 字元**、至少 20 字元（S8 資料集說明） | 三方皆不需要 |

### 4.3 前綴要求——**本節是本調查最重要的公平性發現**

| 模型 | 維度 | 最大長度 | **前綴要求** | 來源 |
|---|---|---|---|---|
| **`minishlab/potion-multilingual-128M`**（我方前端） | **256**（固定） | `seq_length: 1000000`（理論無限） | **不需要** | `F10` §2.9（本地文件） |
| **`hotchpotch/bekko-embedding-v1-a25m`**（主要對手） | **384**（可 Matryoshka 截 256/128/64） | **8192** | **不需要**（`include_prompt: true` 是池化開關，非任務前綴） | S13、S14 |
| **`intfloat/multilingual-e5-small`**（對手的對照基準） | **384** | **512** | **需要 `query:` / `passage:` 前綴** | S12 |

**關鍵結論**：

1. **`bekko` 與 `potion` 都不需要前綴** → 兩者的比較**公平**，可直接對比。
2. **`multilingual-e5-small` 需要前綴** → 若把它放進同一張表，
   **必須明確標註前綴策略**（分類任務通常用 `query:`，因為文本是被編碼成要被分類的「查詢」）。
   若忘了加前綴，e5 的分數會被**人為壓低**，結論會失真。
3. **`e5-small` 的 512 token 上限 vs `bekko` 的 8192**：
   MASSIVE 的文本極短（avg 34.5 字元），**兩者都遠未觸頂**，此差異在本子集上不構成影響。
4. **維度對齊問題**：
   - `potion` 固定 256 維 → **無法**做維度消融（除非自己套 PCA，但那會混入額外變因）
   - `bekko` 可 Matryoshka 截到 256 → **與 potion 同維度可比**
   - **建議**：主實驗用 **256 維對 256 維**（bekko 截斷後），
     維度消融則**只在 bekko 內部**做（384 → 256 → 128 → 64），
     並誠實說明「potion 無法參與維度消融」。

> **待補**：`bekko` 截到 256 的「損失只有 −1.35%」這個數字來自使用者提供的模型卡，
> **本調查未獨立核實**（S13 的 HF API 回傳 `model-index: null`，無 MTEB 官方分數）。
> 標為 `TODO(核實)`。**特別注意**：`bekko` 沒有 `model-index`，
> 所以**它沒有任何 MTEB 官方認證分數**——這對「王者對決」的敘事是好消息（我們可以自己跑），
> 但壞消息是**沒有現成 baseline 可引用**。

---

## 五、評估協定

> 本節全部依據 **S5**：`mteb/abstasks/classification.py` 的實際原始碼，非二手描述。

### 5.1 凍結嵌入 + 線性探針：MTEB 的官方定義

MTEB 的分類協定**就是**「凍結嵌入 + 線性探針」，原始碼明文：

```python
class AbsTaskClassification(AbsTask):
    evaluator_model: SklearnModelProtocol = LogisticRegression(max_iter=100)
    samples_per_label: int = 8      # ← 關鍵！
    n_experiments: int = 10         # ← 關鍵！
    train_split: str = "train"
    is_cross_validation: bool = False
```

流程（`_evaluate_subset`）：

1. **載入 `train` split 與評估 split**（預設 `test`，實際由各任務 `eval_splits` 決定）
2. **欠採樣**：從 `train` 中**每個標籤只抽 `samples_per_label` 筆**（多數分類任務覆寫為 **32**）
3. **凍結編碼**：`model.encode(...)` 對 train 與 test 各編碼一次（**模型權重完全不更新**）
4. **訓練 `LogisticRegression(max_iter=100)`** 於凍結嵌入之上
5. **重複 `n_experiments`（預設 10）次**，每次用不同種子重新欠採樣
6. **回報 10 次實驗的平均**（`_calculate_avg_scores`）

> **對本專案的直接影響（務必注意）**：MTEB 的探針**只訓練 `32 × 類別數` 筆樣本**，
> 不是整個 train split。以 MASSIVE zh-TW intent（59 類）為例，
> 每 experiment 只用 **32 × 59 = 1888** 筆（若用預設 8 則僅 **472** 筆）。
> 我們的 QBN 實驗若用完整 11514 筆訓練，
> **與 MTEB leaderboard 的分數不可直接相比**。這一點必須在論文中明講。

### 5.2 固定 split？要不要自己切驗證集？

**答案：MTEB 用資料集**原生**的 train/test split，不自己切。**

| 情境 | MTEB 的行為（原始碼依據） |
|---|---|
| 資料集有 `train` + `test` | 直接使用，**不切驗證集** |
| 資料集有 `train` + `validation` + `test` | `eval_splits` 決定用哪些；MASSIVE 用 `["validation", "test"]` |
| 資料集**沒有** train split（如 `SIBFLEURS`、`yue_openrice`） | 設 `is_cross_validation = True` → 改用 **`KFold(n_splits=5)`** 在 `train_split` 上做交叉驗證 |

`_evaluate_subset_cross_validation` 有明確的防護：

```python
if self.train_split != hf_split:
    raise ValueError(
        f"Performing {self.n_splits}-fold cross validation, but the dataset has a "
        f"train (`{self.train_split}`) and test split (`{hf_split}`)! "
        f"Set `is_cross_validation` to False, and retry."
    )
```

**對本專案的建議**：
- **MASSIVE 有 `validation` split** → 我們的 temperature scaling 與超參選擇**直接用 validation**，
  **不要**從 test 切，這樣才能與 MTEB 協定對齊。
- **QBN 的容量掃描**（RQ1）需要自己的驗證曲線 → 用 `validation`（2033 筆），
  **test（2974 筆）留給最終報告**，避免資料洩漏。

### 5.3 指標定義——**這是「用錯指標結果就不可比」的關鍵**

`_calculate_scores` 的**完整**回報清單（原始碼逐字，已壓縮空白）：

```python
scores = ClassificationMetrics(
    accuracy           = accuracy_score(y_test, y_pred),
    f1                 = f1_score(y_test, y_pred, average="macro"),     # macro
    f1_weighted        = f1_score(y_test, y_pred, average="weighted"),  # weighted
    precision          = precision_score(y_test, y_pred, average="macro"),
    precision_weighted = precision_score(y_test, y_pred, average="weighted"),
    recall             = recall_score(y_test, y_pred, average="macro"),
    recall_weighted    = recall_score(y_test, y_pred, average="weighted"),
    ap = None, ap_weighted = None,          # 僅二元分類才填
)
if len(np.unique(y_test)) == 2:             # 二元分類才補上
    scores["ap"]          = average_precision_score(y_test, y_pred, average="macro")
    scores["ap_weighted"] = average_precision_score(y_test, y_pred, average="weighted")
```

**逐項確認**：

| 指標 | 平均方式 | 適用條件 | main_score？ |
|---|---|---|---|
| `accuracy` | 不分類別，直接正確率 | **所有任務** | ✅ **`main_score="accuracy"`（本調查所有候選皆是）** |
| `f1` | **macro** | 所有任務 | ❌ 但 leaderboard 常並列 |
| `f1_weighted` | **weighted**（按支持度加權） | 所有任務 | ❌ |
| `precision` / `recall` | **macro** | 所有任務 | ❌ |
| `precision_weighted` / `recall_weighted` | **weighted** | 所有任務 | ❌ |
| `ap` / `ap_weighted` | macro / weighted | **僅二元分類**（`len(unique(y_test)) == 2`） | ❌ |

> **⚠️ 重要陷阱**：MTEB 的分類任務**一律回報 macro-F1 與 weighted-F1 兩個版本**。
> 引用時**必須指明是哪一個**。以 MASSIVE zh-TW intent（極不平衡）為例，
> 兩者可能相差數個百分點。
> `F10` 文件提醒的「Mean(Task)、Mean(TaskType)、STS 不可直接相减」是**聚合層級**的陷阱；
> 這裡是**指標層級**的同類陷阱——**務必在論文中寫明「我們報的是 macro-F1 還是 weighted-F1」**。

### 5.4 多語言任務的聚合方式

對 `MassiveIntentClassification` 這類**多 subset 任務**，`evaluate()` 對
**每個 hf_subset（每個語言）分別計分**，然後 `_add_main_score` 取平均。
因此 leaderboard 上的 `MassiveIntentClassification` 分數是 **51 語言的平均**，
**不是** `zh-TW` 的分數。

**引用 zh-TW 分數時必須指明 config**，例如
`MassiveIntentClassification (zh-TW)`，而非 `MassiveIntentClassification`。

### 5.5 `samples_per_label` 差異表（影響可比性）

| 任務 | `samples_per_label` | `n_experiments` | `eval_splits` | 來源 |
|---|---|---|---|---|
| MassiveIntentClassification | 8（**預設，未覆寫**） | 10（預設） | `["validation", "test"]` | S6 |
| MassiveScenarioClassification | 8（**預設，未覆寫**） | 10（預設） | `["validation", "test"]` | S6 |
| SIB200Classification | 8（**預設，未覆寫**） | 10（預設） | `["train", "validation", "test"]` | S6 |
| SIB200Classification.v2 | 8（**預設，未覆寫**） | 10（預設） | `["test"]` | S6 |
| TNews / TNews.v2 | **32** | 10 | `["validation"]` | S6 |
| IFlyTek / IFlyTek.v2 | **32** | **5** | `["validation"]` | S6 |
| JDReview / JDReview.v2 | **32** | 10 | `["test"]` | S6 |
| OnlineShopping | **32** | 10 | `["test"]` | S6 |
| Waimai / Waimai.v2 | **32** | 10 | `["test"]` | S6 |
| MultilingualSentiment / .v2 | **32** | 10 | `["validation", "test"]` | S6 |
| YueOpenriceReviewClassification(.v2) | **32** | 10 | `["test"]` | S6 |

> **MASSIVE 用預設的 `samples_per_label = 8`，而 CMTEB 用 32。**
> 這代表 MTEB 對 MASSIVE 的探針訓練量**更少**（8 × 59 = 472 筆），
> 分數偏保守。若我們用 32，分數會**高於** leaderboard——這不是作弊，
> 但**必須在論文中說明差異**，否則會被質疑。

---

## 六、建議的實驗子集

### 6.1 推薦組合（三個子集，覆蓋不同控制變數）

| 角色 | 任務 | config | 為什麼 |
|---|---|---|---|
| **主實驗** | `MassiveIntentClassification` | **`zh-TW`** | 唯一「原生繁體 + 大樣本 + 有 validation」的組合；59 類讓 5 qubit 的容量瓶頸明顯 |
| **難度對照** | `MassiveScenarioClassification` | **`zh-TW`** | 同一語料的 18 類版本；與主實驗**配對比較**，隔離「類別數」這個變數 |
| **繁簡消融** | `MassiveIntentClassification` | **`zh-CN`** | 同語料、同標籤、同樣本數的簡體版；可直接量測「繁體輸入是否造成前端退化」 |

**這三個子集共用同一份底層語料（MASSIVE），這是優點也是限制**：
- **優點**：完美控制語料變數，任何差異都可歸因於「類別數」「文字系統」或「電路容量」
- **限制**：**不能**宣稱「在多個獨立資料集上驗證」
  → 對策：若時間允許，加跑 `SIB200Classification (zho-Hant)` 作為**語域泛化**的附帶觀察
  （但必須標明其 24 筆 test 不足以支撐任何統計結論）

### 6.2 為什麼不選其他

| 候選 | 排除理由 |
|---|---|
| `AmazonReviewsClassification (zh)` | `cmn-Hans` 簡體，無法回答繁體問題 |
| 全部 CMTEB 中文任務 | 13 個類別**全部** `cmn-Hans`；且 `JDReview`(388)、`OnlineShopping`(99) 樣本過小 |
| `MTOPIntent/Domain` | **完全沒有中文**（使用者原本的假設不成立） |
| `YueOpenriceReviewClassification` | 粵語，非台灣中文；且單一 test split |
| `SIBFLEURS` | **音訊**任務，文字嵌入無法使用 |
| `SIB200Classification` 作為主實驗 | test 僅 24 筆，無法做 ECE；v1 還把 train 當評估集 |

### 6.3 風險登記

| # | 風險 | 嚴重度 | 緩解 |
|---|---|---|---|
| R1 | MASSIVE 繁體分數顯著低於簡體（e5：62.54 vs 68.24） | 中 | 這**本身就是發現**，寫成「繁簡落差不只存在於大模型」 |
| R2 | 類別極不平衡（`general_greet` 51 筆 vs `calendar_set` 10659 筆） | **高** | 永遠並列 accuracy 與 **macro-F1**；考慮報 balanced accuracy |
| R3 | MTEB revision 與 leaderboard 不一致 | 中 | 引用分數必附 revision；我們自己跑時固定 `revision=` |
| R4 | `samples_per_label` 差異（MASSIVE 8 vs CMTEB 32） | 中 | 論文明示我們的探針訓練量；必要時兩種都跑 |
| R5 | MASSIVE 是**機器翻譯**語料（`sample_creation="human-translated and localized"`） | 低 | 誠實標註；但它是**人工翻譯＋在地化**，優於純 MT |
| R6 | 同一語料三個子集 → 無法宣稱跨資料集泛化 | 中 | 明確寫成「controlled ablation on a single corpus」 |
| R7 | `bekko` 無 MTEB 官方分數 | 低 | 自己跑；但**不能引用現成分數** |
| R8 | `zho-Hant` / `cmo-Hant` 標籤來自 MTEB 維護者 | 低 | 已用 `first-rows` 實地驗證文本，非僅信標籤 |

### 6.4 具體落地步驟（給實作組）

```python
from datasets import load_dataset
ds    = load_dataset("mteb/amazon_massive_intent", "zh-TW")  # 繁體
ds_cn = load_dataset("mteb/amazon_massive_intent", "zh-CN")  # 簡體對照
# 各為 train 11514 / validation 2033 / test 2974；欄位 text(str) + label(int)，共 5 欄

from model2vec import StaticModel
model = StaticModel.from_pretrained("minishlab/potion-multilingual-128M")
X = model.encode(ds["train"]["text"])          # (11514, 256)
# 線性探針請模仿 MTEB：LogisticRegression(max_iter=100)
# 注意 MTEB 對 MASSIVE 只抽 samples_per_label=8；我們若用全部 11514 必須說明差異
```

> `TODO(核實)`：`load_dataset` 的 config 名稱是否為 `"zh-TW"`（含連字號）需實測。
> **本任務僅調查，未下載任何資料**（依硬規則 5）。

---

## 七、待核實

本節列出**查不到**或**未獨立驗證**的項目，並說明**已搜尋什麼**。

| # | 項目 | 我搜了什麼 | 狀態 |
|---|---|---|---|
| T1 | `SIB200Classification.v2` 的 `zho_Hant` 逐 split 樣本數 | `datasets-server.huggingface.co/size?dataset=mteb/sib200.v2&config=zho_Hant` → **HTTP 404**；`splits` API → 亦可取得 repo 但 config 查詢失敗 | `TODO(核實)` |
| T2 | `mteb/waimai`（Waimai.v2 的 HF 路徑）是否真的存在 | `size`、`splits` API 皆 404；但 `C-MTEB/waimai-classification`（v1 路徑）**正常**（train 8000 / test 1000） | `TODO(核實)`——可能是 repo 未建立或已改名 |
| T3 | `mteb/MTOPIntentClassification` / `MTOPDomainClassification` 的 HF repo 是否存在 | `datasets-server` splits API → **404**；`mteb/mtop_intent` 亦 404 | `TODO(核實)`。**語言清單已從原始碼確認無中文**，此項僅影響可執行性 |
| T4 | `MultilingualSentimentClassification`（multilingual 版）的 HF repo id | 僅知檔名 `multilingual_sentiment_classification.py`，**未展開內容** | `TODO(核實)` |
| T5 | `LanguageClassification`、`MInDS14` 的 split 與樣本數 | 僅從 S6 掃描得知含 `cmn-Hans` / `zh-CN` | `TODO(核實)` |
| T6 | MASSIVE zh-TW **subset 專屬**的描述統計（標籤分佈、長度） | S10 的 README 只有**全庫**統計（跨 51 語言）；無 zh-TW 專屬統計 | `TODO(核實)`——需自行 `load_dataset` 後 `.to_pandas().describe()` |
| T7 | `bekko` 的 Matryoshka「截 256 僅損 −1.35%」 | HF API 回傳 `model-index: null`（**無 MTEB 官方分數**） | `TODO(核實)`——來源為使用者提供的模型卡 |
| T8 | `bekko` 是否需要任務前綴 | 讀了 `config.json`、`1_Pooling/config.json`；**未讀 README**（模型卡） | 部分核實：`include_prompt: true` 僅為池化開關。**前綴要求需讀模型卡確認** |
| T9 | `e5-small` 在 Massive**Scenario** (zh-TW) 的分數 | S11 的 model-index 過長被截斷，只確認到 intent 與部分 scenario | `TODO(核實)` |
| T10 | MTEB 目前**確切版本號** | `pyproject.toml` 抓取後 `Select-String '^version'` **無輸出**（可能格式不同） | `TODO(核實)` |

### 已確認**不成立**的假設（重要，避免後人重複）

| 假設 | 實際 | 證據 |
|---|---|---|
| 「MTOP 含中文」 | **不成立**，只有 en/de/es/fr/hi/th | S6 |
| 「`zh` 標籤可能涵蓋繁體」 | **不成立**，`AmazonReviewsClassification` 的 `zh` 明載 `cmn-Hans` | S6 |
| 「`SIBFLEURS` 的 `zho_Hant` 可用」 | **不成立**，它是**音訊**任務 | S6 |
| 「MASSIVE 只有 `zh` 沒有 `zh-TW`」 | **不成立**，`zh-TW` 確實存在且是原生繁體 | S6、S7、S8、S9、S11 |

---

## 附錄 A：完整的中文相關任務清單（10 個檔案）

`S6` 掃描 281 個分類任務檔案，僅以下 10 個含中文語言標記：

| # | 檔案 | 任務類別 | 中文標籤 |
|---|---|---|---|
| 1 | `multilingual/amazon_reviews_classification.py` | AmazonReviewsClassification | `cmn-Hans` / `zh` |
| 2 | `multilingual/language_classification.py` | LanguageClassification | `cmn-Hans` |
| 3 | `multilingual/m_in_ds14.py` | MInDS14 | `zh-CN` |
| 4 | `multilingual/massive_intent_classification.py` | MassiveIntentClassification | `zh-CN` / **`zh-TW`** |
| 5 | `multilingual/massive_scenario_classification.py` | MassiveScenarioClassification | `zh-CN` / **`zh-TW`** |
| 6 | `multilingual/multi_hate_classification.py` | MultiHateClassification | `cmn-Hans` |
| 7 | `multilingual/multilingual_sentiment_classification.py` | MultilingualSentimentClassification | `cmn-Hans` |
| 8 | `multilingual/sib200_classification.py` | SIB200Classification、SIB200Classification.v2 | **`zho-Hant`**、`yue-Hant` |
| 9 | `zho/cmteb_classification.py` | TNews、IFlyTek、MultilingualSentiment、JDReview、OnlineShopping、Waimai（各含 .v2） | `cmn-Hans`（**全部簡體**） |
| 10 | `zho/yue_openrice_review_classification.py` | YueOpenriceReviewClassification、.v2 | `yue-Hant`（粵語） |

> **掃描盲點揭露**：regex 為 `cmn-Hant|cmn-Hans|zh-TW|zh-CN|"zh"|cmn\b|yue-Hant`，
> **未**涵蓋純 `zho-Hant`。`sib200_classification.py` 是因 `yue-Hant` 才被命中，故未遺漏；
> 但推論上仍有極小機率遺漏「只寫 `zho-Hant` 且不含其他關鍵字」的檔案。
> 已用 `sibfleurs.py` 反例驗證此盲點確實存在（它含 `zho_Hant`，只因另一輪掃到 `zho` 才發現）。
> **保守結論：含繁中的文字分類任務只有 MASSIVE 與 SIB200 兩個家族。**

## 附錄 B：本調查使用的完整指令（可重現）

```powershell
# 1. 列出所有分類任務檔案
$r = Invoke-RestMethod "https://api.github.com/repos/embeddings-benchmark/mteb/git/trees/main?recursive=1"
$r.tree | Where-Object { $_.path -like "mteb/tasks/classification/*" -and $_.type -eq "blob" } | ForEach-Object { $_.path }

# 2. 掃描含中文的任務：逐檔抓 raw.githubusercontent.com，regex 比對語言標記

# 3. 確認 split 與樣本數
Invoke-RestMethod "https://datasets-server.huggingface.co/splits?dataset=mteb%2Famazon_massive_intent"
Invoke-RestMethod "https://datasets-server.huggingface.co/size?dataset=mteb%2Famazon_massive_intent&config=zh-TW"

# 4. 實地檢視文本（繁簡判定）
Invoke-RestMethod "https://datasets-server.huggingface.co/first-rows?dataset=mteb%2Famazon_massive_intent&config=zh-TW&split=test"
```

> *本調查為純文獻與 API 調查，未執行任何訓練、未下載任何模型權重或資料集。*
