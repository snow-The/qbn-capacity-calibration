"""Tuna-17 通用送出器：容量網格與去相位消融共用。

讀 runs/<kind>/<tag>.json（由 grid_export.py 或 ablation_export.py 產生）＋ 同名的
sample*.qasm，分批（Tuna-17 每批上限 5 條）送出，收集 counts 並與模擬端比較。

counts -> 類別：class = int(key[-3:], 2)（key 最右邊是 c[0] = qubit 0）。
映射若寫錯，準確率會掉到隨機 0.125，而模擬端是 0.375 上下 —— 一眼可見。

用法：python hw_run.py --kind grid --tag n5_d2_s0
"""
import argparse
import datetime
import json
import pathlib
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from qiskit import qasm2, transpile
from qiskit_quantuminspire.qi_provider import QIProvider

HW = pathlib.Path(r"C:\Users\snow\qi\hw")


def native_delay_circuit(sample: dict, rec: dict):
    """用 Qiskit 原生 API 建延遲電路（QASM 不能表達 delay，見 ablation_export.py）。"""
    from qiskit import QuantumCircuit
    x, w = sample["x"], np.asarray(sample["w"])
    n = rec["n"]
    qc = QuantumCircuit(n, n)
    for i in range(n):
        qc.ry(x[i], i)
    if rec["delay_after_encoding"]:
        qc.barrier()
        for i in range(n):
            qc.delay(rec["delay_after_encoding"], i)
    ring = lambda step: [(i, (i + step) % n) for i in range(n)]
    for d in range(rec["depth"]):
        for i in range(n):
            qc.ry(w[d, i, 0], i)
            qc.rz(w[d, i, 1], i)
        for c, t in ring(1 if d % 2 == 0 else 2):
            qc.cx(c, t)
    if rec["delay_before_measure"]:
        qc.barrier()
        for i in range(n):
            qc.delay(rec["delay_before_measure"], i)
    qc.measure(range(n), range(n))
    return qc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="grid")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--backend", default="Tuna-17")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--opt", type=int, default=1)
    a = ap.parse_args()

    run = HW / a.kind / a.tag
    rec = json.loads((HW / a.kind / (a.tag + ".json")).read_text(encoding="utf-8"))
    provider = QIProvider()
    backend = provider.get_backend(a.backend)
    limit = getattr(backend, "max_shots", None)
    if limit is not None and a.shots > limit:
        raise SystemExit("shots %d 超過 %s 上限 %d" % (a.shots, a.backend, limit))
    print("kind=%s tag=%s | %s | shots=%d | 樣本 %d"
          % (a.kind, a.tag, a.backend, a.shots, len(rec["samples"])), flush=True)

    chunks = [rec["samples"][i:i + 5] for i in range(0, len(rec["samples"]), 5)]
    all_counts = []
    for ci, ch in enumerate(chunks):
        if a.kind == "ablation":
            qcs = [transpile(native_delay_circuit(s, rec), backend,
                             optimization_level=a.opt, seed_transpiler=0) for s in ch]
        else:
            qcs = [transpile(qasm2.loads((run / ("sample%02d.qasm" % s["k"])).read_text(encoding="utf-8")),
                             backend, optimization_level=a.opt, seed_transpiler=0) for s in ch]
        print("  批次 %d/%d：%d 條，深度 %s"
              % (ci + 1, len(chunks), len(qcs), [c.depth() for c in qcs]), flush=True)
        job = backend.run(qcs, shots=a.shots)
        t0, last = time.time(), None
        while time.time() - t0 < 2400:
            st = str(job.status())
            if st != last:
                print("    [%5.0fs] %s" % (time.time() - t0, st), flush=True)
                last = st
            if st in ("JobStatus.DONE", "JobStatus.ERROR", "JobStatus.CANCELLED"):
                break
            time.sleep(5)
        got = job.result(wait_for_results=False).get_counts()
        all_counts.extend(got if isinstance(got, list) else [got])

    P, preds = [], []
    for c in all_counts:
        tot = sum(c.values())
        v = np.zeros(8)
        for key, n in c.items():
            v[int(key[-3:], 2)] += n / tot
        P.append(v)
        preds.append(int(v.argmax()))
    P = np.array(P)
    ys = np.array([s["y"] for s in rec["samples"]])
    Psim = np.array([np.asarray(s["expected_class_probs"]) for s in rec["samples"]])

    def kl(M):
        return float(np.mean([np.sum(p * np.log(p / 0.125 + 1e-12)) for p in M]))

    res = {
        "kind": a.kind, "tag": a.tag, "backend": a.backend, "shots": a.shots,
        "hw_acc": float((P.argmax(1) == ys).mean()),
        "sim_acc": float((Psim.argmax(1) == ys).mean()),
        "hw_mean_p_true": float(P[np.arange(len(ys)), ys].mean()),
        "sim_mean_p_true": float(Psim[np.arange(len(ys)), ys].mean()),
        "hw_kl_uniform": kl(P), "sim_kl_uniform": kl(Psim),
        "hw_mean_max_prob": float(P.max(1).mean()),
        "sim_mean_max_prob": float(Psim.max(1).mean()),
        "counts": all_counts,
    }
    print()
    print("  %-22s %10s %10s" % ("指標", "模擬", "真機"))
    print("  %-22s %10.4f %10.4f" % ("argmax 準確率", res["sim_acc"], res["hw_acc"]))
    print("  %-22s %10.4f %10.4f" % ("平均 P(真實類別)", res["sim_mean_p_true"], res["hw_mean_p_true"]))
    print("  %-22s %10.4f %10.4f" % ("平均最大機率", res["sim_mean_max_prob"], res["hw_mean_max_prob"]))
    print("  %-22s %10.4f %10.4f" % ("對均勻的 KL", res["sim_kl_uniform"], res["hw_kl_uniform"]))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = HW / a.kind / ("%s_%s_%d_%s.json" % (a.tag, a.backend, a.shots, stamp))
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  寫出:", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
