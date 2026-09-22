"""分析真機資料：檢驗論文 3.6 節的可證偽預測。

預測：理想的去相位是精確通道，尾端去相位（臂 C）應該與無通道（臂 A）
      **逐位元相同**。真機上 T1 振幅衰減會改變對角元，所以那個相等會被破壞，
      而**破壞的量本身就是可量測的硬體特性**。
"""
import json, pathlib, collections, math
import numpy as np

ROOT = pathlib.Path("/home/b02/qi")
D = ROOT / "results/cqasm2"
TAGS = ("A_n5_d2_s0", "B1_n5_d2_s0", "B4_n5_d2_s0", "C1_n5_d2_s0", "C4_n5_d2_s0")
NREAD = 3          # 讀出用前 3 個邏輯 qubit

def load():
    recs = {}
    for f in sorted(D.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("counts") or not d.get("quality_ok"):
            continue
        recs[(d["tag"], d["k"])] = d
    return recs

def probs(counts, n):
    """QI 的字串是 Qiskit 公約（最左＝最高古典位元）。
    反轉之後，第 i 個字元 = 邏輯 qubit i。再取前 NREAD 個當類別索引。"""
    v = np.zeros(2 ** NREAD)
    tot = sum(counts.values())
    for key, c in counts.items():
        q = key[::-1]                 # 轉成 q[0] 在最左
        v[int(q[:NREAD], 2)] += c / tot
    return v

def purity(P):
    """以類別分布的平方和當「態純度」的下界代理（真機無完整密度矩陣）。"""
    return float(np.sum(P ** 2))

def kl_uniform(P):
    u = 1.0 / len(P)
    return float(np.sum(P * np.log((P + 1e-12) / u)))

def main():
    recs = load()
    print("可用紀錄: %d" % len(recs))
    by_tag = collections.Counter(t for (t, _) in recs)
    for t in TAGS:
        print("  %-14s %d" % (t, by_tag.get(t, 0)))
    ks = sorted({k for (_, k) in recs})
    print("  樣本 k: %s" % ks)
    print()
    print("=== 每個樣本：A 與各臂的差異（32 維機率、讀出取前 3 qubit）===")
    print("  k   臂    max|dP|      TVD      KL    純度   AC 逐位元相同?")
    rows = []
    for k in ks:
        if ("A_n5_d2_s0", k) not in recs:
            continue
        PA = probs(recs[("A_n5_d2_s0", k)]["counts"], NREAD)
        CA = recs[("A_n5_d2_s0", k)]["counts"]
        for tag in TAGS:
            if (tag, k) not in recs:
                continue
            P = probs(recs[(tag, k)]["counts"], NREAD)
            C = recs[(tag, k)]["counts"]
            d = float(np.max(np.abs(P - PA)))
            tvd = float(0.5 * np.sum(np.abs(P - PA)))
            kl = kl_uniform(P)
            same = (C == CA)
            rows.append(dict(k=k, tag=tag, maxdp=d, tvd=tvd, kl=kl,
                             purity=purity(P), bitwise_same=same))
            print("  %-3d %-13s %.5f  %.5f  %.4f  %.5f  %s" % (
                k, tag.replace("_n5_d2_s0", ""), d, tvd, kl, purity(P),
                "是" if same else "否"))
    (ROOT / "results/ablation_hw_analysis.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print("=== 彙總（對照論文的模擬預測）===")
    for tag in TAGS:
        rs = [r for r in rows if r["tag"] == tag]
        if not rs:
            continue
        print("  %-13s max|dP| 平均 %.5f  最大 %.5f | TVD 平均 %.5f | 逐位元相同 %d/%d" % (
            tag.replace("_n5_d2_s0", ""),
            np.mean([r["maxdp"] for r in rs]), max(r["maxdp"] for r in rs),
            np.mean([r["tvd"] for r in rs]),
            sum(1 for r in rs if r["bitwise_same"]), len(rs)))

if __name__ == "__main__":
    main()
