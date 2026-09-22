"""容量網格的真機匯出：把 s16 的每一格重訓、驗證、匯出成 QASM。

與 export_hw_circuits.py 的差別：那支是單一設定，這支跑一張清單（grid）。

每一步都有 fail-closed 驗證：
  1. 重訓後必須與 s16_capacity_final_5seed.json 記錄的指標一致（差 <= 0.005），
     否則中止 —— 沒有這個檢查，我們不確定送上去的是不是論文那一格。
  2. 匯出的 QASM 之後還要與 s12 的精確機率對帳（見 verify_hw_qasm.py）。

用法（在 q01-gpu venv，需要 torch）：
    python grid_export.py --configs "5,2,0;5,4,0;5,8,0;3,2,0;8,2,0" --samples 16
    （n,depth,seed 以分號分隔）
輸出：runs/grid/<tag>/sample*.qasm ＋ runs/grid/<tag>.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parent
ML = HERE.parent / "ml"
sys.path.insert(0, str(ML))
sys.path.insert(0, str(HERE))

import s09_capacity_scan as s09  # noqa: E402
import s12_torch_capacity as s12  # noqa: E402
from export_hw_circuits import qasm_for  # noqa: E402

STEPS, LR = 1200, 0.05
GOLD_ROWS = ML / "out" / "s16_capacity_final_5seed.json"
OUTROOT = HERE / "runs" / "grid"


def train_one(n, depth, seed):
    """與 s16 完全相同的訓練路徑。"""
    Z_tr, y_tr, Z_te, y_te = s09.make_data()
    rng = np.random.default_rng(seed)
    w = torch.tensor(rng.normal(0, 0.3, size=(depth, n, 2)), requires_grad=True)
    Xa, Xb = s09.encode(Z_tr[:, :n]), s09.encode(Z_te[:, :n])
    opt = torch.optim.Adam([w], lr=LR)
    for _ in range(STEPS):
        loss = s12.ce_loss(n, depth, Xa, y_tr, w)
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        Pa = s12.probs_torch(n, depth, Xa, w).numpy()
        Pb = s12.probs_torch(n, depth, Xb, w).numpy()
    return w.detach().numpy(), Xb, y_te, Pa, Pb


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True, help="n,depth,seed 以分號分隔")
    ap.add_argument("--samples", type=int, default=16)
    a = ap.parse_args()

    torch.set_default_dtype(torch.float64)
    rows = json.loads(GOLD_ROWS.read_text(encoding="utf-8"))["rows"]
    cfgs = [tuple(int(v) for v in c.split(",")) for c in a.configs.split(";") if c.strip()]
    print("要匯出 %d 個設定" % len(cfgs))

    for n, depth, seed in cfgs:
        tag = "n%d_d%d_s%d" % (n, depth, seed)
        print("=== %s ===" % tag, flush=True)
        w, Xb, y_te, Pa, Pb = train_one(n, depth, seed)
        ref = [r for r in rows if r["n_qubit"] == n and r["depth"] == depth and r["seed"] == seed]
        if not ref:
            print("  ★ s16 沒有這一格，跳過"); continue
        ref = ref[0]
        test_acc = float((Pb.argmax(1) == y_te).mean())
        d = abs(test_acc - ref["test_acc"])
        print("  重訓 test_acc %.4f  vs 論文 %.4f  |  差 %.4f" % (test_acc, ref["test_acc"], d))
        if d > 0.005:
            print("  ★ 重訓沒有重現這一格，跳過（不將就）"); continue

        per = max(1, a.samples // s09.N_CLASS)
        pick = []
        for c in range(s09.N_CLASS):
            pick.extend(np.where(y_te == c)[0][:per].tolist())
        pick = pick[:a.samples]
        outdir = OUTROOT / tag
        outdir.mkdir(parents=True, exist_ok=True)
        rec = {"n": n, "depth": depth, "seed": seed, "tag": tag,
               "test_acc_full": test_acc, "s16_record": ref,
               "n_trainable": depth * n * 2, "samples": []}
        for k, i in enumerate(pick):
            (outdir / ("sample%02d.qasm" % k)).write_text(
                qasm_for(n, depth, Xb[i], w), encoding="utf-8")
            rec["samples"].append({"k": k, "test_index": int(i), "y": int(y_te[i]),
                                   "expected_class_probs": [float(v) for v in Pb[i]],
                                   "pred": int(Pb[i].argmax())})
        (OUTROOT / (tag + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
        print("  匯出 %d 份 -> runs/grid/%s" % (len(pick), tag), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
