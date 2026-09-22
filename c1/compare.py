"""比對三個實作（NumPy 參考 / CUDA-Q / PennyLane）在 24 種慣例下的 ⟨Z⟩。

這一步回答的是 C1 真正的問題：**同一份閘列表，換框架會不會變？**
若三者一致到 1e-12，則「跨框架可移植」成立，剩下的差異都來自慣例選擇（而非框架）。
"""
import json
import pathlib
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent / "out"
cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]


def load(name):
    p = HERE / name
    if not p.exists():
        return None
    return {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))["cases"]}


cq, pl = load("cudaq.json"), load("pennylane.json")
print("案例數: %d | CUDA-Q: %s | PennyLane: %s"
      % (len(cases), "有" if cq else "缺", "有" if pl else "缺"))

for label, other, key in (("CUDA-Q", cq, "z_cudaq"), ("PennyLane", pl, "z_pennylane")):
    if not other:
        continue
    worst = 0.0
    for c in cases:
        a = np.asarray(c["z_numpy"])
        b = np.asarray(other[c["id"]][key])
        worst = max(worst, float(np.max(np.abs(a - b))))
    print("  NumPy 參考 vs %-12s 最差 max|d<Z>| = %.3e  ==> %s"
          % (label, worst, "一致" if worst < 1e-10 else "★ 不一致"))

# 順便看慣例之間的差異有多大（這是 C1 要報的區間）
by = {}
for c in cases:
    by.setdefault((c["euler"], c["scaling"]), []).append(c["z_numpy"])
print()
print("  12 種慣例（4 歐拉順序 x 3 縮放）的 ⟨Z⟩ 分散程度：")
keys = sorted(by)
worst_pair, worst_val = None, 0.0
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a = np.asarray(by[keys[i]]).ravel()
        b = np.asarray(by[keys[j]]).ravel()
        if len(a) != len(b):
            continue
        d = float(np.max(np.abs(a - b)))
        if d > worst_val:
            worst_pair, worst_val = (keys[i], keys[j]), d
print("    最不相似的兩組慣例: %s vs %s，差 %.4f"
      % (worst_pair[0], worst_pair[1], worst_val) if worst_pair else "    (n/a)")
print("    => 慣例選擇造成的差異，**遠大於**框架造成的差異（若上面是 1e-12 級）")
