"""獨立驗證：bekko 的 ABTT 崩壞是真現象還是求解器假象？

三個獨立角度：
1. 前幾個主成分各自帶什麼資訊（情感 vs 語言）
2. ABTT 在有／無逐維標準化下的差別
3. 用 sklearn LogisticRegression(C=1.0) 這個**獨立實作**交叉核對我的 Newton 解
   （sklearn 只作為外部核對，不進入主流程；主流程維持純 NumPy）
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/mnt/c/Users/qq134/source/repos/QBN")
ML = ROOT / "projects/qbn-capacity-calibration/ml"
sys.path.insert(0, str(ML))
sys.path.insert(0, str(ROOT / "dev"))
import s08_pca_dim_ablation as s08  # noqa: E402
from data_bilingual_sentiment import load_dataset  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

texts, labels, langs = load_dataset()
y = np.asarray(labels)
lang = np.asarray(langs)
y_lang = (lang == "en").astype(int)

for key in s08.MODEL_ORDER:
    f = s08.CACHE_DIR / f"emb_{key.replace('/', '_')}.npz"
    X = np.load(f, allow_pickle=True)["X"]
    Xn = s08.l2norm(X)
    folds = s08.stratified_folds(y, 5, 7)
    te = folds[0]
    tr = np.concatenate([folds[j] for j in range(5) if j != 0])
    mu, Vt, s = s08.fit_pca(Xn[tr])
    rank = s08.pca_rank(s)
    Ztr = (Xn[tr] - mu) @ Vt.T
    Zte = (Xn[te] - mu) @ Vt.T
    print("=" * 78)
    print(f"{key}  (d={X.shape[1]}, rank={rank}, "
          f"PC1 evr={s[0] ** 2 / (s ** 2).sum():.4f}, PC2 evr={s[1] ** 2 / (s ** 2).sum():.4f})")

    print("  單一/前幾個 PC 的情感預測力與語言預測力（同一摺，seed=7 fold=1）：")
    for label, cols in (("PC1", [0]), ("PC2", [1]), ("PC1+PC2", [0, 1]),
                        ("PC3+PC4", [2, 3]), ("PC3..PC10", list(range(2, 10))),
                        ("PC3..PC66", list(range(2, 66)))):
        a_sent = s08.probe_scores(Ztr[:, cols], y[tr], Zte[:, cols], y[te])["acc"]
        a_lang = s08.probe_scores(Ztr[:, cols], y_lang[tr], Zte[:, cols], y_lang[te])["acc"]
        print(f"    {label:12s} 情感 acc={a_sent:.4f}   語言 acc={a_lang:.4f}")

    print("  ABTT 變體（k=64）：")
    A1, B1, _ = s08.arm_features(Ztr, Zte, X[tr], X[te], "abtt_k", 64, rank)
    print(f"    abtt_k（丟 2 + 標準化）      acc="
          f"{s08.probe_scores(A1, y[tr], B1, y[te])['acc']:.4f}")
    A2, B2 = s08.standardize(Ztr[:, 2:66], Zte[:, 2:66])
    print(f"    abtt（丟 2 + 標準化，重算）  acc="
          f"{s08.probe_scores(A2, y[tr], B2, y[te])['acc']:.4f}")
    A3, B3 = Ztr[:, 2:66], Zte[:, 2:66]
    print(f"    abtt（丟 2，不標準化）       acc="
          f"{s08.probe_scores(A3, y[tr], B3, y[te])['acc']:.4f}")
    A4, B4 = Ztr[:, 2:], Zte[:, 2:]
    print(f"    丟 2 且保留全部 {A4.shape[1]} 維     acc="
          f"{s08.probe_scores(A4, y[tr], B4, y[te])['acc']:.4f}")

    print("  sklearn LogisticRegression(C=1.0) 交叉核對（同一摺）：")
    for label, (Atr_, Ate_) in {
        "pca_first_k@64": (Ztr[:, :64], Zte[:, :64]),
        "abtt_k@64": (A1, B1),
        "PC1+PC2 only": (Ztr[:, :2], Zte[:, :2]),
    }.items():
        clf = LogisticRegression(C=1.0, max_iter=5000).fit(Atr_, y[tr])
        sk = float((clf.predict(Ate_) == y[te]).mean())
        mine = s08.probe_scores(Atr_, y[tr], Ate_, y[te])["acc"]
        print(f"    {label:16s} sklearn={sk:.4f}  Newton={mine:.4f}  "
              f"{'✅ 一致' if abs(sk - mine) < 1e-9 else '⚠ 不同'}")
print("VERIFY DONE")
