"""產生「已路由」的 cQASM：Qiskit transpile 負責路由，cqasm.dumps 負責匯出。

為什麼要這樣做（2026-09-22 的兩個發現）：
  1. Tuna-17 的連接圖上**沒有 5-環**（有 4-環，無 5-環），
     所以送邏輯 qubit 的環形電路會被伺服器拒絕：
         Compilation error: the following qubit interactions ... prevent a 1-to-1 mapping
  2. 但 `qi run --file x.cq` 這條原生路徑是乾淨的（不經過 job.result()）。
  → 用 Qiskit 做路由、匯出成 cQASM、再用 qi run 送出。
"""
import json, pathlib, re
from qiskit import QuantumCircuit, transpile
from qiskit_quantuminspire.qi_provider import QIProvider
from qiskit_quantuminspire import cqasm

ROOT = pathlib.Path("/home/b02/qi")
DATA = ROOT / "data"
OUT = ROOT / "cqasm_routed"
SEND_TAGS = ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0")


def build(enc, layers, n, dae, dbm):
    qc = QuantumCircuit(n, n)
    for i, a in enumerate(enc):
        qc.ry(float(a), i)
    if dae:
        for i in range(n):
            qc.delay(int(dae), i, unit="dt")
    for layer in layers:
        for i in range(n):
            qc.cx(i, (i + 1) % n)
        for i, (ry, rz) in enumerate(layer):
            qc.ry(float(ry), i)
            qc.rz(float(rz), i)
    if dbm:
        for i in range(n):
            qc.delay(int(dbm), i, unit="dt")
    qc.measure(range(n), range(n))
    return qc


def main():
    b = QIProvider().get_backend("Tuna-17")
    OUT.mkdir(parents=True, exist_ok=True)
    man = []
    for p in sorted(DATA.rglob("*.json")):
        if "cudaq" in str(p):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        tag = d.get("tag") or p.stem
        if tag not in SEND_TAGS:
            continue
        kind = "ablation"
        dae = int(d.get("delay_after_encoding") or 0)
        dbm = int(d.get("delay_before_measure") or 0)
        n = int(d.get("n") or 5)
        sub = OUT / tag
        sub.mkdir(parents=True, exist_ok=True)
        for sm in d.get("samples") or []:
            k = sm["k"]
            enc = [float(v) for v in sm["x"]]
            layers = [[[float(g) for g in pair] for pair in lay] for lay in sm["w"]]
            qc = build(enc, layers, n, dae, dbm)
            tqc = transpile(qc, b, optimization_level=1, seed_transpiler=0)
            text = cqasm.dumps(tqc)
            (sub / ("k%02d.cq" % k)).write_text(text, encoding="utf-8")
            man.append(dict(tag=tag, k=k, kind=kind, n=n, depth=len(layers),
                            delay_after_encoding=dae, delay_before_measure=dbm,
                            path=str((sub / ("k%02d.cq" % k)).relative_to(ROOT)),
                            cx=tqc.count_ops().get("cx", 0), swap=tqc.count_ops().get("swap", 0),
                            depth_t=tqc.depth(), gates=sum(tqc.count_ops().values())))
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("產生 %d 個已路由 cQASM" % len(man))
    import collections
    c = collections.Counter(m["tag"] for m in man)
    for t, v in sorted(c.items()):
        print("  %-14s %d" % (t, v))
    if man:
        m0 = man[0]
        print()
        print("範例 %s k=%d: cx=%d swap=%d depth=%d gates=%d" % (
            m0["tag"], m0["k"], m0["cx"], m0["swap"], m0["depth_t"], m0["gates"]))


if __name__ == "__main__":
    main()
