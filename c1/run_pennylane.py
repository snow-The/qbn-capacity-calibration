"""在 PennyLane 上執行 cases.json 的閘列表，回報 ⟨Z⟩。

跑在 /root/pl/.venv（獨立 venv，不碰正式軌）。
原論文用的就是 PennyLane，所以這一邊是「原框架」的代表。
"""
import json
import pathlib
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pennylane as qml

HERE = pathlib.Path(__file__).resolve().parent
cases = json.loads((HERE / "out" / "cases.json").read_text(encoding="utf-8"))
N = cases["n_qubit"]
dev = qml.device("default.qubit", wires=N)
GATE = {"ry": qml.RY, "rz": qml.RZ, "rx": qml.RX}


@qml.qnode(dev)
def circuit(gates):
    for name, qs, ang in gates:
        if name == "cx":
            qml.CNOT(wires=[qs[0], qs[1]])
        else:
            GATE[name](ang, wires=qs[0])
    return [qml.expval(qml.PauliZ(i)) for i in range(N)]


out = []
for c in cases["cases"]:
    gates = [(n, q, a) for n, q, a in c["gates"]]
    z = np.asarray(circuit(gates), dtype=float)
    out.append({"id": c["id"], "z_pennylane": [float(v) for v in z]})

(HERE / "out" / "pennylane.json").write_text(json.dumps({"cases": out}, indent=1), encoding="utf-8")
print("PennyLane 執行 %d 個案例 -> out/pennylane.json" % len(out))
