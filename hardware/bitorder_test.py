"""在 Tuna-17 上直接測定位元序 —— 不靠推論，用實驗。

原理：把某一個 qubit 翻成 |1>，其餘保持 |0>，量測全部 5 個 qubit。
回傳的字串中「1」出現在哪個位置，就定義了該平台的位元序公約。

三顆電路：只翻 q0 / 只翻 q2 / 只翻 q4。三者互相印證。
"""
import json, pathlib, time, datetime

from qiskit import QuantumCircuit, transpile
from qiskit_quantuminspire.qi_provider import QIProvider
from qi2_shared.client import config
from qi2_shared.utils import run_async
from compute_api_client import ApiClient
from compute_api_client.api.results_api import ResultsApi

OUT = pathlib.Path("/home/b02/qi/results/bitorder")
OUT.mkdir(parents=True, exist_ok=True)
SHOTS = 1024

def log(*a):
    print("%s  %s" % (datetime.datetime.now().strftime("%H:%M:%S"), " ".join(str(x) for x in a)), flush=True)

def api_counts(job_id):
    async def _go():
        async with ApiClient(config()) as client:
            ra = ResultsApi(client)
            page = await ra.read_results_by_job_id_results_job_job_id_get(job_id=job_id)
            items = getattr(page, "items", page)
            if not items:
                return None, None
            d = items[0].to_dict() if hasattr(items[0], "to_dict") else vars(items[0])
            return d.get("results"), d
    return run_async(_go())

def one(phys, label, b):
    qc = QuantumCircuit(5, 5)
    qc.x(phys)
    qc.measure(range(5), range(5))          # clbit i <- logical qubit i
    tqc = transpile(qc, b, optimization_level=1, seed_transpiler=0)
    t0 = time.time()
    job = b.run(tqc, shots=SHOTS)
    jid = None
    try:
        jid = job.circuits_run_data[0].job_id
    except Exception as e:
        log("  !! 取不到 job_id:", str(e)[:120])
    last = None
    while time.time() - t0 < 2400:
        st = str(job.status())
        if st != last:
            last = st
        if "DONE" in st or "ERROR" in st or "CANCELLED" in st:
            break
        time.sleep(5)
    counts, detail = api_counts(jid) if jid else (None, None)
    log("  %-14s job_id=%s status=%s wall=%.0fs keys=%s" % (
        label, jid, str(last).replace("JobStatus.", ""), time.time() - t0,
        (len(counts) if counts else 0)))
    rec = dict(label=label, logical_qubit=phys, job_id=jid, shots=SHOTS,
               wall_s=round(time.time() - t0, 1), counts=counts,
               shots_done=(detail or {}).get("shots_done"),
               exec_s=(detail or {}).get("execution_time_in_seconds"))
    (OUT / ("%s.json" % label)).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    if counts:
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:4]
        log("      top:", top)
    return rec

def main():
    b = QIProvider().get_backend("Tuna-17")
    log("=== 位元序測定 start ===", "status:", b.status)
    res = []
    for phys in (0, 2, 4):
        res.append(one(phys, "x_on_q%d" % phys, b))
    log("=== 判讀 ===")
    for r in res:
        c = r.get("counts") or {}
        if not c:
            log("  %-14s 無結果" % r["label"]); continue
        best = max(c.items(), key=lambda kv: kv[1])[0]
        log("  %-14s 主要態=%-8s -> 字串中 1 在第 %d 位（由左數，0-based）" % (
            r["label"], best, best.index("1") if "1" in best else -1))
    log("=== 位元序測定 end ===")

if __name__ == "__main__":
    main()
