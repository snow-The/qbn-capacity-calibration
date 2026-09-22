"""真機分類器結果的正確讀法。

為什麼不能只看 argmax 準確率：真機回來的最大機率只有 0.144–0.242（8 類均勻 = 0.125），
分布幾乎被壓平，argmax 等於在雜訊裡挑一個 —— 16 個樣本量到的「準確率」不可信。
正確做法是用完整機率向量：真機給真實類別的機率 P(y|x) 才是它真正攜帶的資訊。
"""
import glob, json, pathlib, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HW = pathlib.Path(r"C:\Users\snow\qi\hw")

for path in sorted(glob.glob(str(HW / "hw_n5_d2_s0_Tuna-17_*.json"))):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    counts, ys = d["counts"], d["y"]
    rec = json.loads((HW / (d["tag"] + ".json")).read_text(encoding="utf-8"))
    P_hw, P_sim = [], []
    for c, s in zip(counts, rec["samples"]):
        tot = sum(c.values())
        v = np.zeros(8)
        for k, n in c.items():
            v[int(k[-3:], 2)] += n / tot
        P_hw.append(v)
        P_sim.append(np.asarray(s["expected_class_probs"]))
    P_hw, P_sim = np.array(P_hw), np.array(P_sim)
    y = np.array(ys)
    print("===", pathlib.Path(path).name, "===")
    print("  電路 %s | shots=%d | 樣本=%d" % (d["tag"], d["shots"], len(ys)))
    print()
    print("  %-26s %8s %8s" % ("指標", "模擬", "真機"))
    print("  %-26s %8.4f %8.4f" % ("argmax 準確率", (P_sim.argmax(1) == y).mean(), (P_hw.argmax(1) == y).mean()))
    print("  %-26s %8.4f %8.4f" % ("平均 P(真實類別)  <- 關鍵", P_sim[np.arange(len(y)), y].mean(), P_hw[np.arange(len(y)), y].mean()))
    print("  %-26s %8.4f %8.4f" % ("平均最大機率", P_sim.max(1).mean(), P_hw.max(1).mean()))
    print("  %-26s %8.4f %8.4f" % ("分布熵 (nats)", -(P_sim * np.log(P_sim + 1e-12)).sum(1).mean(), -(P_hw * np.log(P_hw + 1e-12)).sum(1).mean()))
    print("  %-26s %8.4f %8.4f" % ("對均勻的 KL", np.mean([np.sum(p * np.log(p / 0.125 + 1e-12)) for p in P_sim]), np.mean([np.sum(p * np.log(p / 0.125 + 1e-12)) for p in P_hw])))
    print()
    print("  均勻分布 = 0.1250；最大熵 = %.4f nats" % np.log(8))
    lift = P_hw[np.arange(len(y)), y].mean() / 0.125
    print("  真機對真實類別的平均機率是均勻的 %.2f 倍" % lift)
    # 二項檢定：真機 P(y) 的平均是否顯著高於 0.125
    from math import sqrt
    m, se = P_hw[np.arange(len(y)), y].mean(), P_hw[np.arange(len(y)), y].std(ddof=1) / sqrt(len(y))
    print("  單樣本 t = %.2f（H0: 平均 P(y) = 0.125）" % ((m - 0.125) / se))
