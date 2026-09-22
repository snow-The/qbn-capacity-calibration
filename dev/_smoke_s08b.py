"""s08 的煙霧測試（重建版）：在合成資料上跑通純 NumPy 路徑與出圖（不載入真模型）。"""
import sys
from pathlib import Path

import numpy as np

ML = Path("/mnt/c/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration/ml")
sys.path.insert(0, str(ML))
import s08_pca_dim_ablation as s08  # noqa: E402

print("import OK; ARMS =", s08.ARMS)

rng = np.random.default_rng(0)
n = 160
lang = np.array(["zh"] * 80 + ["en"] * 80)
y = np.array([1] * 40 + [0] * 40 + [1] * 40 + [0] * 40)
X = rng.normal(0, 1, (n, 256))
X[:, 0] += np.where(lang == "en", 4.0, -4.0)
X[:, 1] += np.where(lang == "en", -3.0, 3.0)
X[:, 2] += np.where(y == 1, 2.0, -2.0)
X[:, 3] += np.where(y == 1, -1.5, 1.5)
X = s08.l2norm(X)
y_lang = (lang == "en").astype(int)

st = s08.self_test(X, y)
print("self_test ok:", all([st["train_side_invariance"]["ok"],
                            st["synthetic_separable_probe"]["ok"],
                            st["permuted_labels_abtt_k_k32"]["within_3sigma_or_0.05"]]))

res = s08.sweep_task("smoke_cv", X, y, s08.ARMS, [64, 8], split_mode="cv")
for arm in res["arms"]:
    d = res["results"][arm][64]["seed"]
    print(f"  {arm:14s} k=64 acc={d['acc_mean']:.4f}±{d['acc_std']:.4f}")
res_t = s08.sweep_task("smoke_tr", X, y, ["pca_first_k", "abtt_k"], [64, 8],
                       split_mode="transfer", lang=lang)
res_l = s08.sweep_task("smoke_lang", X, y_lang, ["pca_first_k", "abtt_k"], [64, 8],
                       split_mode="cv")
print("  transfer mean:", f"{res_t['results']['abtt_k'][64]['mean']['acc_mean']:.4f}")
print("  langid:", f"{res_l['results']['abtt_k'][64]['seed']['acc_mean']:.4f}")
diag = s08.pc_content_diagnostic(X, y, y_lang)
print("  pc_diag PC1+PC2:", diag["PC1+PC2"])

tasks = {"sentiment_cv": {"bekko-embedding-v1-a25m": res},
         "transfer": {"bekko-embedding-v1-a25m": res_t},
         "langid_cv": {"bekko-embedding-v1-a25m": res_l},
         "ref_full": {"bekko-embedding-v1-a25m": res}}
s08.make_figure(tasks, ["bekko-embedding-v1-a25m"],
                {64: {"trunc_k": 0.7, "pca_first_k": 0.6, "abtt_k": 0.8,
                      "k_eff_pca": 64, "winner": "abtt_k", "delta_trunc_minus_pca": 0.1}},
                {"bekko-embedding-v1-a25m": diag})
print("figure OK:", s08.FIG_PNG.exists(), s08.FIG_PDF.exists())
print("SMOKE DONE")
