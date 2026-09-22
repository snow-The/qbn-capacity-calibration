"""真機 vs 理想模擬的統計分析（修正版）。

第一版的錯誤：我把二項變異數的下界設成 1e-9，於是「期望次數趨近 0」的態
會產生 z=1309 這種假訊號，chi2 也被灌到 240 萬。正確的下界應該取 1（Poisson 尺度）。
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


def vec(counts):
    total = sum(counts.values())
    p = np.zeros(2 ** n)
    for bits, c in counts.items():
        p[int(bits.replace(" ", "")[::-1], 2)] += c / total
    return p


for path in sorted(glob.glob(str(HERE / "qi_qbn5_book_*.json"))):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    counts = d["counts"]
    N = sum(counts.values())
    p = vec(counts)
    print("=== %s ===" % pathlib.Path(path).name)
    print("  後端 %s | shots %d | 鍵數 %d" % (d.get("backend"), N, len(counts)))

    tv = 0.5 * float(np.sum(np.abs(p - g)))
    fid = float(np.sum(np.sqrt(p * g)) ** 2)
    print("  max|dP| = %.4e   TV 距離 = %.4f   保真度(Bhattacharyya^2) = %.4f"
          % (np.max(np.abs(p - g)), tv, fid))

    exp = g * N
    obs = p * N
    var = np.maximum(N * g * (1 - g), 1.0)      # Poisson 尺度下界，不是 1e-9
    z = (obs - exp) / np.sqrt(var)
    print("  取樣雜訊基準(1/sqrt(N)) = %.2e" % (N ** -0.5))
    print("  max|z| = %.2f   |z|>3 的態數 = %d / %d   chi2 = %.1f / df=%d"
          % (np.max(np.abs(z)), int(np.sum(np.abs(z) > 3)), len(g),
             float(np.sum(z ** 2)), len(g) - 1))
    worst = int(np.argmax(np.abs(p - g)))
    print("  最大偏差在 idx=%d：觀測 %.4f vs 理想 %.4f（差 %+.4f）"
          % (worst, p[worst], g[worst], p[worst] - g[worst]))
    idx = np.argsort(-g)[:6]
    print("  主要態  理想 ->  觀測:")
    for i in idx:
        print("    idx %2d   %.4f -> %.4f   (%+.4f)" % (i, g[i], p[i], p[i] - g[i]))
    print()
