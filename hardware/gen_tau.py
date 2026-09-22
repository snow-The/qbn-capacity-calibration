"""高檢定力的 T1 劑量反應實驗。

8192 shots 時 A vs C 的差異與取樣雜訊無法區分（p ≈ 0.27）。
提高檢定力：shots ×8（雜訊 ÷2.8）＋ 多個 τ 看單調性。

設計：同一組 8 個樣本，測量前插入 wait(τ)，τ ∈ {0, 1, 4, 16, 64}。
      τ=0 即臂 A（對照），其餘是不同劑量的尾端去相位。
      預測：若 T1 是機制，對 A 的偏差應隨 τ 單調上升。
"""
import json, pathlib
from qiskit import QuantumCircuit, transpile
from qiskit_quantuminspire.qi_provider import QIProvider
from qiskit_quantuminspire import cqasm

ROOT = pathlib.Path("/home/b02/qi")
OUT = ROOT / "cqasm_tau"
TAUS = (0, 1, 4, 16, 64)

def main():
    b = QIProvider().get_backend("Tuna-17")
    OUT.mkdir(parents=True, exist_ok=True)
    d = json.loads((ROOT / "data/ablation/A_n5_d2_s0.json").read_text(encoding="utf-8"))
    man = []
    for sm in d["samples"]:
        k = sm["k"]
        enc = [float(v) for v in sm["x"]]
        layers = [[[float(g) for g in p] for p in lay] for lay in sm["w"]]
        for tau in TAUS:
            sub = OUT / ("tau%02d" % tau)
            sub.mkdir(parents=True, exist_ok=True)
            qc = QuantumCircuit(5, 5)
            for i, a in enumerate(enc):
                qc.ry(a, i)
            for lay in layers:
                for i in range(5):
                    qc.cx(i, (i + 1) % 5)
                for i, (ry, rz) in enumerate(lay):
                    qc.ry(ry, i)
                    qc.rz(rz, i)
            if tau:
                for i in range(5):
                    qc.delay(int(tau), i, unit="dt")
            qc.measure(range(5), range(5))
            tqc = transpile(qc, b, optimization_level=1, seed_transpiler=0)
            (sub / ("k%02d.cq" % k)).write_text(cqasm.dumps(tqc), encoding="utf-8")
            man.append(dict(tag="tau%02d" % tau, k=k, tau=tau,
                            path=str((sub / ("k%02d.cq" % k)).relative_to(ROOT)),
                            gates=sum(tqc.count_ops().values()), cx=tqc.count_ops().get("cx", 0)))
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("產生 %d 個 cQASM（τ ∈ %s × 8 樣本）" % (len(man), list(TAUS)))
    import collections
    for t, v in sorted(collections.Counter(m["gates"] for m in man).items()):
        print("   gates=%d : %d 個" % (t, v))

if __name__ == "__main__":
    main()
