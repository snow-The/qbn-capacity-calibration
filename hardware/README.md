# 真機路線：Quafu（BAQIS 超導雲）

> 決策（2026-09-19，作者）：真機走 **Quafu**。理由：免費、只綁信箱、每月 1000 次啟動額度、
> 且能一次使用上百個真實 qubit。SDK：`pyquafu`（https://github.com/ScQ-Cloud/pyquafu）。

## 一、環境現況（已驗證）

| 項目 | 值 |
|---|---|
| 套件 | `pyquafu 0.4.5`（Apache-2.0） |
| **import 名** | **`quafu`**（⚠️ 發行名是 `pyquafu`，**import 要用 `quafu`**） |
| 安裝位置 | `/root/quafu/.venv`（**獨立 venv**） |
| Python / numpy | 3.12.3 / **1.26.4** |
| 為什麼獨立 | `pyquafu` 釘 **`numpy<2.0.0`**，與 q01（numpy 2.5.3）**衝突** |
| 輪子 | 有 cp39–cp313、win_amd64／manylinux／macOS ✓ |

## 二、API 完備度（實測）

| 能力 | 物件 | 對我們的用途 |
|---|---|---|
| **OpenQASM 匯入** | `QuantumCircuit.from_openqasm` | ★ 交換格式：q01 端匯出 QASM，不必在 q01 裝 pyquafu |
| **本地模擬** | `quafu.simulate` | ★ **先用本地驗證，不浪費真機額度** |
| **轉譯** | `quafu.transpiler` | 映射到目標晶片的耦合圖 |
| 閘集 | `h cx cy cz cp cs ct iswap fredkin mcx mcy mcz dagger add_controls`… | 我們的 ansatz（RY/RZ/CX）完整覆蓋 |
| 提交 | `Task`、`User`、`ExecResult` | 真機任務與結果 |
| 其他子模組 | `qfasm, synthesis, visualisation, dagcircuits, algorithms` | 備用 |

## 三、整合架構（沿用既有的 JSON 交換模式）

```
q01（numpy≥2，測過的 IR）
        │  匯出 QASM／JSON（純文字，無新依賴）
        ▼
/root/quafu/.venv（Python 3.12 + numpy 1.26）
        ├─ QuantumCircuit.from_openqasm
        ├─ quafu.simulate          ← 先在本地驗證（免費）
        ├─ quafu.transpiler        ← 映射到目標晶片
        └─ Task → 真機             ← 最後才花額度
                    │ counts.json
                    ▼
        我們的 ECE／溫度縮放／盲點分析管線（專案最強的一段）
```

## 四、論文影響（RQ3）

現在論文最弱的一點是「全部結果都可古典模擬」。有真機之後應改為：

**RQ3：不確定性與校準分析是否轉移到真機？**

- 用 QBN 輸出層（4–8 qubit）在真機上跑分類，取 counts
- 套上既有的 ECE／溫度縮放／盲點分析（**這是專案最獨特的一段**）
- 與**黃金向量**（CUDA-Q 精確模擬）逐項對照 ⇒ 直接量出「真機 vs 模擬」
- 加 readout error mitigation（真機論文標準配備）

⚠️ 仍**不主張量子優勢**（4–8 qubit 依然可古典模擬）；
但貢獻從「模擬研究」升級為「**在真機上端到端驗證的管線 ＋ 雜訊特性刻畫**」。

## 五、待辦（P5）

1. **重置 Quafu token**（舊的已被服務端拒絕；新 token 寫進 `~/.dsh/quafu.token`，**不進聊天、不進 git**）
2. 用 token 列後端 → 記錄晶片規格（qubit 數、耦合圖、basis gates、讀出錯誤率）
3. q01 端：**IR → QASM 匯出**（純 Python，零新依賴）
4. QASM → quafu → **本地 simulate** → 與黃金向量對帳（**先不碰真機**）
5. 用 `transpiler` 映射到目標晶片，再本地模擬確認等價
6. 真機試跑 1–2 個任務（驗證 token、shots 參數、結果解析）
7. 真機結果接進校準分析管線 → RQ3

## 六、安全約定

- token 只從 `~/.dsh/quafu.token` 讀取，**永不回顯**（只印長度／遮罩）
- 不寫進任何 git 追蹤的檔案、不寫進 settings.yaml、不貼進聊天

---

## 七、不需要 token 的部分：已完成並驗證（2026-09-19）

### 7.1 q01 端：IR → OpenQASM 2.0

`packages/q01/tools/hardware/qasm_export.py`（純 Python、零新依賴）。
閘集刻意限定在硬體實驗所需：`h x y z s sdg t tdg sx rx ry rz`、單控制 X（`cx`）、
雙控制 X（`ccx`）；**多控制旋轉不匯出**（QASM 2.0 沒有標準閘）→ 明確報錯，不近似。

### 7.2 交換格式先用第三方驗證（不碰 quafu）

`verify_qasm_via_qiskit.py`：IR → QASM → `qiskit.qasm2.loads` → `Statevector` → 比黃金向量。

| 案例 | QASM 行數 | max\|ΔP\| |
|---|---|---|
| `bell` | 5 | **0.000e+00** |
| `qbn5_book` | 23 | **3.469e-17** |
| `qbn5_depth2` | 38 | **1.110e-16** |
| `entangle_then_rotate` | 6 | **0.000e+00** |
| `mcry3` | — | 正確 SKIP（多控制 RY 非標準 QASM 2.0） |

**這步的價值**：把「QASM 寫錯了」與「真機 SDK 收不收」兩個問題分開；
之後 quafu 端若有問題，一定是 SDK 側。

### 7.3 quafu 端：同一份 QASM 餵 `quafu.simulate`（本地、免費、不耗額度）

`verify_qasm_via_quafu.py`（跑在 `/root/quafu/.venv`）。API 實測：

- `QuantumCircuit(qnum, cnum=None)`；**`from_openqasm(text)` 是實例方法**（不是 classmethod）
- `simulate(qc, psi=..., simulator='statevector', shots=0, use_gpu=False, use_custatevec=False) -> SimuResult`
  ⇒ `shots=0` + `simulator='statevector'` 取得精確振幅

### 7.4 ★ L0 公約：**quafu 是 big-endian（q0 = MSB）**

| 案例 | 直接比對 | 位元反轉後 |
|---|---|---|
| `bell` | 0.000e+00 | 0.000e+00（對稱，判不出來） |
| `qbn5_book` | 5.575e-02 | **4.441e-16** ✅ |
| `qbn5_depth2` | 1.306e-01 | **2.776e-16** ✅ |
| `entangle_then_rotate` | 1.097e-01 | **0.000e+00** ✅ |

**⇒ quafu 的狀態索引是 big-endian，與 CUDA-Q／Qiskit／PennyLane（little-endian）相反。**
反轉後最差 **4.44e-16**（判準 1e-10）。

> 有趣的巧合：quafu 的順序與 **q01 的內部表示**一致（q01 對外才轉成 little-endian）。
> 真機結果接回來時，**位元順序轉換一律走 `bitorder.py`**（全專案唯一置換處）。

### 7.5 現在的狀態

| 步驟 | 狀態 |
|---|---|
| q01 端 IR → QASM | ✅ 完成並驗證（經 Qiskit，≤1.1e-16） |
| quafu 端收 QASM + 本地模擬 | ✅ 完成並驗證（反轉後 ≤4.4e-16） |
| L0 公約 | ✅ 定案（big-endian） |
| 列後端／晶片規格 | ⏸ **需要 token** |
| 真機試跑 | ⏸ 需要 token（先用 1–2 個任務驗證流程） |

**⇒ token 一到就能直接送：整條路（QASM → quafu → 模擬對帳）已經在本地跑通。**

---

## 八、後端清單實測（token 生效，2026-09-19）

`User(api_token=...)` → `get_available_backends()`，**共 16 個後端**：

| 名稱 | qubits | 狀態 | 備註 |
|---|---|---|---|
| **ScQ-P5** | **5** | **Online** | 我們的主電路規模（5 qubit） |
| **Baihua（百花）** | **119** | **Online** | ★ 真機、上百 qubit |
| ScQ-Sim10 | 10 | Online | 官方模擬器 |
| ScQ-P10 | 10 | Offline | |
| ScQ-P21 | 11 | Offline | |
| ScQ-P102 | 102 | Obsolete | |
| Baiwang | 136 | Obsolete | |
| Miaofeng | 108 | Obsolete | |
| Dongling | 105 | Offline | |
| Haituo | 105 | Offline | |
| Yunmeng | 156 | Obsolete | |
| Xiang | 35 | Obsolete | |
| ScQ-P3 / ScQ-TEST | 3 / 3 | Offline | |
| ScQ-Sim | 2 | Obsolete | |

**⇒ 之前「Quafu 只有 5 qubit」的判斷不完整：`Baihua` 是 119 qubit 且在線。**
（「Obsolete」多半是退役機，但代表歷史上有過；離線不代表永久不可用。）

### 8.1 pyquafu 正確用法（踩過的三個坑）

```python
from quafu import User, Task
u = User(api_token=token)        # ★ 直接帶入即可；不要用 User()（它會去讀 ~/.quafu/api）
b = u.get_available_backends()   # 回 {名稱: Backend}
```

- ❌ `User()` 無參 → `UserError: Please first save api token`（它不會自己找我們的 token 檔）
- ❌ `User.save_apitoken(token)` → `AttributeError: 'str' object has no attribute 'token_dir'`（它是實例方法）
- ❌ `Task(api_token=...)` → `Task` 要的是 **`user=`**
- ✅ `User(api_token=token)` **不落地任何檔案**（對保密更好）

### 8.2 Backend 物件可用的資訊

`name`、`qubit_num`、`qv`、`status`、`system_id`、`task_in_queue`、
**`get_chip_info()`**、**`get_valid_gates()`** ← 下一步要用這兩個取耦合圖與 basis gates。

### 8.3 額度（作者確認）

**1000 次／月，計費單位是「任務數」不是 shots** ⇒ 每次提交要盡量把 shots 用滿，
而且**本地模擬先行**（`quafu.simulate`）是必須的，別把額度浪費在 debug 上。

作者另有 N 個信箱與 IP ⇒ 額度可橫向擴充（但仍以省著用為原則）。

### 8.4 閘集與可用性實測（2026-09-19）

| 後端 | status | 佇列 | 有效閘（節錄） |
|---|---|---|---|
| ScQ-P5 | Online | 721 | `cx cz rx ry rz x y z h sx sy swap cy cnot id barrier` |
| Baihua | Online | 475 | `cx cz rx ry rz x y z h delay barrier`（**無 `sx/sy/swap`**）—— ⛔ **無權限，送不出去** |
| ScQ-Sim10 | Online | 0 | 官方模擬器（可送，見 §8.6） |
| Baiwang / ScQ-P102 / Yunmeng / Xiang | Obsolete | 有數字 | 仍可查詢，但**不應視為可用** |

**⇒ 我們的 ansatz 只需要 `ry/rz/cx`；但「閘集支援」不等於「有權限」。**

★ **實測（2026-09-19）：Baihua 送不出去。** 閘集查詢、狀態查詢都正常（`Online`、119 qubit），
但 `send()` 被伺服器擋下：

```
quafu.exceptions.user_error.UserError: 'Sorry, you do not have permission to use this chip.'
```

⇒ **API 列得出來 ≠ 能送任務**（這正是使用者「網頁上沒看到 Baihua」的原因）。
這個拒絕**不消耗額度**（伺服器端就擋掉），所以「送一次看錯誤訊息」是**免費**的權限探測法。
**目前確認唯一可用的真機是 ScQ-P5。**

### 8.5 API 事實（pyquafu 0.4.5 實測）

- `User(api_token=tok)` → `get_available_backends()`：回 `{名稱: Backend}`
- `Backend`：`name` / `qubit_num` / `qv` / `status` / `task_in_queue` / `get_valid_gates()`
  （`get_chip_info()` 是本地方法，內部再建 `User()` 所以會失敗；耦合圖要用別的路徑）
- `Task(user=u)` → `.config(backend=..., shots=..., compile=True)` → `.run(qc)`
- ★ **`run()` 是同步的**：原始碼 `run(qc)` = `send(qc, wait=True)`，回傳的 `ExecResult`
  **已經帶著結果**（`.counts` / `.probabilities` / `.logicalq_res`），不需要再輪詢。
- ★ **task id 在 `ExecResult.taskid`，不在 `Task` 上**：`Task` 實例**沒有** `taskid`
  屬性（`t.taskid` 取不到）；正確位置是 `ExecResult.taskid`（例：`8E04BDA01432EDCF`）。
  用錯位置會變成 `retrieve(None)` → 伺服器回錯誤 JSON → `ExecResult` 建構時
  `KeyError: 'task_id'`，看起來像「任務沒成立」，其實結果早就在手上。
- **長時間排隊的正確做法：非同步送單**
  `res = t.send(qc, wait=False)` → 立刻拿到 `res.taskid`（**先存檔再等待**）→
  之後 `t.retrieve(tid)` 輪詢。就算連線斷了，任務也不會丟。
- `Task.retrieve(taskid: str)` 是**查詢**（**不耗額度**）；`Task.get_history()` 目前回 `{}`
- **權限不足會拋 `UserError`，在 `send()` 階段就被伺服器擋下，且不消耗額度**；
  額度只在**任務真的成立**時才計。（Baihua 就是這樣被擋的，見 §8.4）
- `compile=True` 會做映射編譯：`transpiled_openqasm` 可能配置**比邏輯位更多的實體位**
  （`qbn5_book` 的 5 個邏輯位在 Sim10 上被放到 `qreg q[10]`），並附
  `measures = {實體位: clbit}`；回傳的 `counts` 鍵是 **creg 順序**的字串。

### 8.6 ScQ-Sim10：第一個成功送出的任務（2026-09-19）

| 項目 | 值 |
|---|---|
| taskid | `8E04BDA01432EDCF`（2 000 shots）、`8E05353008B850AF`（20 000 shots） |
| 後端 / shots | ScQ-Sim10 / 2 000 與 20 000 |
| 電路 | `qbn5_book`（5 qubit、20 閘） |
| 回傳鍵數 | 25（2 000 shots）／29（20 000 shots） |

**對帳黃金向量**（`max|ΔP|`）：

| 位元序處理 | 2 000 shots | 20 000 shots |
|---|---|---|
| **反轉一次（映到我們的索引）** | **6.04e-03** | **1.76e-03** ✅ |
| 不反轉 | 5.78e-02 | 5.71e-02 |

- top-3 狀態與黃金向量**完全一致**：golden `[0, 17, 29]` ↔ quafu `[0, 17, 29]`。
- 這同時**再確認了大端序公約**（§7.4）：只有「反轉一次」的映射才對得上。

#### 8.6.1 一個被實驗否證的假設（方法論示範）

2 000 shots 那次跑完，$\chi^2 = 55.5/\mathrm{df}{=}31$（$p \approx 7\times10^{-4}$）、
32 個態裡有 2 個 $|z| > 3$——**單看這個結果，不能宣稱「只是取樣漲落」**。
其中 33.7 的 $\chi^2$ 來自 3 個期望值 $< 1.5$ 的罕見態（`idx14` 期望 0.33、觀測 3），
這個模式（罕見態系統性偏多）看起來像**噪聲底**。

於是提出可否證的預測，並用 10 倍 shots 檢驗：

| shots | max\|ΔP\| | max\|z\| | $n(\|z\|>3)$ | $\chi^2/\mathrm{df}$ |
|---|---|---|---|---|
| 2 000 | 6.04e-03 | 4.66 | 2 | 55.5 / 31 |
| **20 000** | **1.76e-03** | **2.35** | **0** | **33.5 / 31** |

- 若是**噪聲底**（系統性）：偏差量固定，$z$ 應隨 $\sqrt{N}$ **變大**（約 3.2 倍）。
- 若是**取樣漲落**（統計性）：偏差量應隨 $1/\sqrt{N}$ **變小**（約 3.2 倍）。
- 實測：$6.04\times10^{-3} \to 1.76\times10^{-3}$（縮小 **3.4 倍**，$\sqrt{10} = 3.16$），
  $|z|_{\max}$ 由 4.66 降到 **2.35**（32 個標準常態的期望最大值約 2.2）。

**⇒ 假設被否證：ScQ-Sim10 是理想取樣器，2 000 shots 那次是罕見但正常的統計漲落。**

#### 8.6.2 轉譯也被獨立驗證過

把雲端回傳的 `transpiled_openqasm`（10 個實體位、63 閘、含 SWAP 分解）拿回來，
用 Qiskit 態向量**無噪聲**重算，再依 `measures = {6:0, 9:1, 5:2, 8:3, 7:4}` 邊際化：

| 比對 | max\|ΔP\| |
|---|---|
| 轉譯後電路（無噪聲）vs 黃金向量 | **8.88e-16** ✅ |
| 同一結果不反轉 | 5.58e-02 |

⇒ `compile=True` 的映射編譯是**忠實**的；§8.6.1 的偏差不可能來自轉譯。

- 證據檔：`hardware/runs/sim10_qbn5_book_2000.json`、`hardware/runs/sim10_qbn5_book_20000.json`

### 8.7 目前狀態

- ✅ 本地鏈路：IR → QASM → quafu 模擬 → 對帳（≤4.4e-16）
- ✅ token 生效、16 個後端可列、閘集可查
- ✅ **第一個任務成功送出並回收**（ScQ-Sim10，見 §8.6）
- 🔄 ScQ-P5 真機已送出（taskid 存於 `hardware/runs/scqp5_qbn5_book.taskid`），等待佇列
---

## 九、真機進度與替代路線（2026-09-21 更新）

### 9.1 ScQ-P5：仍在佇列，而且佇列沒有在前進

| 時間 | P5 佇列 | 我們的狀態 |
|---|---|---|
| 2026-09-20 15:02 / 15:08 / 15:13 | 733 | （尚未查） |
| 2026-09-21 02:43 | **735** | **In Queue** |

- taskid `8E04C01019B694A7`（2026-09-20 01:54 送出），約 25 小時後仍是 `In Queue`、`counts` 為空。
- 11.5 小時內佇列由 733 → 735（**增加** 2）——不是在消化。
- 輪詢本身**不耗額度**（`Task.retrieve` 是查詢），所以可以放心定期查。
- 證據：`runs/p5_queue_samples.jsonl`（每次查詢追加一行，含 `our_status`）。

**結論：等待不是策略。** 需要替代路線。

### 9.2 已完成：Quantum Inspire 送出前的全部準備（只差登入）

| 項目 | 狀態 |
|---|---|
| 獨立 venv | `/root/qi/.venv`（Python 3.12.3；qiskit 2.x 的 numpy 需求與 q01 不衝突） |
| SDK | `qiskit-quantuminspire 0.18.4` + `qiskit 2.3.1` + `qi-compute-api-client 0.63.0` |
| CLI | `qi`（由 `quantuminspire 4.0.0` 提供） |
| 登入 | ⏸ **`qi login`（互動式，需要帳號）** |
| 送出腳本 | `submit_qi.py`（已寫好，dry-run 通過） |

⚠️ **QI 2.0 的程式端入口不是 `import quantuminspire`。**
`quantuminspire 4.0.0` 現在提供的是 **CLI**；程式裡要用
`from qiskit_quantuminspire.qi_provider import QIProvider`。
`QIProvider()` 在未登入時會拋
`FileNotFoundError: No configuration file found. Please connect to Quantum Inspire using the CLI.`

**送出前的兩項離線驗證（都不需要帳號，已通過）：**

1. QASM 在 **qiskit 2.3.1**（QI 平台用的版本）下往返，最差 `max|ΔP| = 1.665e-16`
   （`qbn5_book` 3.469e-17、`qbn5_depth2` 1.665e-16、`bell` 與 `entangle_then_rotate` 皆 0）。
   這是用 `/root/qi/.venv` 的 python 重跑 `packages/q01/tools/hardware/verify_qasm_via_qiskit.py`。
2. `submit_qi.py --dry-run`：精確機率 vs 黃金向量 `1.388e-17`；另外用 20 萬 shots
   模擬計數再反推機率，`max|ΔP| = 7.53e-04` —— 這一步是在**先驗證位元序反轉沒寫反**，
   不必等真機回來才知道。

### 9.3 待辦：只需要一個動作

```bash
wsl -d QBN -u root -- bash -lc "/root/qi/.venv/bin/qi login"
```

登入後先列後端（要挑真機，不要 emulator）：

```bash
wsl -d QBN -u root -- bash -lc "cd /mnt/c/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration/hardware && /root/qi/.venv/bin/python submit_qi.py --list"
```

再送：

```bash
... submit_qi.py --shots 8192
```

結果寫到 `runs/qi_<case>_<shots>.json`，內含 counts 與與黃金向量的 `max|ΔP|`。

### 9.4 論文措辭已更正

論文結論原本寫「並經**真機鏈路**與官方模擬器驗證」——那會被讀成「已取得真機結果」，
但真機任務從未完成。已改為可查證的敘述：

> …並另外透過 Quafu 雲端 API 在官方模擬器上端到端驗證，
> 轉譯後電路與黃金向量一致到 $8.88 \times 10^{-16}$。

（書站台原本就是誠實的：〈三十分鐘全貌〉寫「真機執行列為未來工作」、
RQ3 寫「如果真機結果能取得」。）
### 9.5 ★ 真機結果（2026-09-21 03:28，Tuna-17，8192 shots）

**拿到了。** 這是本專案第一個真機資料點。

| 項目 | 值 |
|---|---|
| 後端 | **Tuna-17**（17 qubit 超導，QuTech 真機，`is_hardware=True`） |
| 電路 | `qbn5_book`（5 logical qubit；轉譯後深度 9、21 閘） |
| shots | 8192（32 個鍵全部回來） |
| 證據 | `runs/qi_qbn5_book_Tuna-17_8192_20260921-032832.json` |

**與理想模擬（CUDA-Q 黃金向量）的差距：**

| 指標 | 值 |
|---|---|
| max abs(dP) | **1.279e-01** |
| 取樣雜訊基準（1/sqrt(N)） | 1.10e-02 |
| 訊噪比 | **約 11.6 倍** |
| TV 距離 | 0.2623 |
| 保真度（Bhattacharyya 平方） | 0.7851 |
| max abs(z) | 404 |
| abs(z)>3 的態 | **26 / 32** |
| chi2 | **210282 / df=31** |

**這不是統計漲落，是系統性偏差。** 六個主要態**全部**掉了機率：

| idx | 理想 | 觀測 | 差 |
|---|---|---|---|
| 0 | 0.6335 | 0.5056 | -0.1279 |
| 17 | 0.1192 | 0.0924 | -0.0268 |
| 29 | 0.0590 | 0.0052 | -0.0537 |
| 16 | 0.0389 | 0.0197 | -0.0192 |
| 25 | 0.0232 | 0.0049 | -0.0183 |

機率一致地從主要態漏到其餘態 —— 去相干 ＋ 讀出錯誤 ＋ 閘錯誤的典型樣態。

**位元序已驗證**：top-2 狀態 `0`、`17` 與黃金向量完全吻合。
（反轉與不反轉的 max abs(dP) 同為 0.1279 —— 這個測試對「偏差由主要態主導」
不敏感，真正判準是 top-k 是否吻合。Quafu 那邊的陷阱在這裡沒有重演。）

**RQ3 的起點**：真機的雜訊底約為取樣雜訊的 **11.6 倍**。任何要在真機上談
「校準改善」的宣稱，都必須先跨過這個底。

**Tuna-5（5 qubit，與我們電路同尺寸）當下 OFFLINE**，所以改用 Tuna-17；
5 個邏輯 qubit 由平台的轉譯器對映到 17 個實體 qubit 中的 5 個。

**工具**（放在這個目錄）：

| 檔案 | 用途 |
|---|---|
| `submit_qi_local.py` | 在本機送出（QASM 在筆電產、憑證在本機）；自己輪詢 status，
|  | 避開 SDK `result()` 內建 60 秒上限會拋 JobTimeoutError 的問題 |
| `analyze_qi.py` | 真機 vs 理想：max abs(dP)、TV、保真度、z、chi2 |
| `check_bitorder.py` | 只做一件事：確認位元序沒寫反 |

⚠️ 分析時踩到的坑：二項變異數的下界若取太小（我先寫了 1e-9），
期望次數趨近 0 的態會產生 z=1309 的假訊號、chi2 被灌到 240 萬。
下界應取 1（Poisson 尺度）。
### 9.6 ★ 真機上的「訓練過的分類器」（2026-09-21 04:05，Tuna-17）

第一個把**訓練好的分類器**送上真機的資料點：`n=5, L=2, seed=0`，16 個測試樣本
（每類 2 個），分 4 批送出（Tuna-17 限制每批 ≤ 5 條），每條 8192 shots。

| 指標 | 模擬 | 真機 |
|---|---|---|
| argmax 準確率 | 0.3750 | **0.4375** |
| **平均 P(真實類別)** | 0.1879 | **0.1513** |
| 平均最大機率 | 0.2524 | 0.1765 |
| 分布熵（最大 2.0794 nats） | 1.9135 | **2.0485** |
| 對均勻的 KL | 0.1660 | **0.0309** |

（8 類均勻 = 0.1250；真機對真實類別的平均機率是均勻的 1.21 倍，單樣本 t = 2.30。）

#### ★ 這裡有一個方法論陷阱，而且正好是本論文的主題

**argmax 準確率看起來沒問題（真機 0.4375 vs 模擬 0.3750），但那是假的。**
真機回來的分布已經被壓到接近均勻：熵 2.0485（最大 2.0794，即 98.5% 最大熵）、
對均勻的 KL 只剩 **0.0309**（模擬是 0.1660，掉了 **81%**）。
在這種分布上取 argmax，等於在雜訊裡挑一個最大值 —— 16 個樣本量到的準確率沒有意義。

**正確的讀法是完整機率向量**：真機給真實類別的平均機率只有 **0.1513**，
是均勻分布（0.125）的 1.21 倍。也就是說，**分類器的訊號只剩下一絲**。

**RQ3 的第一個誠實答案（深度 19、8192 shots）**：
> 在 Tuna-17 上，一個深度 19 的分類器只保留模擬端分布資訊的約 19%
> （KL 0.031 對 0.166）。在這個雜訊水準下，argmax 準確率不是可用的指標。

#### 為什麼深度必須往下修（設計變更，有數據支撐）

原設計的 L=8（n=5）在 Tuna-17 上轉譯後：

| 電路 | 原始深度 | 轉譯後深度 | 閘數 | 其中 SWAP |
|---|---|---|---|---|
| `qbn5_book`（固定電路） | 4 | **9** | 21 | 0 |
| **n=5, L=2** | 12 | **19** | 41 | 4 |
| **n=5, L=8** | 50 | **75–101** | 143 | **18–32** |

L=8 需要 40 個 CX 加上 18 個 SWAP（SWAP = 3 個 CX）＝ 等效約 **94 個雙閘**。
以第一個資料點（深度 9 就有 max|dP| = 0.128）估算，L=8 會被雜訊完全吃掉。
**所以實驗 A 的深度範圍由 {2,4,6,8} 收窄為低深度。** 這不是妥協，是量測結果。

#### 工具

| 檔案 | 用途 |
|---|---|
| `export_hw_circuits.py` | 重訓指定 (n,depth,seed)、**驗證與論文記錄一致**、匯出 QASM |
| `submit_qi_batch.py` | 分批（≤5）送出、自己輪詢、由 counts 算類別機率 |
| `analyze_hw_classifier.py` | 用完整機率向量比較（不是 argmax） |
| `transpile_depth.py` | 比較不同 optimization_level 的轉譯深度與 SWAP 數 |

#### 踩到的兩個 bug（都由驗證抓到）

1. **二次編碼**：`Xb` 已經是 `encode(Z_te)` 的結果，匯出時又呼叫了一次 `s09.encode`，
   把值全推到 π。症狀是「16 個樣本全部預測同一類」。
   由「QASM vs 模擬器精確機率」的比對抓到（修好後最差 max|dP| = 3.886e-16）。
2. **超出每批上限**：Tuna-17 限制每個 batch_job 最多 5 條電路，送 16 條直接拋錯。
### 9.7 ★ 取樣雜訊對照：分布變平是硬體造成的，不是統計假象

模擬端用的是**精確機率**，真機是 8192 shots 的**估計值**。有限取樣本身就會讓量到的
分布變平，所以在把 9.6 的「資訊掉 81%」歸因於硬體之前，必須先排除這個平凡解釋。

做法：把模擬端的精確分布用同樣的 8192 shots 重抽 200 次取平均，再算同一組指標。

| 指標 | 模擬（精確） | 模擬@8192 shots | 真機 |
|---|---|---|---|
| 對均勻的 KL | 0.1660 | **0.1660** | **0.0309** |
| 分布熵（最大 2.0794） | 1.9135 | **1.9135** | 2.0485 |
| 平均 P(真實類別) | 0.1879 | 0.1880 | 0.1513 |
| 平均最大機率 | 0.2524 | 0.2525 | 0.1765 |

**=> 取樣雜訊造成的 KL 損失 = 0%。真機額外掉到只剩 19%。**

為什麼雜訊為 0：8192 shots 分到 32 個基底態，每態平均 256 次，標準誤約
1/sqrt(256) = 6%，相對 KL 0.166 的訊號量級可以完全忽略。

工具：`control_shotnoise.py`

### 9.8 深度轉移曲線（進行中）

| L | Tuna-17 轉譯後深度 | 模擬端 16 樣本準確率 | 真機 |
|---|---|---|---|
| 1 | **8** | 0.3125 | ⏳ 等 Tuna-17 上線 |
| 2 | **19** | 0.3750 | ✅ 見 9.6 |
| 4 | **38** | 0.4375 | ⏳ 等 Tuna-17 上線 |
| 8 | **75–101** | 0.6250 | 不送（見 9.6 的深度論證） |

**真機隨時會 OFFLINE。** 實測：L=1/L=4 要送出時，前一刻 Tuna-17 還是 EXECUTING，
下一秒就變 offline（同一時間 Tuna-5 與 Tuna-9 也都是 OFFLINE，只剩模擬器 IDLE）。
已備好 `wait_tuna17.py`：每 60 秒查一次，一上線就自動送出兩批；
**只重試 offline 這一種錯誤**，其他錯誤直接停 —— 免得把 bug 當成離線一直重試。
---

## 十、送出流程掛上 b02（2026-09-21）

### 為什麼要搬

真機常常離線好幾小時（實測：L=1／L=4 要送出時，Tuna-17 前一刻還是 EXECUTING，
下一秒就 OFFLINE，而且連續 3 小時以上沒回來）。等待器必須長時間活著，
但本機（snow）是桌上機、會休眠。**b02 是常開伺服器。**

### b02 環境（實測）

| 項目 | 值 |
|---|---|
| 系統 | Debian 13（kernel 6.12） |
| Python | 3.13.5（QI SDK 要求 >=3.10,<3.14） |
| venv | `~/qi/.venv` |
| 套件 | qiskit 2.3.1 + qiskit-quantuminspire 0.18.4 + quantuminspire 4.0.0 |
| 網路 | quantum-inspire.com HTTP 200、PyPI 200 |
| 憑證 | `~/.quantuminspire/config.json`（由 snow 上傳，**權限 600**） |

⚠️ **憑證處理**：該檔含 OAuth refresh token。上傳與驗證過程**只檢查結構與權限，
內容從未回顯、不進 git、不貼進聊天**。b02 是使用者自己的伺服器。

### 常駐送出器 `~/qi/b02_runner.py`

- `nohup` 啟動，日誌在 `~/qi/runner.log` 與 `~/qi/runner.out`
- 每 300 秒查一次 Tuna-17；上線就把 9 項依序送完（每批 <= 5 條）
- 結果寫到 `~/qi/results/<kind>_<tag>_<stamp>.json`（含 counts 與四項指標）
- **只重試「離線」這一種錯誤**，其他錯誤直接記錄並跳過 —— 免得把 bug 當成離線無限重試
- 上限 24 小時

### 待送的 9 項

| kind | tag | 樣本 | 用途 |
|---|---|---|---|
| hw | hw_n5_d1_s0 | 16 | 深度曲線 L=1 |
| hw | hw_n5_d4_s0 | 16 | 深度曲線 L=4 |
| grid | n5_d2_s0 | 8 | 容量網格 |
| grid | n5_d8_s0 | 8 | 容量網格 |
| ablation | A_n5_d2_s0 | 8 | 無延遲（基線） |
| ablation | B1_n5_d2_s0 | 8 | 編碼後延遲 1 |
| ablation | B4_n5_d2_s0 | 8 | 編碼後延遲 4 |
| ablation | C1_n5_d2_s0 | 8 | 測量前延遲 1 |
| ablation | C4_n5_d2_s0 | 8 | 測量前延遲 4 |

**本機的等待器已停掉** —— 兩個同時跑會重複送出、浪費 QI 額度。
