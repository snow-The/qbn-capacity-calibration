"""產生論文 fig:cliff：容量—效能曲線（資料來源 s16_capacity_final_5seed.json）。

為什麼用英文軸標籤：本機（WSL）沒有任何 CJK 字型（fc-list :lang=zh 為空），
中文會渲染成豆腐方塊。中文說明放在 Typst 的圖說裡，這樣也符合多數中文論文的慣例。

用法：python make_fig_cliff.py
輸出：paper/figs/cliff.svg + cliff.pdf（向量，論文用）、cliff.png（200 dpi，預覽用）
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# typography: match the LaTeX submission (Times body, STIX math)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'Nimbus Roman', 'DejaVu Serif']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.unicode_minus'] = False
import numpy as np

# 本檔放在 .../qbn-capacity-calibration/paper/ 下，路徑由 __file__ 推導
HERE = pathlib.Path(__file__).resolve().parent          # .../paper
PROJ = HERE.parent                                      # .../qbn-capacity-calibration
ML = PROJ / "ml"
FIGS = HERE / "figs"
OUT = FIGS / "cliff.png"        # 僅供快速預覽；論文引用的是向量版

NS = list(range(3, 11))
DS = list(range(1, 9))
CHANCE = 0.125
COLORS = {n: plt.get_cmap("viridis")(x) for n, x in zip(NS, np.linspace(0.04, 0.96, len(NS)))}


def series(rows, n, key):
    xs, ys, es = [], [], []
    for d in DS:
        v = [r[key] for r in rows if r["n_qubit"] == n and r["depth"] == d]
        if not v:
            continue
        xs.append(d)
        ys.append(float(np.mean(v)))
        es.append(float(np.std(v, ddof=1)) if len(v) > 1 else 0.0)
    return xs, ys, es


def main() -> int:
    data = json.loads((ML / "out" / "s16_capacity_final_5seed.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    # 每個 n 在「每一深度」的種子數。部分完成時各深度可能不同，
    # 圖例必須誠實反映，否則會宣稱比實際更多的重複次數。
    cover = {}
    for n in NS:
        cnt = [len({r["seed"] for r in rows if r["n_qubit"] == n and r["depth"] == d}) for d in DS]
        done = [c for c in cnt if c]
        cover[n] = (min(done), max(done)) if done else (0, 0)
    print("每個 n 的種子覆蓋 (min, max):", cover, "| partial =", data.get("partial"))

    def seed_label(n):
        lo, hi = cover[n]
        return f"{lo} seeds" if lo == hi else f"{lo}-{hi} seeds"

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.9), dpi=200)
    for ax, key, ylab in ((axes[0], "test_acc", "Test accuracy"),
                          (axes[1], "test_ece", "ECE")):
        for n in NS:
            xs, ys, es = series(rows, n, key)
            if not xs:
                continue
            ax.errorbar(xs, ys, yerr=es, marker="o", ms=4.5, lw=1.6, capsize=3,
                        color=COLORS[n], label=f"n = {n} ({seed_label(n)})")
        ax.set_xlabel("Circuit depth $L$")
        ax.set_ylabel(ylab)
        ax.set_xticks(DS)
        ax.grid(alpha=0.25, lw=0.6)
    axes[0].axhline(CHANCE, ls=":", c="gray", lw=1.2)
    # 放在中下方的空白處：原本放在右端會壓到圖例
    axes[0].annotate("chance = 0.125", (4.5, CHANCE - 0.006), ha="center", va="top",
                     fontsize=7.5, color="gray")
    axes[0].legend(fontsize=7.5, frameon=False, loc="lower right")
    axes[0].set_title("(a) Capacity vs. performance", fontsize=9.5)
    axes[1].set_title("(b) Calibration error", fontsize=9.5)
    fig.tight_layout()

    FIGS.mkdir(parents=True, exist_ok=True)
    # 期刊要求向量圖。SVG 是 Typst 保證支援的向量格式；
    # PDF 一併輸出，方便日後改用 LaTeX 管線。
    fig.savefig(FIGS / "cliff.svg")
    fig.savefig(FIGS / "cliff.pdf")
    fig.savefig(OUT)
    print("已寫出", FIGS / "cliff.svg", FIGS / "cliff.pdf", OUT.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
