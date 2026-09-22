"""延伸 tau 掃描：把延遲推到 T2 / T1 的時間尺度。

關鍵事實（兩個官方來源一致）：
  cQASM 規格的 wait 指令：「the unit ... represents the duration of a
  single-qubit gate on the backend, i.e., an execution cycle」
  QI 知識庫：「idle the qubit ... for the given number of cycles」

所以 wait(1) 約等於一個單閘時間（~25 ns），而 wait(64) 約 1.6 us。
transmon 的 T2 是 10-100 us 級 -> 先前 tau<=64 的延遲比 T2 短 1-3 個數量級，
去相位通道根本沒有實現。這正是五臂全部貼在雜訊底的原因。

本掃描：tau ∈ {0, 256, 1024, 4096, 16384, 65536} cycles（跨度 5 個數量級），
      與既有掃描 {0,1,4,16,64} 合起來是一條完整的對數劑量反應曲線。
tau=0 這一塊同時是同批次的漂移對照。
"""
import collections
import json
import pathlib

from qiskit import QuantumCircuit, transpile
from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.qi_provider import QIProvider

ROOT = pathlib.Path("/home/b02/qi")
OUT = ROOT / "cqasm_tau2"
TAUS = (0, 256, 1024, 4096, 16384, 65536)


def main():
    backend = QIProvider().get_backend("Tuna-17")
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "data/ablation/A_n5_d2_s0.json").read_text(encoding="utf-8"))
    man = []
    for sm in data["samples"]:
        k = sm["k"]
        enc = [float(v) for v in sm["x"]]
        layers = [[[float(g) for g in p] for p in lay] for lay in sm["w"]]
        for tau in TAUS:
            tag = "tau%05d" % tau
            sub = OUT / tag
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
            tqc = transpile(qc, backend, optimization_level=1, seed_transpiler=0)
            f = sub / ("k%02d.cq" % k)
            f.write_text(cqasm.dumps(tqc), encoding="utf-8")
            man.append(dict(tag=tag, k=k, tau=tau,
                            path=str(f.relative_to(ROOT)),
                            gates=sum(tqc.count_ops().values()),
                            cx=tqc.count_ops().get("cx", 0),
                            swap=tqc.count_ops().get("swap", 0)))
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("產生 %d 個 cQASM (tau in %s x 8 samples)" % (len(man), list(TAUS)))
    for t, v in sorted(collections.Counter(m["gates"] for m in man).items()):
        print("   gates=%d : %d" % (t, v))
    # show that the wait actually survived transpilation
    for tau in TAUS:
        if not tau:
            continue
        txt = (OUT / ("tau%05d" % tau) / "k00.cq").read_text(encoding="utf-8")
        ws = sorted({ln.strip() for ln in txt.splitlines() if ln.strip().startswith("wait")})
        print("   tau=%d -> %s" % (tau, ws[:2]))


if __name__ == "__main__":
    main()