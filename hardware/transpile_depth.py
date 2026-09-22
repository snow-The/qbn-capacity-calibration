import json, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from qiskit import qasm2, transpile
from qiskit_quantuminspire.qi_provider import QIProvider
HW = pathlib.Path(r"C:\Users\snow\qi\hw")
rec = json.loads((HW / "hw_n5_d8_s0.json").read_text(encoding="utf-8"))
b = QIProvider().get_backend("Tuna-17")
qc0 = qasm2.loads((HW / "hw_n5_d8_s0" / "sample00.qasm").read_text(encoding="utf-8"))
print("原始電路: depth=%d ops=%d" % (qc0.depth(), sum(qc0.count_ops().values())))
for lvl in (0, 1, 2, 3):
    t = transpile(qc0, b, optimization_level=lvl, seed_transpiler=0)
    ops = t.count_ops()
    print("  opt=%d: depth=%3d ops=%3d  %s" % (lvl, t.depth(), sum(ops.values()), dict(ops)))
