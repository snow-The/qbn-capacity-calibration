"""把 q01 的電路送到 Quantum Inspire 真機，並與 CUDA-Q 黃金向量對帳。

分工（沿用 hardware/README 的既有模式）：
  q01（numpy≥2，練習軌）匯出 OpenQASM 2.0
      ↓  純文字，不需要在 q01 裝任何雲端 SDK
  Quantum Inspire（qiskit-quantuminspire + qi CLI）
      ↓  transpile 到目標後端 → run → counts
  與 packages/q01/tests/golden/cudaq_golden.json 比對

位元序：
  * Qiskit 的 counts 鍵是「左端為最高古典位」，
    而黃金向量的索引是狀態向量索引（q0 = 最低位）。
    所以比對前要把位元字串反轉：idx = int(bits[::-1], 2)。
  * 這一點在 Quafu 上是相反的（那裡是 big-endian），已寫進 hardware/README §7.4。

用法：
  python submit_qi.py --dry-run        # 不連網，只驗證 QASM 與比對邏輯
  python submit_qi.py --shots 8192     # 真的送出（需要先 qi login）
  python submit_qi.py --list           # 只列後端
"""
import argparse
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "packages" / "q01"
sys.path.insert(0, str(ROOT / "tools" / "oracle"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "hardware"))

import cases  # noqa: E402
from qasm_export import QasmExportError, to_qasm  # noqa: E402

GOLD = json.loads((ROOT / "tests" / "golden" / "cudaq_golden.json").read_text(encoding="utf-8"))
HERE = pathlib.Path(__file__).resolve().parent


def build_qasm(name: str) -> str:
    """從 q01 的 IR 取指定案例的 QASM。找不到就明確中止，不回退到別的東西。"""
    for cname, kernel, args in cases.trace_cases():
        if cname != name:
            continue
        trace = kernel.trace(*args, live=False)
        try:
            return to_qasm(trace, measure=True)
        except QasmExportError as exc:
            raise SystemExit("這個案例匯不出 QASM：" + str(exc))
    raise SystemExit("cases.trace_cases() 裡沒有 " + name)


def golden(name: str) -> np.ndarray:
    return np.asarray(GOLD["cases"][name]["probabilities"], dtype=float)


def counts_to_prob(counts: dict, n_qubits: int) -> np.ndarray:
    """counts -> 長度 2**n 的機率向量（索引 = 狀態向量索引，q0 為最低位）。"""
    total = sum(counts.values())
    p = np.zeros(2 ** n_qubits, dtype=float)
    for bits, c in counts.items():
        clean = bits.replace(" ", "")
        idx = int(clean[::-1], 2)          # 反轉：Qiskit 左端是最高古典位
        p[idx] += c / total
    return p


def dry_run(name: str) -> int:
    from qiskit import qasm2
    from qiskit.quantum_info import Statevector

    text = build_qasm(name)
    qc = qasm2.loads(text)
    n = qc.num_qubits
    exact = np.abs(Statevector(qc.remove_final_measurements(inplace=False)).data) ** 2
    g = golden(name)
    d = float(np.max(np.abs(exact - g)))
    print("案例:", name, "| qubit:", n, "| QASM", len(text.splitlines()), "行")
    print("  精確機率 vs 黃金向量 max|dP| = %.3e（判準 1e-10）" % d)
    print("  ==>", "OK" if d < 1e-10 else "★ 有問題")

    # 用精確機率模擬一次計數，驗證 counts_to_prob 的位元序沒有寫反
    rng = np.random.default_rng(0)
    shots = 200000
    draws = rng.choice(len(exact), size=shots, p=exact / exact.sum())
    fake = {}
    for k in draws:
        bits = format(int(k), "0%db" % n)[::-1]      # 模擬 Qiskit 的鍵順序
        fake[bits] = fake.get(bits, 0) + 1
    back = counts_to_prob(fake, n)
    d2 = float(np.max(np.abs(back - exact)))
    print("  counts 位元序自我檢查（20 萬 shots 模擬）max|dP| = %.3e" % d2)
    print("  ==>", "位元序正確" if d2 < 5e-3 else "★ 位元序可能寫反了")
    return 0


def submit(name: str, shots: int) -> int:
    from qiskit import qasm2, transpile
    from qiskit_quantuminspire.qi_provider import QIProvider

    provider = QIProvider()
    backends = provider.backends()
    print("可用後端:")
    for b in backends:
        print("   ", b)

    # 真機優先：名稱含 emulator/simulator 的先跳過，除非只剩模擬器
    real = [b for b in backends if not any(s in str(b).lower() for s in ("emulator", "simulator"))]
    target = (real or list(backends))[0]
    print("選用後端:", target)

    qc = qasm2.loads(build_qasm(name))
    compiled = transpile(qc, target)
    job = target.run(compiled, shots=shots)
    result = job.result()
    counts = result.get_counts()
    if isinstance(counts, list):
        counts = counts[0]
    print("counts:", len(counts), "個鍵，總 shots", sum(counts.values()))

    p = counts_to_prob(counts, qc.num_qubits)
    g = golden(name)
    d = float(np.max(np.abs(p - g)))
    print("真機 vs 黃金向量 max|dP| = %.3e" % d)

    out = HERE / "runs" / ("qi_" + name + "_" + str(shots) + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "backend": str(target), "shots": shots, "counts": counts,
        "max_abs_dp_vs_golden": d,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("寫出:", out)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="qbn5_book")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        return dry_run(a.case)
    if a.list:
        from qiskit_quantuminspire.qi_provider import QIProvider
        for b in QIProvider().backends():
            print("   ", b)
        return 0
    return submit(a.case, a.shots)


if __name__ == "__main__":
    raise SystemExit(main())
