"""產生 C1 跨框架對照的測試案例：24 種慣例 × N 組隨機輸入。

Qt 端不需要任何量子框架 —— 閘列表與 NumPy 參考值都在這裡算好，
之後各框架只要「照著列表執行」並回報 ⟨Z⟩。
"""
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qlayer import DEPTH, EULER_ORDERS, N_QUBIT, SCALINGS, gates_for, z_expectations

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
N_INPUT = 5

rng = np.random.default_rng(20260921)
cases = []
for euler in EULER_ORDERS:
    for scaling in SCALINGS:
        for k in range(N_INPUT):
            x = rng.normal(0, 1, size=10)
            theta = rng.uniform(-np.pi, np.pi, size=(DEPTH, N_QUBIT, 3))
            g = gates_for(x, theta, euler, scaling)
            cases.append({
                "id": "%s|%s|%d" % (euler, scaling, k),
                "euler": euler, "scaling": scaling,
                "gates": [[n, q, a] for n, q, a in g],
                "z_numpy": [float(v) for v in z_expectations(g)],
            })
(OUT / "cases.json").write_text(json.dumps({"n_qubit": N_QUBIT, "depth": DEPTH,
                                            "cases": cases}, indent=1), encoding="utf-8")
print("產生 %d 個案例（%d 慣例 x %d 輸入）-> out/cases.json"
      % (len(cases), len(EULER_ORDERS) * len(SCALINGS), N_INPUT))
