"""把 q01 匯出的 QASM 送到 Quantum Inspire，並與 CUDA-Q 黃金向量對帳。

分工：QASM 在筆電產（q01 與 qasm_export.py 的最新版在那裡），送出在本機做
（qi login 的憑證在這裡）。QASM 是純文字，正好當交換格式。

位元序：Qiskit 的 counts 鍵左端是最高古典位，而黃金向量的索引是狀態向量索引
（q0 = 最低位），所以比對前要反轉：idx = int(bits[::-1], 2)。

等待：QI 的 result() 預設只等 60 秒就會拋 JobTimeoutError（實測踩到），
所以這裡自己輪詢 status()，等真正結束才去取結果。

用法：
  python submit.py --backend "QX emulator" --shots 4096   # 先免費模擬器驗證流程
  python submit.py --backend "Tuna-5" --shots 4096        # 再上真機
"""
import argparse
import datetime
import json
import pathlib
import sys
import time
import warnings

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
GOLD = json.loads((HERE / "cudaq_golden.json").read_text(encoding="utf-8"))


def counts_to_prob(counts: dict, n: int) -> np.ndarray:
    total = sum(counts.values())
    p = np.zeros(2 ** n)
    for bits, c in counts.items():
        p[int(bits.replace(" ", "")[::-1], 2)] += c / total
    return p


def wait_for(job, budget_s: float):
    """自己輪詢，避開 result() 內建的 60 秒上限。"""
    t0 = time.time()
    last = None
    while time.time() - t0 < budget_s:
        st = str(job.status())
        if st != last:
            print("    [%5.0fs] status=%s" % (time.time() - t0, st))
            last = st
        if st in ("JobStatus.DONE", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            return st
        time.sleep(5)
    return "TIMEOUT"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="qbn5_book")
    ap.add_argument("--backend", default="QX emulator")
    ap.add_argument("--shots", type=int, default=4096)
    ap.add_argument("--budget", type=float, default=900.0, help="等待上限（秒）")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    from qiskit import qasm2, transpile
    from qiskit.quantum_info import Statevector
    from qiskit_quantuminspire.qi_provider import QIProvider

    provider = QIProvider()
    if a.list:
        for b in provider.backends():
            print("   %-34s qubits=%s" % (getattr(b, "name", b), getattr(b, "num_qubits", "?")))
        return 0

    text = (HERE / "qasm" / ("qasm_" + a.case + ".qasm")).read_text(encoding="utf-8")
    qc = qasm2.loads(text)
    n = qc.num_qubits
    print("案例 %s | qubit %d | QASM %d 行" % (a.case, n, len(text.splitlines())))

    clean = qc.remove_final_measurements(inplace=False)
    exact = np.abs(Statevector(clean).data) ** 2
    g = np.asarray(GOLD["cases"][a.case]["probabilities"], dtype=float)
    d0 = float(np.max(np.abs(exact - g)))
    print("  QASM 無噪聲 vs 黃金向量 max|dP| = %.3e  ==> %s" % (d0, "OK" if d0 < 1e-10 else "★ 中止"))
    if d0 >= 1e-10:
        return 2

    backend = provider.get_backend(a.backend)

    # 上限防護：超過 max_shots 的任務不會報錯，只會一直卡在佇列裡。
    # 實測：QX emulator（上限 2048）送 4096 shots，等了 1800 秒仍未完成；
    # 同一時間 Tuna-17（上限 131072）的 8192 shots 100 秒就跑完。
    limit = getattr(backend, "max_shots", None)
    if limit is not None and a.shots > limit:
        raise SystemExit("★ --shots %d 超過 %s 的上限 %d（超過不會報錯，只會卡住）"
                         % (a.shots, getattr(backend, "name", a.backend), limit))
    compiled = transpile(qc, backend)
    print("後端 %s | 轉譯後深度 %s | 閘數 %s"
          % (getattr(backend, "name", a.backend), compiled.depth(), sum(compiled.count_ops().values())))

    job = backend.run(compiled, shots=a.shots)
    print("  已送出 job_id=%r" % (job.job_id(),))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        st = wait_for(job, a.budget)
        print("  最終狀態:", st)
        if st == "TIMEOUT":
            print("  ★ 在 %ds 內沒結束；job 仍在系統上，可稍後再查" % a.budget)
            return 3
        result = job.result(wait_for_results=False)

    msgs = getattr(result, "system_messages", None)
    if msgs:
        print("  system_messages:", json.dumps(msgs, ensure_ascii=False)[:400])
    for w in caught:
        print("  警告:", str(w.message)[:300])

    counts = result.get_counts()
    if isinstance(counts, list):
        counts = counts[0]
    if not counts:
        print("  ★ 沒有 counts —— 上面若顯示 FAILED，請看 system_messages")
        return 4
    print("  回來 %d 個鍵，總 shots %d" % (len(counts), sum(counts.values())))

    p = counts_to_prob(counts, n)
    d = float(np.max(np.abs(p - g)))
    print("  %s vs 黃金向量 max|dP| = %.3e（%d shots 的取樣雜訊約 %.1e）"
          % (a.backend, d, a.shots, (1.0 / a.shots) ** 0.5))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = HERE / ("qi_" + a.case + "_" + a.backend.replace(" ", "_") + "_" + str(a.shots) + "_" + stamp + ".json")
    out.write_text(json.dumps({
        "case": a.case, "backend": a.backend, "shots": a.shots, "counts": counts,
        "max_abs_dp_vs_golden": d, "qasm_lines": len(text.splitlines()), "sent_at": stamp,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  寫出:", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
