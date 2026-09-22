"""tau_fig.py -- 延遲劑量反應圖（純手寫 SVG，無需 matplotlib）。

讀 results/tau_dose.json，畫兩個面板：
  (a) max|dP| 對 tau（對數 x 軸），含純取樣零假設的 95% 帶、以及同電路異時重複性的水平線
  (b) P(00000) 對 tau，T1 弛豫造成的質量集中
tau=0 以左緣的獨立刻度表示。
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "figs/tau_dose.svg"

W, H = 1000, 390
PAD_L, PAD_R, PAD_T, PAD_B = 74, 26, 36, 54
GAP = 80
PW = (W - PAD_L - PAD_R - GAP) / 2
PH = H - PAD_T - PAD_B
TMAX = 65536.0
FONT = "Times New Roman, Liberation Serif, serif"


def xpos(tau, x0):
    if tau <= 0:
        return x0 + 7
    return x0 + 20 + (PW - 36) * (math.log10(tau) / math.log10(TMAX))


def panel(series, x0, y0, title, ylab, ymax, band=None, hline=None, hlabel="", fmt="%.4f"):
    o = []
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#333" stroke-width="1"/>' % (x0, y0, PW, PH))
    o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="13" text-anchor="middle">%s</text>' % (x0 + PW / 2, y0 - 11, FONT, title))
    for i in range(5):
        v = ymax * i / 4.0
        yy = y0 + PH - PH * i / 4.0
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#dddddd" stroke-width="1"/>' % (x0, yy, x0 + PW, yy))
        o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="10" text-anchor="end">%s</text>' % (x0 - 6, yy + 3, FONT, fmt % v))
    o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" text-anchor="middle" transform="rotate(-90 %.1f %.1f)">%s</text>' % (x0 - 50, y0 + PH / 2, FONT, x0 - 50, y0 + PH / 2, ylab))
    if band is not None:
        lo, hi = band
        y1 = y0 + PH - PH * min(hi, ymax) / ymax
        y2 = y0 + PH - PH * min(lo, ymax) / ymax
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#cfe3f7" opacity="0.6"/>' % (x0, y1, PW, max(y2 - y1, 1.2)))
    if hline is not None and hline < ymax:
        yy = y0 + PH - PH * hline / ymax
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c0392b" stroke-width="1.4" stroke-dasharray="5,3"/>' % (x0, yy, x0 + PW, yy))
        o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="9.5" fill="#c0392b">%s</text>' % (x0 + PW - 6, yy - 4, FONT, hlabel))
    ticks = [0, 1, 4, 16, 64, 256, 1024, 4096, 16384, 65536]
    for t in ticks:
        xx = xpos(t, x0)
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" stroke-width="1"/>' % (xx, y0 + PH, xx, y0 + PH + 4))
        lab = "0" if t == 0 else ("%d" % t)
        o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="9" text-anchor="middle">%s</text>' % (xx, y0 + PH + 16, FONT, lab))
    o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" text-anchor="middle">wait cycles (log scale)</text>' % (x0 + PW / 2, y0 + PH + 38, FONT))
    pts = [(xpos(t, x0), y0 + PH - PH * min(v, ymax) / ymax) for (t, v) in series]
    o.append('<polyline points="%s" fill="none" stroke="#12507b" stroke-width="1.9"/>' % " ".join("%.1f,%.1f" % p for p in pts))
    for (px, py) in pts:
        o.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="#12507b"/>' % (px, py))
    return o


def main():
    d = json.loads((ROOT / "results/tau_dose.json").read_text(encoding="utf-8"))
    rows = sorted(d["rows"], key=lambda r: r["tau"])
    ns = d["null_shot"]
    nmax = max(ns, key=lambda k: int(k))
    nb = ns[nmax]
    lo = max(nb["mean"] - 1.96 * nb["sd"], 0.0)
    hi = nb["mean"] + 1.96 * nb["sd"]
    rep = float(d["null_repeat"]["mean"])
    p0 = float(d["p0"])
    md = max([r["maxdp"] for r in rows] + [hi, rep]) * 1.14
    pd_ = max(r["p00000"] for r in rows) * 1.12
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]
    o += panel([(r["tau"], r["maxdp"]) for r in rows], PAD_L, PAD_T,
               "(a) deviation from the undelayed circuit", "max |\u0394P|", md,
               band=(lo, hi), hline=rep, hlabel="device repeatability")
    o += panel([(r["tau"], r["p00000"]) for r in rows], PAD_L + PW + GAP, PAD_T,
               "(b) mass concentrating on 00000", "P(00000)", pd_,
               hline=None, fmt="%.3f")
    o.append('<rect x="%.1f" y="%.1f" width="15" height="9" fill="#cfe3f7" opacity="0.6" stroke="#8fb8dd"/>' % (PAD_L + 10, PAD_T + 12))
    o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="9.5">95%% shot-noise interval</text>' % (PAD_L + 30, PAD_T + 20, FONT))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c0392b" stroke-width="1.4" stroke-dasharray="5,3"/>' % (PAD_L + 10, PAD_T + 30, PAD_L + 25, PAD_T + 30))
    o.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="9.5" fill="#c0392b">device repeatability</text>' % (PAD_L + 30, PAD_T + 34, FONT))
    o.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(o), encoding="utf-8")
    print("wrote %s" % OUT)
    print("  shot-noise n=%s: %.5f +- %.5f  band %.5f..%.5f" % (nmax, nb["mean"], nb["sd"], lo, hi))
    print("  repeatability: %.5f" % rep)
    print("  tau=0 P(00000)=%.5f" % p0)


if __name__ == "__main__":
    main()