"""取樣雜訊對照：A 與 C 的差異，有多少是純統計造成的？

專案的教訓：報一個差異之前，先報「純雜訊下該差異的期望值」。
做法：把 A 的實測分布當母體，重抽兩次 8192 shots，算 max|dP| 與 TVD。
      重複很多次得到零假設下的分布，再跟實測的 A vs C 比。
"""
import json, pathlib, collections
import numpy as np

ROOT = pathlib.Path("/home/b02/qi")
D = ROOT / "results/cqasm2"
TAGS = ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0")
NREAD, SHOTS, TRIALS = 3, 8192, 4000

def load():
    r = {}
    for f in D.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("counts") and d.get("quality_ok"):
            r[(d["tag"], d["k"])] = d["counts"]
    return r

def probs(counts):
    v = np.zeros(2 ** NREAD)
    tot = sum(counts.values())
    for key, c in counts.items():
        v[int(key[::-1][:NREAD], 2)] += c / tot
    return v

def raw_probs(counts):
    """不反轉的版本（給重抽用，公約不影響統計量）。"""
    v = np.zeros(2 ** NREAD)
    tot = sum(counts.values())
    for key, c in counts.items():
        v[int(key[-NREAD:], 2)] += c / tot
    return v

def metrics(P, Q):
    return float(np.max(np.abs(P - Q))), float(0.5 * np.sum(np.abs(P - Q)))

def main():
    recs = load()
    rng = np.random.default_rng(0)
    print("=== 觀測到的 A vs 各臂 ===")
    obs = collections.defaultdict(list)
    for k in sorted({k for (_, k) in recs}):
        if ("A_n5_d2_s0", k) not in recs:
            continue
        PA = probs(recs[("A_n5_d2_s0", k)])
        for t in TAGS[1:]:
            if (t, k) in recs:
                obs[t].append(metrics(probs(recs[(t, k)]), PA))
    for t in TAGS[1:]:
        a = np.array(obs[t])
        print("  %-13s max|dP| = %.5f ± %.5f | TVD = %.5f" % (
            t.split("_")[0], a[:, 0].mean(), a[:, 0].std(), a[:, 1].mean()))
    print()
    print("=== 純取樣雜訊的零假設分布（把 A 當母體，重抽兩次 %d shots）===" % SHOTS)
    null_max, null_tvd = [], []
    for k in sorted({k for (_, k) in recs}):
        if ("A_n5_d2_s0", k) not in recs:
            continue
        p = raw_probs(recs[("A_n5_d2_s0", k)])
        for _ in range(TRIALS // 8):
            x = rng.multinomial(SHOTS, p) / SHOTS
            y = rng.multinomial(SHOTS, p) / SHOTS
            m, tv = metrics(x, y)
            null_max.append(m); null_tvd.append(tv)
    nm, nt = np.array(null_max), np.array(null_tvd)
    print("  max|dP| : 平均 %.5f  中位數 %.5f  95%% 分位 %.5f" % (
        nm.mean(), np.median(nm), np.percentile(nm, 95)))
    print("  TVD     : 平均 %.5f  中位數 %.5f  95%% 分位 %.5f" % (
        nt.mean(), np.median(nt), np.percentile(nt, 95)))
    print()
    print("=== 判讀：觀測值 vs 零假設 ===")
    for t in TAGS[1:]:
        a = np.array(obs[t])
        z_max = (a[:, 0].mean() - nm.mean()) / (nm.std() / np.sqrt(len(a))) if nm.std() > 0 else 0
        p_max = float(np.mean(nm >= a[:, 0].mean()))
        print("  %-13s 觀測 %.5f | 零假設 %.5f | 超出 %.1f 倍 | p(>=觀測) = %.3f" % (
            t.split("_")[0], a[:, 0].mean(), nm.mean(),
            a[:, 0].mean() / nm.mean() if nm.mean() else 0, p_max))

if __name__ == "__main__":
    main()
