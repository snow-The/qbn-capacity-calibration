"""真機結果的第一件事：確認位元序，再談雜訊。

為什麼：max|dP| 偏大可能是「真機有雜訊」，也可能是「位元序寫反」。
Quafu 那邊就是後者（反轉前 5.6e-2、反轉後 4.4e-16）。不先分辨，結論會反。
"""
import glob
import json
import pathlib
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(r"C:\Users\snow\qi")
GOLD = json.loads((HERE / "cudaq_golden.json").read_text(encoding="utf-8"))
g = np.asarray(GOLD["cases"]["qbn5_book"]["probabilities"], dtype=float)
n = 5


def vec(counts, reverse: bool):
    total = sum(counts.values())
    p = np.zeros(2 ** n)
    for bits, c in counts.items():
        b = bits.replace(" ", "")
        if reverse:
            b = b[::-1]
        p[int(b, 2)] += c / total
    return p


for path in sorted(glob.glob(str(HERE / "qi_qbn5_book_Tuna-17_*.json"))):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    counts = d["counts"]
    shots = sum(counts.values())
    p_rev = vec(counts, True)
    p_raw = vec(counts, False)
    print("檔案:", pathlib.Path(path).name)
    print("  shots=%d  鍵數=%d" % (shots, len(counts)))
    print("  反轉一次（我們的索引） max|dP| = %.4e" % np.max(np.abs(p_rev - g)))
    print("  不反轉                max|dP| = %.4e" % np.max(np.abs(p_raw - g)))
    print("  => 位元序:", "反轉正確" if np.max(np.abs(p_rev - g)) < np.max(np.abs(p_raw - g)) else "★ 反轉反而更差，要查")
    top_t = sorted(range(len(p_rev)), key=lambda i: -p_rev[i])[:6]
    top_g = sorted(range(len(g)), key=lambda i: -g[i])[:6]
    print("  Tuna-17 top6 idx:", top_t, [round(float(p_rev[i]), 4) for i in top_t])
    print("  黃金   top6 idx:", top_g, [round(float(g[i]), 4) for i in top_g])
    # 逐態 z 分數：觀測 vs 期望（二項，忽略真機系統誤差）
    exp = g * shots
    obs = p_rev * shots
    sd = np.sqrt(np.maximum(exp * (1 - g), 1e-9))
    z = (obs - exp) / sd
    print("  max|z| = %.2f  |  |z|>3 的態數 = %d / %d" % (np.max(np.abs(z)), int(np.sum(np.abs(z) > 3)), len(g)))
    print("  chi2 = %.1f / df=%d" % (float(np.sum(z ** 2)), len(g) - 1))
