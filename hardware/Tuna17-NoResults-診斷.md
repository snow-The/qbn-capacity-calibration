# Tuna-17「No Results」完整診斷（2026-09-21）

> 結論先講：**硬體一直是好的，結果一直存在伺服器上。**
> 是 `qiskit-quantuminspire` 的 `job.result()` 抓不到，而且它把「被取消」誤報成 `No Results`。
> 已從 API 直接救回 **72 筆真實硬體結果**（`results/recovered.json`）。

---

## 一、官方 API 文件在哪裡

**OpenAPI spec（權威來源）**：`https://api.quantum-inspire.com/openapi.json`
（title: Quantum Inspire 2, version 0.1.0, openapi 3.1.1, 53 個路徑, 76 個 schema）

這是 `QuTech-Delft/compute-api-client` 產生客戶端所用的同一份 spec
（見該 repo 的 `generate.sh`：`--input-spec http://localhost:8000/openapi.json`，
伺服器啟動時提供同一份）。

相關 repo：
- `QuTech-Delft/compute-api-client` — Python 客戶端（本地已安裝為 `compute_api_client`）
- `QuTech-Delft/qiskit-quantuminspire` — Qiskit provider（`tests/e2e_test.py` 是官方範例）
- `QuTech-Delft/compute-runtime-schema` — 2200/2300 在地介面（與雲端 API 無關）
- `QuTech-Delft/cQASM-spec`、`QuTech-Delft/pennylane-quantuminspire`

## 二、後端的正式限制（BackendType schema 的原文說明）

| 欄位 | 官方說明 | Tuna-17 的值 |
|---|---|---|
| job_execution_time_limit | Maximum allowed execution time (seconds) for a job. | **300.0** |
| max_jobs_per_batch_job | Maximum number of jobs allowed in a batch job. | 5 |
| batchjobs_per_queue_limit | Maximum allowed number of batchjobs per user and backend type. | 5 |
| max_number_of_shots | The maximum number of shots | 131072 |
| default_number_of_shots | The default shots | 8192 |
| nqubits | The number of qubits on the backend | 17（ninja-star，24 個 coupler） |
| gateset | 原生閘 | I Rx X X90 mX90 Ry Y Y90 mY90 Rz Z S T Sdag Tdag **H CZ** init measure reset barrier wait |
| supports_raw_data | 是否支援原始資料 | True |

## 三、根因

### 症狀
`JobStatus.DONE` 之後呼叫 `job.result()` 得到：

```
QiskitError: 'Result failed ,  Experiment failed. Trace_id: , System Message: No Results'
```

### 客戶端的訊息是誤導的
`qiskit_quantuminspire/qi_jobs.py` 的 `_fetch_failed_jobs_message`：

```python
"message": job.message if job.status == QIJobStatus.FAILED else "No Results",
```

**它只檢查 FAILED。** 而 JobStatus 的完整 enum 是
planned / running / completed / cancelled / failed——
**被 CANCELLED 的 job 不是 failed，所以訊息被寫成字面上的 No Results**，
`trace_id` 也是空的。這讓「被取消」看起來像「沒有任何結果」。

### 真正發生的事
直接查 API（/batch_jobs → /jobs/{id} → /results?job_id=）：

```
batch=844089  job=1462088  exec= 42.3s  COMPLETED
batch=844089  job=1462090  exec=213.5s  COMPLETED
batch=844089  job=1462092              CANCELLED   ← 超過 300 秒被取消
```

- 同一批電路中，有些只要 **~42 秒**，有些要 **~215–235 秒**（慢 5 倍）
- 一個 batch 有 5 個 job；只要含一顆慢電路，總執行時間就逼近或超過 **300 秒上限**
- 超過的 job 被 **CANCELLED**，客戶端就報 No Results
- **但同一批裡跑得快的 job 其實都完成了、結果也都存在**

## 四、救回來的資料

`results/recovered.json`（65 KB）：直接以 API 抓取，**93 個 job 中 72 個有完整結果**。

```
狀態分布：COMPLETED 72 / CANCELLED 21
shots   ：8192 x79、1024 x10、4096 x3、2048 x1
keys 數 ：32（5 qubit 全量測）、24、23、22、4
```

腳本：`hardware/recover_results.py`。

## 五、正確的做法（修正）

1. **不要依賴 `job.result()` 當唯一來源。** 它是 `@cache` 的、預設 `timeout=60.0`，
   而且對 CANCELLED 的訊息是誤導的。
2. **直接查 API**：`/results?job_id=<id>`（`ResultsApi.read_results_by_job_id_...`）
   拿到 Result，欄位有 `execution_time_in_seconds`、`shots_requested`、
   **`shots_done`**（實際完成的 shots）、`results`（counts）。
3. **控制 batch 的總執行時間**：慢電路（~215s）不要與其他電路湊成 5 顆。
   依實測，**每批 1–2 顆**才安全；或先量測每顆電路的執行時間再分組。
4. 檢查 `result.success`（官方 `tests/e2e_test.py` 就是這樣寫的），
   而不是只 catch 例外。
5. 官方 e2e 範例的用法是 **一顆電路一個 `backend.run(qc)`**，且**不傳 shots**
   （用後端預設 8192）。

## 六、教訓

1. **先讀 API 文件再寫程式。** 這次是反過來做（先讀原始碼、再跑經驗測試），
   多花了好幾輪。權威來源其實是一個 URL：`https://api.quantum-inspire.com/openapi.json`。
2. **錯誤訊息不必然是事實。** No Results 是客戶端自己填的字串，不是伺服器的診斷；
   伺服器端的真相要用 API 查。
3. **「任務完成」不等於「結果可用」。** 輪詢狀態之後仍應讓 `result()` 自己等，
   而且要知道 CANCELLED 也是一種結局。
4. **失敗不代表沒收到資料。** 這次 93 個 job 裡有 72 個其實成功了，
   如果只看客戶端的例外就會全部丟掉。
5. `pkill -f <名稱>` 會殺掉執行該指令的 shell 自己；遠端停程序請用腳本或先取 PID。
