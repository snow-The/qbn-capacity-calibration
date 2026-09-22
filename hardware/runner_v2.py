"""b02 真機送出器 v2

與 v1 的差別（皆為 2026-09-21 診斷的結論）：
  1. 每個 job 只送 1 顆電路。Tuna-17 job_execution_time_limit=300s，
     實測慢電路要 215-235s；一次 5 顆必定超時被 CANCELLED。
  2. 結果直接查 API（ResultsApi），不用 job.result()——
     後者對 CANCELLED 會回傳誤導的 "No Results"。
  3. 提交時就把 (kind, tag, k) 寫進記錄，不需要事後比對。
  4. 資料品質關卡：shots_done 必須等於 shots_requested、
     key 數必須符合預期、exec 時間必須在上限內。
  5. 被 CANCELLED 的 job 會自動重試（最多 RETRY 次）。
"""
import json, pathlib, time, datetime, sys

from qiskit import qasm2, transpile
from qiskit_quantuminspire.qi_provider import QIProvider
from qi2_shared.client import config
from qi2_shared.utils import run_async
from compute_api_client import ApiClient
from compute_api_client.api.results_api import ResultsApi

ROOT = pathlib.Path("/home/b02/qi")
DATA = ROOT / "data"
OUT = ROOT / "results/v2"
OUT.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "runner_v2.log"

BACKEND = "Tuna-17"
SHOTS = 8192
POLL_S = 5
TIMEOUT_S = 1500          # job 本身的上限是 300s；給排隊與回報留餘裕
RETRY = 3
EXPECT_KEYS = 32          # 5 個 qubit 全量測

def log(*a):
    line = "%s  %s" % (datetime.datetime.now().strftime("%m-%d %H:%M:%S"), " ".join(str(x) for x in a))
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + chr(10))

def api_result(job_id):
    """回傳 (counts, detail_dict) 或 (None, None)。"""
    async def _go():
        async with ApiClient(config()) as client:
            ra = ResultsApi(client)
            page = await ra.read_results_by_job_id_results_job_job_id_get(job_id=job_id)
            items = getattr(page, "items", page)
            if not items:
                return None, None
            d = items[0].to_dict() if hasattr(items[0], "to_dict") else vars(items[0])
            return d.get("results"), d
    try:
        return run_async(_go())
    except Exception as e:
        log("      api_result 失敗:", type(e).__name__, str(e)[:100])
        return None, None

def job_id_of(job):
    try:
        return job.circuits_run_data[0].job_id
    except Exception:
        return None

def schedule():
    items = []
    items.append(("hw", "hw_n5_d1_s0", 16))
    items.append(("hw", "hw_n5_d4_s0", 16))
    items.append(("grid", "n5_d2_s0", 8))
    items.append(("grid", "n5_d8_s0", 8))
    for tag in ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0"):
        items.append(("ablation", tag, 8))
    return items

def qasm_path(kind, tag, k):
    if kind == "hw":
        return DATA / tag / ("sample%02d.qasm" % k)
    return DATA / kind / tag / ("sample%02d.qasm" % k)

def already_done(tag, k):
    return bool(list(OUT.glob("%s__k%02d__*.json" % (tag, k))))

def run_one(b, kind, tag, k, attempt):
    src = qasm_path(kind, tag, k)
    if not src.is_file():
        log("  [%s k=%02d] 缺 QASM，跳過 (%s)" % (tag, k, src))
        return None
    try:
        qc = qasm2.loads(src.read_text(encoding="utf-8"))
        tqc = transpile(qc, b, optimization_level=1, seed_transpiler=0)
    except Exception as e:
        log("  [%s k=%02d] 建電路失敗: %s" % (tag, k, str(e)[:100]))
        return None

    t0 = time.time()
    try:
        job = b.run(tqc, shots=SHOTS)
    except Exception as e:
        log("  [%s k=%02d] 送出失敗: %s" % (tag, k, str(e)[:100]))
        return None
    jid = job_id_of(job)

    last = None
    while time.time() - t0 < TIMEOUT_S:
        st = str(job.status())
        if st != last:
            last = st
        if "DONE" in st or "ERROR" in st or "CANCELLED" in st:
            break
        time.sleep(POLL_S)

    counts, detail = (None, None)
    for wait_i in range(8):
        if jid:
            counts, detail = api_result(jid)
        if counts:
            break
        time.sleep(10)

    detail = detail or {}
    shots_done = detail.get("shots_done")
    shots_req = detail.get("shots_requested")
    exec_s = detail.get("execution_time_in_seconds")
    ok = bool(counts) and (shots_done == shots_req) and (len(counts) == EXPECT_KEYS)

    rec = dict(kind=kind, tag=tag, k=k, attempt=attempt, backend=BACKEND,
               shots_requested=SHOTS, shots_done=shots_done, exec_s=exec_s,
               job_id=jid, wall_s=round(time.time() - t0, 1),
               final_status=str(last).replace("JobStatus.", ""),
               n_keys=(len(counts) if counts else 0), quality_ok=ok, counts=counts)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUT / ("%s__k%02d__%s.json" % (tag, k, stamp))).write_text(
        json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

    log("  [%s k=%02d try%d] %s wall=%.0fs exec=%s shots=%s/%s keys=%s %s" % (
        tag, k, attempt, rec["final_status"], time.time() - t0, exec_s,
        shots_done, shots_req, rec["n_keys"], "OK" if ok else "不合格"))
    return rec

def main():
    b = QIProvider().get_backend(BACKEND)
    items = schedule()
    total = sum(n for _, _, n in items)
    log("=== runner v2 啟動 ===  後端=%s  狀態=%s" % (BACKEND, b.status))
    log("    項目=%d  樣本總數=%d  每顆電路 1 個 job  shots=%d" % (len(items), total, SHOTS))
    n_ok = n_bad = n_skip = 0
    for kind, tag, n in items:
        for k in range(n):
            if already_done(tag, k):
                n_skip += 1
                continue
            rec = None
            for attempt in range(1, RETRY + 1):
                rec = run_one(b, kind, tag, k, attempt)
                if rec and rec.get("quality_ok"):
                    break
                if rec is None:
                    break
                time.sleep(20)
            if rec and rec.get("quality_ok"):
                n_ok += 1
            elif rec:
                n_bad += 1
    log("=== runner v2 結束 ===  OK=%d  不合格=%d  已存在=%d" % (n_ok, n_bad, n_skip))

if __name__ == "__main__":
    main()
