"""關鍵對照：把「真機分布變平」歸因於硬體之前，先排除取樣雜訊。

模擬端用的是精確機率，真機是 8192 shots 的估計。有限取樣必然讓量到的分布
比真分布更平（雜訊灌進每個態）。所以必須問：**如果硬體是完美的，只是抽 8192 次，
量到的 KL 會是多少？** 若那個值仍接近模擬端的 0.166，則 0.031 就是硬體造成的。
"""
import glob, json, pathlib, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HW = pathlib.Path(r"C:\Users\snow\qi\hw")

def stats(P, y):
    kl = np.mean([np.sum(p * np.log(p / 0.125 + 1e-12)) for p in P])
    ent = np.mean([-(p * np.log(p + 1e-12)).sum() for p in P])
    return kl, ent, P[np.arange(len(y)), y].mean(), P.max(1).mean()

for path in sorted(glob.glob(str(HW / "hw_n5_d2_s0_Tuna-17_*.json"))):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    rec = json.loads((HW / (d["tag"] + ".json")).read_text(encoding="utf-8"))
    ys = np.array(d["y"])
    n_states = 1 << 5
    shots = d["shots"]

    P_sim = np.array([np.asarray(s["expected_class_probs"]) for s in rec["samples"]])
    P_hw = []
    for c in d["counts"]:
        tot = sum(c.values())
        v = np.zeros(8)
        for k, n in c.items():
            v[int(k[-3:], 2)] += n / tot
        P_hw.append(v)
    P_hw = np.array(P_hw)

    # 對照：完美硬體 + 同樣 shots 的取樣（用真機的 counts 總數，逐樣本重抽 200 次取平均）
    rng = np.random.default_rng(0)
    reps = 200
    kl_s, ent_s, py_s, mx_s = [], [], [], []
    for p in P_sim:
        acc = np.zeros(8)
        for _ in range(reps):
            cnt = rng.multinomial(shots, p) / shots
            acc += cnt
        q = acc / reps
        kl_s.append(np.sum(q * np.log(q / 0.125 + 1e-12)))
        ent_s.append(-(q * np.log(q + 1e-12)).sum())
        py_s.append(q[ys[len(kl_s) - 1]])
        mx_s.append(q.max())
    kl_s, ent_s, py_s, mx_s = map(float, (np.mean(kl_s), np.mean(ent_s), np.mean(py_s), np.mean(mx_s)))

    print("===", pathlib.Path(path).name, "===")
    print("  %-30s %10s %10s %10s" % ("指標", "模擬(精確)", "模擬@8192", "真機"))
    a = stats(P_sim, ys)
    b = stats(P_hw, ys)
    print("  %-30s %10.4f %10.4f %10.4f" % ("對均勻的 KL", a[0], kl_s, b[0]))
    print("  %-30s %10.4f %10.4f %10.4f" % ("分布熵 (最大 2.0794)", a[1], ent_s, b[1]))
    print("  %-30s %10.4f %10.4f %10.4f" % ("平均 P(真實類別)", a[2], py_s, b[2]))
    print("  %-30s %10.4f %10.4f %10.4f" % ("平均最大機率", a[3], mx_s, b[3]))
    print()
    print("  => 取樣雜訊本身造成的 KL 損失：%.4f -> %.4f（佔 %.0f%%）"
          % (a[0], kl_s, 100 * (a[0] - kl_s) / a[0]))
    print("  => 真機再額外掉的：%.4f -> %.4f（剩下的 %.0f%%）"
          % (kl_s, b[0], 100 * b[0] / kl_s))
