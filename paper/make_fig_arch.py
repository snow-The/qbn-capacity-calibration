"""fig:arch —— 系統架構圖（向量輸出）。

為什麼要這張圖：論文的「方法 → 系統架構」小節原本只放一個灰色佔位框
（「此處插入架構圖」），那是投稿前必須補掉的空洞。既有素材
`docs/assets/diagrams/qbn-pipeline.html` 是給書站台用的互動式 HTML，
不是向量圖，無法直接進 Typst。

為什麼不用 cetz：cetz 要從 packages.typst.org 下載，離線或無網路時編譯會失敗；
改用 matplotlib 直接產生向量 PDF，零外部依賴，且與其他兩張圖同一套管線。

正確性要求：圖上只畫論文明確主張的東西——
  * 讀出永遠取前 3 個 qubit（與 n、L 無關）
  * 去相位通道插在「含 R_Y 的層之前」才觀測得到（插在尾端機率變化 1.4e-17）

用法：python make_fig_arch.py
輸出：paper/figs/arch.pdf（向量，論文用）、paper/figs/arch.png（預覽用）
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = pathlib.Path(__file__).resolve().parent
FIGS = HERE / "figs"

# 與論文裡彩色區塊同一組顏色，讓圖與正文視覺一致
BLUE_FACE, BLUE_EDGE = "#eef6ff", "#4a7fb5"
ORANGE = "#c86400"
GREY_EDGE = "#5a5a5a"

XMAX, YMAX = 100.0, 30.0


def box(ax, x0, y0, w, h, face, edge, lw=1.0, dashed=False):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=0,rounding_size=0.7",
        linewidth=lw, edgecolor=edge, facecolor=face,
        linestyle=(0, (3.5, 2.2)) if dashed else "solid",
        mutation_aspect=YMAX / XMAX,   # 非等比座標下維持圓角比例
    ))


def label(ax, x, y, lines, size=6.6, color="black"):
    """lines[0] 是標題（粗體），其餘是說明行。"""
    n = len(lines)
    step = 1.6
    y0 = y + (n - 1) * step / 2.0
    for i, t in enumerate(lines):
        ax.text(x, y0 - i * step, t, ha="center", va="center",
                fontsize=size, fontweight="bold" if i == 0 else "normal",
                color=color if i == 0 else "#333333")


def arrow(ax, p, q, color="#444444", lw=1.0, ls="solid"):
    ax.add_patch(FancyArrowPatch(
        p, q, arrowstyle="-|>", mutation_scale=9,
        linewidth=lw, color=color, linestyle=ls,
        shrinkA=0, shrinkB=0,
    ))


def main() -> int:
    fig, ax = plt.subplots(figsize=(10.2, 3.7), dpi=200)
    ax.set_xlim(0, XMAX)
    ax.set_ylim(0, YMAX)
    ax.axis("off")

    # ---- 第一列：完整管線（左到右） ----
    y0, h = 20.4, 6.0
    yc = y0 + h / 2.0
    n_box, gap = 6, 2.4
    w = (XMAX - 1.0 - (n_box - 1) * gap) / n_box
    xs = [0.5 + i * (w + gap) for i in range(n_box)]

    stages = [
        (["Text input"], "white", GREY_EDGE),
        (["Static embedding", "potion-multilingual-128M", "(256-d)"], "white", GREY_EDGE),
        (["PCA reduction", "(k dims)"], "white", GREY_EDGE),
        (["Quantum layer", "(n qubits, depth L)"], BLUE_FACE, BLUE_EDGE),
        (["Measurement", "(first 3 qubits)"], BLUE_FACE, BLUE_EDGE),
        (["Readout", "(8 classes)"], "white", GREY_EDGE),
    ]
    for x, (lines, face, edge) in zip(xs, stages):
        box(ax, x, y0, w, h, face, edge, lw=1.1)
        label(ax, x + w / 2.0, yc, lines)
    for i in range(n_box - 1):
        arrow(ax, (xs[i] + w, yc), (xs[i + 1], yc))

    # ---- 古典／量子分界線 ----
    xsplit = xs[3] - gap / 2.0
    ax.plot([xsplit, xsplit], [y0 - 1.6, y0 + h + 1.0], color="#9a9a9a",
            lw=0.9, ls=(0, (2.5, 2.0)))
    ax.text(xsplit - 0.8, y0 + h + 2.0, "classical front end",
            ha="right", va="center", fontsize=6.2, color="#666666")
    ax.text(xsplit + 0.8, y0 + h + 2.0, "quantum layer (simulated)",
            ha="left", va="center", fontsize=6.2, color=BLUE_EDGE)

    # ---- 第二列：量子層展開（把第一列的第 4 格打開給讀者看） ----
    dx0, dx1, dy0, dy1 = 46.0, 93.0, 3.0, 16.0
    box(ax, dx0, dy0, dx1 - dx0, dy1 - dy0, "#fbfbfb", "#9a9a9a", lw=0.9, dashed=True)
    ax.text(dx0 + 1.6, dy1 - 1.4, "Quantum layer, expanded",
            ha="left", va="center", fontsize=7.0, fontweight="bold")

    sx0, sx1 = dx0 + 1.6, dx1 - 1.6
    sy0, sy1 = 6.0, 12.0
    sg = 1.5
    sw = (sx1 - sx0 - 2 * sg) / 3.0
    subs = [
        ["Angle encoding", r"$R_Y(\theta_i)=2\arcsin\sqrt{x_i}$"],
        ["Ring entangler", r"$CX$: $q_i \to q_{i+1}$"],
        ["Trainable block", r"$R_Y\!\cdot\! R_Z$, repeated $L$ times"],
    ]
    for i, lines in enumerate(subs):
        x = sx0 + i * (sw + sg)
        box(ax, x, sy0, sw, sy1 - sy0, "white", "#7a7a7a", lw=0.9)
        label(ax, x + sw / 2.0, (sy0 + sy1) / 2.0, lines, size=6.3)
    for i in range(2):
        x = sx0 + i * (sw + sg)
        arrow(ax, (x + sw, (sy0 + sy1) / 2.0), (x + sw + sg, (sy0 + sy1) / 2.0), lw=0.9)

    # ---- 去相位消融位置（論文的核心實驗設計） ----
    xd = sx0 + 2 * sw + 1.5 * sg - 0.45   # 第 2 與第 3 個子階段的正中間
    ax.plot([xd, xd], [sy0 - 1.0, sy1 + 2.6], color=ORANGE, lw=1.3, ls=(0, (2.2, 1.6)))
    ax.text(xd + 1.0, sy1 + 1.9, "dephasing channel (ablation)",
            ha="left", va="center", fontsize=6.0, color=ORANGE)
    ax.text(xd + 1.0, sy1 + 0.7, "only visible here, before $R_Y$",
            ha="left", va="center", fontsize=6.0, color=ORANGE)

    # 第一列第 4 格 → 展開框的引線
    xlead = xs[3] + w / 2.0
    arrow(ax, (xlead, y0), (xlead, dy1), color="#9a9a9a", lw=0.9, ls=(0, (2.5, 2.0)))


    # ---- 左下角：交叉驗證協定（論文最強的主張，但不屬於管線本身） ----
    ax.text(2.4, 14.6, "Cross-validation protocol",
            ha="left", va="center", fontsize=7.0, fontweight="bold")
    ax.plot([2.4, 2.4], [4.6, 13.6], color="#c8c8c8", lw=1.6, solid_capstyle="butt")
    notes = [
        "Every circuit is evaluated twice:",
        "   - CUDA-Q (formal track; the reported numbers)",
        "   - an independent NumPy state-vector simulator",
        "Agreement criterion:  max |\u0394P| < 1e-10.",
        "Both tracks share one golden-vector test set,",
        "so a silent divergence cannot pass unnoticed.",
    ]
    for i, t in enumerate(notes):
        ax.text(4.6, 12.6 - i * 1.62, t, ha="left", va="center",
                fontsize=6.3, color="#333333")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    FIGS.mkdir(parents=True, exist_ok=True)
    png, pdf, svg = FIGS / "arch.png", FIGS / "arch.pdf", FIGS / "arch.svg"
    fig.savefig(svg)
    fig.savefig(pdf)
    fig.savefig(png)
    print("wrote", svg.name, svg.stat().st_size, "|", pdf.name, pdf.stat().st_size, "|", png.name, png.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
