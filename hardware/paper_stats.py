"""paper_stats.py -- 論文 6.3 節要的精確數字。

方法論要點：觀測量是「8 個樣本的平均 max|dP|」。
所以零假設必須是「8 個樣本平均」的分布，不是單一樣本的分布——
後者會嚴重低估檢定力，讓一個真實效應看起來不顯著。
"""
import collections, json, pathlib
import numpy as np

ROOT = pathlib.Path("/home/b02/qi")
D = ROOT / "results/cqasm2"
MAN = ROOT / "cqasm_routed/manifest.json"
TAGS = ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0")
NREAD, TRIALS = 3, 20000


def load():
    r = {}
    for f in D.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("counts") and d.get("quality_ok"):
            r[(d["tag"], d["k"])] = d
    return r


def probs(counts):
    v = np.zeros(2 ** NREAD)
    tot = sum(counts.values())
    for key, c in counts.items():
        v[int(key[::-1][:NREAD], 2)] += c / tot
    return v


def met(P, Q):
    return float(np.max(np.abs(P - Q))), float(0.5 * np.sum(np.abs(P - Q)))


def main():
    recs = load()
    man = json.loads(MAN.read_text(encoding="utf-8"))
    delays = {}
    for m in man:
        delays[m["tag"]] = (m.get("delay_after_encoding", 0), m.get("delay_before_measure", 0))
    ks = sorted({k for (_, k) in recs})
    shots = recs[("A_n5_d2_s0", ks[0])]["shots"]
    print("紀錄 %d 筆 | 樣本 k=%s | shots=%d | 讀出取前 %d qubit" % (len(recs), ks, shots, NREAD))
    print()

    obs = collections.defaultdict(list)
    PAs = {}
    for k in ks:
        if ("A_n5_d2_s0", k) not in recs:
            continue
        PA = probs(recs[("A_n5_d2_s0", k)]["counts"])
        PAs[k] = PA
        for t in TAGS:
            if (t, k) in recs:
                obs[t].append(met(probs(recs[(t, k)]["counts"]), PA))

    print("=== 觀測：各臂對 A 的差異（%d 個樣本）===" % len(ks))
    print("  臂    延遲(after,before)   max|dP| 平均    標準差    最大      TVD 平均")
    for t in TAGS:
        a = np.array(obs[t])
        dae, dbm = delays.get(t, (0, 0))
        print("  %-3s   (%5d,%6d)      %.5f   %.5f   %.5f   %.5f" % (
            t.split("_")[0], dae, dbm, a[:, 0].mean(), a[:, 0].std(), a[:, 0].max(), a[:, 1].mean()))
    print()

    # 零假設：A 與某臂同分布時，8 樣本平均 max|dP| 的分布
    rng = np.random.default_rng(20260922)
    kval = sorted(PAs)
    n_samp = len(ks)
    null_mean, null_tvd = [], []
    single = []
    for _ in range(TRIALS):
        acc, tacc = [], []
        for _ in range(n_samp):
            p = PAs[kval[rng.integers(len(kval))]]
            x = rng.multinomial(shots, p) / shots
            y = rng.multinomial(shots, p) / shots
            m, tv = met(x, y)
            acc.append(m); tacc.append(tv)
            single.append(m)
        null_mean.append(np.mean(acc)); null_tvd.append(np.mean(tacc))
    nm, nt = np.array(null_mean), np.array(null_tvd)
    sg = np.array(single)
    print("=== 零假設（同分布重抽兩次 %d shots，8 樣本平均；%d 次）===" % (shots, TRIALS))
    print("  max|dP| : 平均 %.5f  標準差 %.5f  95%% %.5f  99%% %.5f" % (
        nm.mean(), nm.std(), np.percentile(nm, 95), np.percentile(nm, 99)))
    print("  TVD     : 平均 %.5f  標準差 %.5f  95%% %.5f" % (nt.mean(), nt.std(), np.percentile(nt, 95)))
    print("  單樣本 max|dP| 對照：平均 %.5f  95%% %.5f" % (sg.mean(), np.percentile(sg, 95)))
    print()
    print("=== 判讀 ===")
    out = {}
    for t in TAGS[1:]:
        a = np.array(obs[t])
        om = a[:, 0].mean()
        p = float(np.mean(nm >= om))
        z = (om - nm.mean()) / nm.std()
        ot = a[:, 1].mean()
        pt = float(np.mean(nt >= ot))
        out[t] = dict(obs_max=om, obs_tvd=ot, null_max=float(nm.mean()),
                      ratio=om / nm.mean(), z=float(z), p_max=p, p_tvd=pt)
        print("  %-3s 觀測 %.5f | 零假設 %.5f | %.2f 倍 | z=%+.2f | p=%.3f   (TVD p=%.3f)" % (
            t.split("_")[0], om, nm.mean(), om / nm.mean(), z, p, pt))
    (ROOT / "results/paper_stats_hw.json").write_text(
        json.dumps(dict(shots=shots, n=len(ks), null_max=float(nm.mean()),
                        null_max_sd=float(nm.std()), null_p95=float(np.percentile(nm, 95)),
                        null_p99=float(np.percentile(nm, 99)), arms=out),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print("寫出 results/paper_stats_hw.json")


if __name__ == "__main__":
    main()