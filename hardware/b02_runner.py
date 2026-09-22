"""b02 常駐送出器：盯著 Tuna-17，上線就把所有待送的批次依序送完。

為什麼掛在 b02：真機常常離線好幾小時，這個工作必須長時間等待；
本機（snow）是桌上機、會休眠，b02 是常開伺服器。

憑證：~/.quantuminspire/config.json（由 snow 上傳，權限 600，永不回顯）。

每批 <= 5 條（Tuna-17 的 batch_job 上限）。只重試「離線」這一種錯誤，
其他錯誤直接記錄並跳過 —— 免得把 bug 當成離線無限重試。
"""
import datetime
import json
import pathlib
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from qiskit import QuantumCircuit, qasm2, transpile
from qiskit_quantuminspire.qi_provider import QIProvider

ROOT = pathlib.Path.home() / "qi"
DATA = ROOT / "data"
OUT = ROOT / "results"
LOG = ROOT / "runner.log"
BACKEND, SHOTS, DEADLINE_H = "Tuna-17", 8192, 24


def log(*a):
    line = "%s  %s" % (datetime.datetime.now().strftime("%m-%d %H:%M:%S"),
                       " ".join(str(x) for x in a))
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + chr(10))


def backend_or_none():
    try:
        return QIProvider().get_backend(BACKEND)
    except Exception as e:
        log("  backend 查詢失敗:", type(e).__name__, str(e)[:80])
        return None


def native_delay_circuit(sample, rec):
    """延遲電路要用 Qiskit 原生 API 建：delay 不是合法 OpenQASM 2.0。"""
    x, w = sample["x"], np.asarray(sample["w"])
    n = rec["n"]
    qc = QuantumCircuit(n, n)
    for i in range(n):
        qc.ry(x[i], i)
    if rec["delay_after_encoding"]:
        qc.barrier()
        for i in range(n):
            qc.delay(rec["delay_after_encoding"], i)
    for d in range(rec["depth"]):
        for i in range(n):
            qc.ry(w[d, i, 0], i)
            qc.rz(w[d, i, 1], i)
        step = 1 if d % 2 == 0 else 2
        for i in range(n):
            qc.cx(i, (i + step) % n)
    if rec["delay_before_measure"]:
        qc.barrier()
        for i in range(n):
            qc.delay(rec["delay_before_measure"], i)
    qc.measure(range(n), range(n))
    return qc

def submit(kind, tag, backend):
    if kind == "hw":
        rundir = DATA / tag
        rec = json.loads((DATA / (tag + ".json")).read_text(encoding="utf-8"))
    else:
        rundir = DATA / kind / tag
        rec = json.loads((DATA / kind / (tag + ".json")).read_text(encoding="utf-8"))
    samples = rec["samples"]
    counts_all = []
    for ci in range(0, len(samples), 5):
        ch = samples[ci:ci + 5]
        if kind == "ablation":
            qcs = [transpile(native_delay_circuit(s, rec), backend, optimization_level=1,
                             seed_transpiler=0) for s in ch]
        else:
            qcs = [transpile(qasm2.loads((rundir / ("sample%02d.qasm" % s["k"])).read_text(encoding="utf-8")),
                             backend, optimization_level=1, seed_transpiler=0) for s in ch]
        job = backend.run(qcs, shots=SHOTS)
        t0, last = time.time(), None
        while time.time() - t0 < 2400:
            st = str(job.status())
            if st != last:
                log("    [%4.0fs] %s" % (time.time() - t0, st))
                last = st
            if "DONE" in st or "ERROR" in st or "CANCELLED" in st:
                break
            time.sleep(5)
        # 原本是 wait_for_results=False，但 QI 的 job DONE 不代表結果已可取回，
        # 會回傳空的 result 並丟出 QiskitError('... No Results')。
        # 實測：改成預設（會等待）之後單電路與批次都正常取得真實計數。
        got = job.result().get_counts()
        counts_all.extend(got if isinstance(got, list) else [got])

    P = []
    for c in counts_all:
        tot = sum(c.values())
        v = np.zeros(8)
        for key, n in c.items():
            v[int(key[-3:], 2)] += n / tot
        P.append(v)
    P = np.array(P)
    ys = np.array([s["y"] for s in samples])
    Psim = np.array([np.asarray(s["expected_class_probs"]) for s in samples])

    def kl(M):
        return float(np.mean([np.sum(p * np.log(p / 0.125 + 1e-12)) for p in M]))

    res = {"kind": kind, "tag": tag, "backend": BACKEND, "shots": SHOTS,
           "n_samples": len(samples),
           "hw_acc": float((P.argmax(1) == ys).mean()),
           "sim_acc": float((Psim.argmax(1) == ys).mean()),
           "hw_mean_p_true": float(P[np.arange(len(ys)), ys].mean()),
           "sim_mean_p_true": float(Psim[np.arange(len(ys)), ys].mean()),
           "hw_kl_uniform": kl(P), "sim_kl_uniform": kl(Psim),
           "hw_mean_max_prob": float(P.max(1).mean()),
           "sim_mean_max_prob": float(Psim.max(1).mean()),
           "counts": counts_all}
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUT / ("%s_%s_%s.json" % (kind, tag, stamp))).write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log("  %-9s %-16s 真機 acc %.4f | 模擬 %.4f | KL 真機 %.4f | 模擬 %.4f"
        % (kind, tag, res["hw_acc"], res["sim_acc"], res["hw_kl_uniform"], res["sim_kl_uniform"]))


JOBS = [("hw", "hw_n5_d1_s0"), ("hw", "hw_n5_d4_s0"),
        ("grid", "n5_d2_s0"), ("grid", "n5_d8_s0"),
        ("ablation", "A_n5_d2_s0"), ("ablation", "B1_n5_d2_s0"),
        ("ablation", "B4_n5_d2_s0"), ("ablation", "C1_n5_d2_s0"),
        ("ablation", "C4_n5_d2_s0")]

log("=== b02 runner 啟動，待送 %d 項 ===" % len(JOBS))
t_end = time.time() + DEADLINE_H * 3600
for kind, tag in JOBS:
    while time.time() < t_end:
        b = backend_or_none()
        st = ""
        try:
            st = str(b.status) if b is not None else "offline"
        except Exception:
            st = "offline"
        if b is None or "offline" in st.lower():
            log("  [%s] Tuna-17 離線，300 秒後重試" % tag)
            time.sleep(300)
            continue
        try:
            log("  [%s] 送出…" % tag)
            submit(kind, tag, b)
            break
        except Exception as e:
            msg = str(e)
            if "offline" in msg.lower():
                log("  [%s] 送出時離線，300 秒後重試" % tag)
                time.sleep(300)
                continue
            log("  [%s] 非離線錯誤，跳過：%s: %s" % (tag, type(e).__name__, msg[:150]))
            break
log("=== runner 結束 ===")
