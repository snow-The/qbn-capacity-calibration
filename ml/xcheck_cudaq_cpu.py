"""大電路三方對帳（正式軌）：真 CUDA-Q 算同一顆電路（n=10, depth=8, 250 閘）。

注意：CUDA-Q 內核不支援三元 IfExp，故把每層的 ring 偏移量預先算好當參數傳入。
"""
import json, pathlib
import numpy as np
import cudaq

P = pathlib.Path("/mnt/c/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration/ml/out/xcheck_params.json")
d = json.loads(P.read_text(encoding="utf-8"))
N, DEPTH = int(d["N"]), int(d["DEPTH"])
enc = [float(x) for x in d["Xa"][0]]
w = [float(x) for row in d["w"] for pair in row for x in pair]
off = [1 if dd % 2 == 0 else 2 for dd in range(DEPTH)]

@cudaq.kernel
def circ(n: int, depth: int, enc: list[float], w: list[float], off: list[int]):
    q = cudaq.qvector(n)
    for i in range(n):
        ry(enc[i], q[i])
    for dd in range(depth):
        for i in range(n):
            ry(w[(dd * n + i) * 2], q[i])
            rz(w[(dd * n + i) * 2 + 1], q[i])
        for i in range(n):
            cx(q[i], q[(i + off[dd]) % n])

cudaq.set_target("qpp-cpu")
print("target:", cudaq.get_target().name)
st = np.asarray(cudaq.get_state(circ, N, DEPTH, enc, w, off))
p = np.abs(st) ** 2
print("state dim =", p.size, " sum = %.12f" % p.sum())
out = pathlib.Path("/mnt/c/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration/ml/out/xcheck_cudaq.json")
out.write_text(json.dumps({"N": N, "DEPTH": DEPTH, "p_cudaq": p.tolist()}), encoding="utf-8")
print("已寫出", out.name)