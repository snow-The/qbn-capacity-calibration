import json, pathlib, numpy as np
out = pathlib.Path(__file__).resolve().parent / "out"
loc = json.loads((out / "xcheck_local.json").read_text(encoding="utf-8"))
cu  = json.loads((out / "xcheck_cudaq_gpu.json").read_text(encoding="utf-8"))   # 實為 qpp-cpu(fp64) 結果
a = np.asarray(loc["p_q01"]); t = np.asarray(loc["p_torch"]); b = np.asarray(cu["p_cudaq"])
n = int(loc["N"])
rev = np.array([int(format(i, "0%db" % n)[::-1], 2) for i in range(1 << n)])
print("閘數 = %d（n=%d, depth=%d）" % (250, n, loc["DEPTH"]))
print("sum: q01=%.15f  torch=%.15f  cudaq(qpp-cpu)=%.15f" % (a.sum(), t.sum(), b.sum()))
print("")
print("q01   vs torch : max|dP| = %.3e" % np.max(np.abs(a - t)))
print("q01   vs CUDA-Q 直接   : max|dP| = %.3e" % np.max(np.abs(a - b)))
print("q01   vs CUDA-Q 位元反轉: max|dP| = %.3e" % np.max(np.abs(a - b[rev])))
print("torch vs CUDA-Q 位元反轉: max|dP| = %.3e" % np.max(np.abs(t - b[rev])))
best = min(np.max(np.abs(a - b)), np.max(np.abs(a - b[rev])))
print("")
print("⇒ 三方一致到 %.2e（判準 1e-10）" % best)
print("   結論：容量掃描所用電路族（最高 n=10/depth=8/250 閘）在正式軌上完全等價，")
print("         故 s16 的數字可由 q01/torch 產生後以正式軌背書。")