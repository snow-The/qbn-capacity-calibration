"""drift_check.py -- 決定性對照：同一電路、不同時間的重複量測。

tau 掃描的 tau=0 區塊在電路上與臂 A 完全相同（都是那 8 個樣本、無延遲），
只是送出時間晚了約一小時。所以 A(t1) vs A(t2) 直接給出硬體漂移的量級。
任何臂差異若不大於這個漂移，就不能歸因於延遲。
"""
import collections, json, pathlib
import numpy as np

ROOT = pathlib.Path("/home/b02/qi")
NREAD = 3


def probs(counts):
    v = np.zeros(2 ** NREAD)
    tot = sum(counts.values())
    for key, c in counts.items():
        v[int(key[::-1][:NREAD], 2)] += c / tot
    return v


def met(P, Q):
    return float(np.max(np.abs(P - Q))), float(0.5 * np.sum(np.abs(P - Q)))


def load(dirname, prefix, expected_shots=None):
    r = {}
    for f in sorted((ROOT / dirname).glob(prefix + "__k*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("counts"):
            r[d["k"]] = d
    return r


def main():
    A = load("results/cqasm2", "A_n5_d2_s0")
    T0 = load("results/tau", "tau00")
    print("臂 A 紀錄 %d 筆 (shots=%s)" % (len(A), A[0]["shots"] if A else "?"))
    print("tau=0 紀錄 %d 筆 (shots=%s)" % (len(T0), T0[0]["shots"] if T0 else "?"))
    print()
    common = sorted(set(A) & set(T0))
    if not common:
        print("尚無共同樣本，等 tau=0 跑完")
        return
    rows = []
    for k in common:
        m, tv = met(probs(T0[k]["counts"]), probs(A[k]["counts"]))
        rows.append((m, tv))
        print("  k=%d  同電路異時  max|dP|=%.5f  TVD=%.5f   (job %s vs %s)"
              % (k, m, tv, T0[k]["job_id"], A[k]["job_id"]))
    a = np.array(rows)
    print()
    print("=== 同電路異時（%d 樣本）===" % len(common))
    print("  max|dP| 平均 %.5f  標準差 %.5f  最大 %.5f" % (a[:, 0].mean(), a[:, 0].std(), a[:, 0].max()))
    print("  TVD     平均 %.5f  標準差 %.5f  最大 %.5f" % (a[:, 1].mean(), a[:, 1].std(), a[:, 1].max()))
    ref = json.loads((ROOT / "results/paper_stats_hw.json").read_text(encoding="utf-8"))
    print()
    print("=== 對照 ===")
    print("  純取樣雜訊零假設 (8 樣本平均)      max|dP| = %.5f  (95%% %.5f)"
          % (ref["null_max"], ref["null_p95"]))
    print("  同電路異時漂移 (n=%d)              max|dP| = %.5f" % (len(common), a[:, 0].mean()))
    for t, v in ref["arms"].items():
        print("  %-3s 延遲臂                          max|dP| = %.5f  (%.2fx null)" % (t.split("_")[0], v["obs_max"], v["ratio"]))
    json.dump(dict(n=len(common), drift_max=float(a[:, 0].mean()), drift_tvd=float(a[:, 1].mean())),
              open(ROOT / "results/drift_check.json", "w"), indent=1)


if __name__ == "__main__":
    main()