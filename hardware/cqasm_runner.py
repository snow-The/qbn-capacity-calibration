"""cQASM 原生送出器 —— 不用 Qiskit、不用 transpiler。

為什麼：
  - Qiskit transpile 會插 SWAP、改寫電路，送出的東西與原稿不同（2026-09-21 踩到）。
  - OpenQASM 2.0 沒有延遲；cQASM 3.0 的 wait(N) q[i] 原生支援。
  - QI 後端原生吃 cQASM（language_id=2），`qi run --file x.cq` 是官方入口。

流程：qi run --file <cq> --backend-type-id 7 --num-shots N  -> job id
      qi jobs status <id>  輪詢
      qi jobs results <id> 取 counts（與 status 分開，這是重點）
"""
import json, pathlib, re, subprocess, sys, time, datetime

ROOT = pathlib.Path("/home/b02/qi")
QI = str(ROOT / ".venv/bin/qi")
OUT = ROOT / "results/cqasm"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "_submit_errors.log").parent.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "cqasm_runner.log"

BACKEND_TYPE_ID = 7        # Tuna-17
SHOTS = 8192
WINDOW = 5                 # batchjobs_per_queue_limit = 5
POLL_S = 10
TIMEOUT_S = 3000

def log(*a):
    line = "%s  %s" % (datetime.datetime.now().strftime("%m-%d %H:%M:%S"), " ".join(str(x) for x in a))
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + chr(10))

def sh(args, timeout=180):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return (p.returncode, (p.stdout or "") + (p.stderr or ""))

def submit(cq_path, tries=4):
    """送出。暫時性的 API 錯誤（429/5xx/連線）要重試——
    2026-09-22 實際踩到：同一結構的 C4 成功、C1 卻丟出 traceback。"""
    last = ""
    for i in range(1, tries + 1):
        rc, out = sh([QI, "run", "--file", str(cq_path), "--backend-type-id", str(BACKEND_TYPE_ID),
                      "--num-shots", str(SHOTS)])
        m = re.search(r"job id[:\s]+(\d+)", out, re.I)
        if m:
            return int(m.group(1)), "try%d" % i
        last = out
        # 完整錯誤寫檔，方便事後判讀（log 只留摘要）
        with (ROOT / "results/cqasm/_submit_errors.log").open("a", encoding="utf-8") as f:
            f.write("== %s try%d ==%s%s%s" % (cq_path, i, chr(10), out, chr(10)))
        time.sleep(15 * i)
    return None, last.strip().replace(chr(10), " ")[:200]

# 取結果一律走 API：
#   - `qi jobs results` 的輸出格式未經確認（探測 job 一直沒跑完）；
#   - API 的 ResultsApi 回傳結構化 dict，欄位有 shots_done / execution_time_in_seconds，
#     2026-09-21 就是用這條路救回 72 筆結果的。
def api_job(job_id):
    from qi2_shared.client import config
    from qi2_shared.utils import run_async
    from compute_api_client import ApiClient
    from compute_api_client.api.jobs_api import JobsApi

    async def _go():
        async with ApiClient(config()) as c:
            j = await JobsApi(c).read_job_jobs_id_get(id=job_id)
            return j.to_dict() if hasattr(j, "to_dict") else vars(j)
    try:
        return run_async(_go())
    except Exception as e:
        return {"_error": "%s: %s" % (type(e).__name__, str(e)[:80])}


def api_counts(job_id):
    from qi2_shared.client import config
    from qi2_shared.utils import run_async
    from compute_api_client import ApiClient
    from compute_api_client.api.results_api import ResultsApi

    async def _go():
        async with ApiClient(config()) as c:
            p = await ResultsApi(c).read_results_by_job_id_results_job_job_id_get(job_id=job_id)
            it = getattr(p, "items", p)
            if not it:
                return None, None
            d = it[0].to_dict() if hasattr(it[0], "to_dict") else vars(it[0])
            return d.get("results"), d
    try:
        return run_async(_go())
    except Exception as e:
        return None, None


def status(job_id):
    d = api_job(job_id)
    return str(d.get("status", d.get("_error", "?")))

def parse_counts(text):
    """從 qi jobs results 的輸出抓出 counts 字典。"""
    for m in re.finditer(r"\{([^{}]*)\}", text):
        body = m.group(1)
        # 引號用 chr() 組，避免 TS/PowerShell/Python 三層跳脫地獄
        qq = "[" + chr(39) + chr(34) + "]([01]+)[" + chr(39) + chr(34) + "]"
        pairs = re.findall(qq + chr(92) + "s*:" + chr(92) + "s*(" + chr(92) + "d+)", body)
        if pairs:
            return {k: int(v) for k, v in pairs}
    return None

# 只送真機才給得出的東西（2026-09-21 的範圍決定）：
#   送   ：五個消融臂 A/B1/B4/C1/C4 —— 檢驗論文 3.6 節的可證偽預測
#          （真機 T1 會破壞「尾端去相位 = no-op」）
#   不送 ：hw_n5_d1/d4、grid n5_d2/d8 —— 容量斷崖純粹是模擬結果
SEND_TAGS = ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0")


def interleaved(man):
    """按樣本 k 交錯五個臂：同一個樣本的各臂在相近時間送出，
    這樣 A vs C 的比較才在同一段校準漂移下進行。"""
    picks = [m for m in man if m["tag"] in SEND_TAGS]
    by_k = {}
    for m in picks:
        by_k.setdefault(m["k"], {})[m["tag"]] = m
    out = []
    for k in sorted(by_k):
        for tag in SEND_TAGS:
            if tag in by_k[k]:
                out.append(by_k[k][tag])
    return out


def main():
    man = json.loads((ROOT / "cqasm" / "manifest.json").read_text(encoding="utf-8"))
    todo = [m for m in interleaved(man)
            if not list(OUT.glob("%s__k%02d__*.json" % (m["tag"], m["k"])))]
    log("=== cQASM 原生送出器啟動 ===")
    log("    總計 %d 顆，待送 %d 顆，視窗 %d，backend_type_id=%d shots=%d" % (
        len(man), len(todo), WINDOW, BACKEND_TYPE_ID, SHOTS))
    n_ok = n_bad = 0
    i = 0
    while i < len(todo):
        batch = todo[i:i + WINDOW]
        i += WINDOW
        inflight = []
        for m in batch:
            cq = ROOT / m["path"]
            jid, msg = submit(cq)
            if jid is None:
                log("  [%s k=%02d] 送出失敗: %s" % (m["tag"], m["k"], msg))
                n_bad += 1
                continue
            inflight.append((m, jid, time.time()))
            log("  [%s k=%02d] 送出 -> job %s" % (m["tag"], m["k"], jid))
        for m, jid, t0 in inflight:
            last = None
            while time.time() - t0 < TIMEOUT_S:
                st = status(jid)
                if st != last:
                    last = st
                if re.search(r"completed|cancelled|failed", st, re.I):
                    break
                time.sleep(POLL_S)
            counts, detail = (None, None)
            for _w in range(12):
                counts, detail = api_counts(jid)
                if counts:
                    break
                time.sleep(10)
            detail = detail or {}
            txt = ""
            shots_done = detail.get("shots_done")
            shots_req = detail.get("shots_requested")
            exec_s = detail.get("execution_time_in_seconds")
            ok = bool(counts) and len(counts) == 32 and sum(counts.values()) == SHOTS \
                and shots_done == shots_req
            rec = dict(tag=m["tag"], kind=m["kind"], k=m["k"], job_id=jid, shots=SHOTS,
                       delay_after_encoding=m.get("delay_after_encoding"),
                       delay_before_measure=m.get("delay_before_measure"),
                       depth=m.get("depth"), n=m.get("n"),
                       wall_s=round(time.time() - t0, 1), status=last,
                       shots_done=shots_done, exec_s=exec_s,
                       n_keys=(len(counts) if counts else 0),
                       total_shots=(sum(counts.values()) if counts else 0),
                       quality_ok=ok, counts=counts, raw=("" if counts else txt[-400:]))
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            (OUT / ("%s__k%02d__%s.json" % (m["tag"], m["k"], stamp))).write_text(
                json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            if ok:
                n_ok += 1
            else:
                n_bad += 1
            log("  [%s k=%02d] %s wall=%.0fs keys=%s shots=%s %s" % (
                m["tag"], m["k"], str(last)[:60], time.time() - t0,
                rec["n_keys"], rec["total_shots"], "OK" if ok else "不合格"))
    log("=== 結束 ===  OK=%d 不合格=%d" % (n_ok, n_bad))

if __name__ == "__main__":
    main()
