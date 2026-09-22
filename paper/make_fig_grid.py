"""fig:grid —— n × L 完整二維網格的熱圖版本。

為什麼要有這一版：
  8 個 qubit 數 × 8 個深度 = 64 格，畫成 8 條折線會很亂，看不出二維結構。
  熱圖讓顏色承載數值，「哪個 (n, L) 組合最好」一眼可見；
  每格再標上精確數字，需要查值時不必回頭翻 JSON。
  完整的數據表另附於論文附錄（熱圖給形狀，表格給精確值）。

誠實性要求：**沒有資料的格子留白，不填 0**。
  填 0 會讓「還沒跑」被誤讀成「表現為零」，那是兩件完全不同的事。

用法：python make_fig_grid.py
輸出：paper/figs/grid.svg + grid.pdf（向量，論文用）、grid.png（預覽用）
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
PROJ = HERE.parent
ML = PROJ / "ml"
FIGS = HERE / "figs"
OUT = FIGS / "grid.png"         # 僅供快速預覽；論文引用的是向量版

NS = list(range(3, 11))
DS = list(range(1, 9))
CHANCE = 0.125


def grid(rows, key):
    """回傳 (n × L) 矩陣；沒有資料的格子是 NaN。"""
    m = np.full((len(NS), len(DS)), np.nan)
    for i, n in enumerate(NS):
        for j, d in enumerate(DS):
            v = [r[key] for r in rows if r["n_qubit"] == n and r["depth"] == d]
            if v:
                m[i, j] = float(np.mean(v))
    return m


def heat(ax, m, title, cmap, vmin, vmax, fmt="%.3f"):
    mm = np.ma.masked_invalid(m)
    cm = plt.get_cmap(cmap).copy()
    cm.set_bad("#f0f0f0")                      # 缺資料 = 淺灰，不是 0
    im = ax.imshow(mm, cmap=cm, aspect="auto", vmin=vmin, vmax=vmax,
                   origin="lower", extent=(0.5, len(DS) + 0.5, NS[0] - 0.5, NS[-1] + 0.5))
    lo, hi = np.nanmin(m), np.nanmax(m)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if np.isnan(m[i, j]):
                ax.text(j + 1, NS[i], "—", ha="center", va="center",
                        fontsize=6.5, color="#999999")
                continue
            rel = (m[i, j] - lo) / (hi - lo) if hi > lo else 0.5
            ax.text(j + 1, NS[i], fmt % m[i, j], ha="center", va="center", fontsize=6.2,
                    color="white" if rel < 0.55 else "black")
    ax.set_xticks(DS)
    ax.set_yticks(NS)
    ax.set_xlabel("Circuit depth $L$")
    ax.set_ylabel("Number of qubits $n$")
    ax.set_title(title, fontsize=9.5)
    return im


def main() -> int:
    data = json.loads((ML / "out" / "s16_capacity_final_5seed.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    acc = grid(rows, "test_acc")
    ece = grid(rows, "test_ece")
    filled = int(np.count_nonzero(~np.isnan(acc)))
    print("格數 %d/%d 有資料 | partial = %s" % (filled, acc.size, data.get("partial")))

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.0), dpi=200,
                             gridspec_kw={"width_ratios": [1, 1, 0.85]})

    im0 = heat(axes[0], acc, "(a) Test accuracy over the $(n, L)$ grid", "viridis",
               CHANCE, float(np.nanmax(acc)))
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.02)
    im1 = heat(axes[1], ece, "(b) Calibration error (ECE)", "magma",
               0.0, float(np.nanmax(ece)))
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.02)

    # (c) 直接檢驗「測試準確率隨 qubit 數下降」：固定深度切面
    for d, c in ((4, "#1f77b4"), (6, "#ff7f0e"), (8, "#d62728")):
        xs = [n for i, n in enumerate(NS) if not np.isnan(acc[i, DS.index(d)])]
        ys = [acc[NS.index(n), DS.index(d)] for n in xs]
        if xs:
            axes[2].plot(xs, ys, marker="o", ms=4.5, lw=1.6, color=c, label=f"$L$ = {d}")
    axes[2].axhline(CHANCE, ls=":", c="gray", lw=1.1)
    axes[2].set_xlabel("Number of qubits $n$")
    axes[2].set_ylabel("Test accuracy")
    axes[2].set_xticks(NS)
    axes[2].grid(alpha=0.25, lw=0.6)
    # 圖例放左下：L=4/6/8 這三條切面最低也才 0.32，左下方到隨機線之間是空的
    axes[2].legend(fontsize=7.5, frameon=False, loc="lower left")
    axes[2].set_title("(c) Accuracy vs. $n$ at fixed depth", fontsize=9.5)
    fig.tight_layout()

    FIGS.mkdir(parents=True, exist_ok=True)
    # 期刊要求向量圖；SVG 是 Typst 保證支援的向量格式。
    fig.savefig(FIGS / "grid.svg")
    fig.savefig(FIGS / "grid.pdf")
    fig.savefig(OUT)
    print("已寫出", FIGS / "grid.svg", FIGS / "grid.pdf", OUT.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
