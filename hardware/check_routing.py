import json, pathlib, collections
import numpy as np
ROOT = pathlib.Path("/home/b02/qi")
man = json.loads((ROOT / "cqasm_routed" / "manifest.json").read_text(encoding="utf-8"))
print("=== 各臂的編譯後電路統計（路線是否一致？）===")
ag = collections.defaultdict(list)
for m in man:
    ag[m["tag"]].append((m["cx"], m["swap"], m["depth_t"], m["gates"], m["delay_after_encoding"], m["delay_before_measure"]))
for t in sorted(ag):
    v = np.array([x[:4] for x in ag[t]], dtype=float)
    d = ag[t][0]
    print("  %-14s cx=%.1f±%.1f swap=%.1f±%.1f depth=%.1f±%.1f gates=%.1f±%.1f  (delay after=%d before=%d)" % (
        t, v[:,0].mean(), v[:,0].std(), v[:,1].mean(), v[:,1].std(),
        v[:,2].mean(), v[:,2].std(), v[:,3].mean(), v[:,3].std(), d[4], d[5]))
print()
print("=== 同一樣本 k，A 與 C 的閘數差 ===")
by = {}
for m in man:
    by.setdefault(m["k"], {})[m["tag"]] = m
for k in sorted(by):
    a = by[k].get("A_n5_d2_s0")
    row = []
    for t in ("B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0"):
        o = by[k].get(t)
        if a and o:
            row.append("%s d_gates=%+d d_cx=%+d d_swap=%+d" % (
                t.split("_")[0], o["gates"] - a["gates"], o["cx"] - a["cx"], o["swap"] - a["swap"]))
    print("  k=%d  %s" % (k, " | ".join(row)))
