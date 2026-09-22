"""把匯出的分類器電路分批送上 Tuna-17（每批上限 5 條），並與模擬端比較。

counts -> 類別：key 是 Qiskit 的古典字串，最右邊是 c[0] = qubit 0。
我們的類別 = 前 3 個 qubit（qubit 0 為 MSB）=> class = int(key[-3:], 2)。
映射若寫錯，準確率會掉到隨機 0.125，而模擬端是 0.625 —— 一眼可見。
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

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="hw_n5_d2_s0")
ap.add_argument("--backend", default="Tuna-17")
ap.add_argument("--shots", type=int, default=8192)
ap.add_argument("--opt", type=int, default=1)
a = ap.parse_args()

HW = pathlib.Path(r"C:\Users\snow\qi\hw")
RUN = HW / a.tag
rec = json.loads((HW / (a.tag + ".json")).read_text(encoding="utf-8"))

provider = QIProvider()
backend = provider.get_backend(a.backend)
limit = getattr(backend, "max_shots", None)
if limit is not None and a.shots > limit:
    raise SystemExit("shots %d 超過上限 %d" % (a.shots, limit))
print("後端 %s | shots %d | 樣本 %d | opt=%d" % (a.backend, a.shots, len(rec["samples"]), a.opt))

chunks = [rec["samples"][i:i + 5] for i in range(0, len(rec["samples"]), 5)]
all_counts = []
for ci, ch in enumerate(chunks):
    qcs = []
    for s in ch:
        qc = qasm2.loads((RUN / ("sample%02d.qasm" % s["k"])).read_text(encoding="utf-8"))
        qcs.append(transpile(qc, backend, optimization_level=a.opt, seed_transpiler=0))
    print("  批次 %d/%d：%d 條，轉譯後深度 %s"
          % (ci + 1, len(chunks), len(qcs), [c.depth() for c in qcs]))
    job = backend.run(qcs, shots=a.shots)
    print("    已送出 job_id=%r" % (job.job_id(),))
    t0, last = time.time(), None
    while time.time() - t0 < 2400:
        st = str(job.status())
        if st != last:
            print("      [%5.0fs] %s" % (time.time() - t0, st))
            last = st
        if st in ("JobStatus.DONE", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            break
        time.sleep(5)
    res = job.result(wait_for_results=False)
    got = res.get_counts()
    if not isinstance(got, list):
        got = [got]
    all_counts.extend(got)

ys = [s["y"] for s in rec["samples"]]
sim_pred = [s["pred"] for s in rec["samples"]]
preds, confs = [], []
for c in all_counts:
    total = sum(c.values())
    cls = np.zeros(8)
    for key, v in c.items():
        cls[int(key[-3:], 2)] += v / total
    preds.append(int(cls.argmax()))
    confs.append(float(cls.max()))

hw_acc = float(np.mean([p == y for p, y in zip(preds, ys)]))
sim_acc = float(np.mean([p == y for p, y in zip(sim_pred, ys)]))
agree = float(np.mean([p == q for p, q in zip(preds, sim_pred)]))
print()
print("  樣本  y   模擬  真機  真機最大機率")
for s, sp, hp, cf in zip(rec["samples"], sim_pred, preds, confs):
    print("   %2d   %d    %d     %d     %.3f" % (s["k"], s["y"], sp, hp, cf))
print()
print("  模擬端準確率 = %.4f" % sim_acc)
print("  真機準確率   = %.4f  （隨機 = 0.125）" % hw_acc)
print("  真機與模擬的預測一致率 = %.4f" % agree)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
out = HW / ("%s_%s_%d_%s.json" % (a.tag, a.backend, a.shots, stamp))
out.write_text(json.dumps({"tag": a.tag, "backend": a.backend, "shots": a.shots, "opt": a.opt,
                           "hw_pred": preds, "sim_pred": sim_pred, "y": ys,
                           "hw_max_prob": confs, "hw_acc": hw_acc, "sim_acc": sim_acc,
                           "agree": agree, "counts": all_counts}, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("  寫出:", out.name)
