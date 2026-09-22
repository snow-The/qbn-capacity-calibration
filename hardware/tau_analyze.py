"""tau_analyze.py -- 延遲劑量反應的定案分析（兩個零假設）。

零假設有兩個，而且第二個才是對的：
  (a) 多項式（純取樣）零假設：把 tau=0 的實測分布當母體重抽兩次 65536 shots。
      這回答「統計上能分辨多小」。
  (b) 同電路異時重複性：兩條掃描的 tau=0 是*逐閘相同*的電路、同樣 shots，
      只是不同時間送出。它們之間的差異給出「這台裝置在同一個設定下重做一次」
      的實際散布。真機的隨機性不只來自 shot，還有漂移與校準變化。
任何小於 (b) 的效應都不能歸因於延遲。
"""
import collections, json, pathlib, sys
import numpy as np

ROOT = pathlib.Path("/home/b02/qi")
SHOTS, TRIALS, NBIN = 65536, 20000, 32


def load(dirname, tags):
    out = {}
    for tag, tau in tags:
        for f in sorted((ROOT / dirname).glob(tag + "__k*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(d, dict) and d.get("counts"):
                out.setdefault(tau, {})[int(d["k"])] = d["counts"]
    return out


def dist(counts):
    v = np.zeros(NBIN)
    tot = sum(counts.values()) or 1
    for key, c in counts.items():
        v[int(key[::-1], 2)] += c / tot
    return v


def met(P, Q):
    return float(np.max(np.abs(P - Q))), float(0.5 * np.sum(np.abs(P - Q)))


def kl_uniform(P):
    u = 1.0 / len(P)
    return float(np.sum(P * np.log((P + 1e-15) / u)))


def p00000(counts):
    return counts.get("00000", 0) / max(sum(counts.values()), 1)


def main():
    s1 = load("results/tau", [("tau00", 0), ("tau01", 1), ("tau04", 4), ("tau16", 16), ("tau64", 64)])
    s2 = load("results/tau2", [("tau00000", 0), ("tau00256", 256), ("tau01024", 1024),
                               ("tau04096", 4096), ("tau16384", 16384), ("tau65536", 65536)])
    ref0 = dict(s1.get(0, {}))
    for k, v in s2.get(0, {}).items():
        ref0.setdefault(k, v)
    if not ref0:
        print("沒有 tau=0 資料")
        return 1
    print("參考 tau=0 樣本數: %d (scan1=%d, scan2=%d)" % (len(ref0), len(s1.get(0, {})), len(s2.get(0, {}))))

    # (b) 同電路異時重複性
    rep = []
    for k in sorted(set(s1.get(0, {})) & set(s2.get(0, {}))):
        m, t = met(dist(s2[0][k]), dist(s1[0][k]))
        rep.append(m)
        print("  同電路異時 k=%d  max|dP|=%.5f  TVD=%.5f" % (k, m, t))
    REP = float(np.mean(rep)) if rep else float("nan")
    print("  -> 同電路異時重複性 (n=%d): 平均 %.5f  最大 %.5f" % (len(rep), REP, max(rep) if rep else float("nan")))
    print()

    # 組資料
    data = {}
    for tau, ks in list(s1.items()) + list(s2.items()):
        data.setdefault(tau, {}).update(ks)
    ordered = sorted(t for t in data if t != 0)
    ks_common = sorted(ref0)
    rows = []
    for tau in ordered:
        ks = [k for k in ks_common if k in data[tau]]
        if not ks:
            continue
        m = [met(dist(data[tau][k]), dist(ref0[k])) for k in ks]
        rows.append(dict(
            tau=tau, n=len(ks),
            p00000=float(np.mean([p00000(data[tau][k]) for k in ks])),
            maxdp=float(np.mean([x[0] for x in m])),
            tvd=float(np.mean([x[1] for x in m])),
            kl=float(np.mean([kl_uniform(dist(data[tau][k])) for k in ks])),
        ))
    p0 = float(np.mean([p00000(ref0[k]) for k in ks_common]))
    print("=== 劑量反應（32 維讀出分布，參考 tau=0）===")
    print("  tau      n   P(00000)   max|dP|    TVD     KL(u)")
    kl0 = float(np.mean([kl_uniform(dist(ref0[k])) for k in ks_common]))
    print("  %-7d %2d   %.5f   %.5f  %.5f  %.5f   <- 參考" % (0, len(ks_common), p0, 0.0, 0.0, kl0))
    for r in rows:
        print("  %-7d %2d   %.5f   %.5f  %.5f  %.5f" % (r["tau"], r["n"], r["p00000"], r["maxdp"], r["tvd"], r["kl"]))
    print()

    # (a) 多項式零假設，每個 n 一組
    rng = np.random.default_rng(7)
    refs = [dist(ref0[k]) for k in ks_common]
    ns = sorted({r["n"] for r in rows})
    NULLS = {}
    for n in ns:
        acc0 = []
        for _ in range(TRIALS):
            acc = []
            for _ in range(n):
                p = refs[rng.integers(len(refs))]
                x = rng.multinomial(SHOTS, p) / SHOTS
                y = rng.multinomial(SHOTS, p) / SHOTS
                acc.append(met(x, y)[0])
            acc0.append(float(np.mean(acc)))
        NULLS[n] = np.array(acc0)
        print("  (a) 多項式零假設 n=%d：%.5f +- %.5f  95%% %.5f" % (n, NULLS[n].mean(), NULLS[n].std(), np.percentile(NULLS[n], 95)))
    print("  (b) 同電路異時重複性      ：%.5f  (n=%d, 這是真機的實際下限)" % (REP, len(rep)))
    print()
    print("=== 判讀（同時對兩個零假設）===")
    for r in rows:
        nm = NULLS[r["n"]]
        r["ratio_shot"] = r["maxdp"] / nm.mean()
        r["p_shot"] = float(np.mean(nm >= r["maxdp"]))
        r["ratio_rep"] = r["maxdp"] / REP if REP == REP else float("nan")
        r["above_rep"] = bool(REP == REP and r["maxdp"] > REP)
        print("  tau=%-7d max|dP| %.5f | %6.2fx shot null | %5.2fx 重複性 | 超過重複性: %s"
              % (r["tau"], r["maxdp"], r["ratio_shot"], r["ratio_rep"], "是" if r["above_rep"] else "否"))
    (ROOT / "results/tau_dose.json").write_text(
        json.dumps(dict(rows=rows, p0=p0, n_ref=len(ks_common),
                        null_shot={str(n): dict(mean=float(NULLS[n].mean()), sd=float(NULLS[n].std()),
                                               p95=float(np.percentile(NULLS[n], 95))) for n in ns},
                        null_repeat=dict(mean=REP, n=len(rep), values=rep), shots=SHOTS,
                        kl0=kl0),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print("=== Typst 表格列 (tau, P(00000), max|dP|, TVD, KL) ===")
    print("  [0], [%.5f], [0.00000], [0.00000], [%.5f]," % (p0, kl0))
    for r in rows:
        print("  [%d], [%.5f], [%.5f], [%.5f], [%.5f]," % (r["tau"], r["p00000"], r["maxdp"], r["tvd"], r["kl"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())