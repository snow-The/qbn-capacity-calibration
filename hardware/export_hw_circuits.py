"""把訓練好的容量模型匯出成真機可送的電路（Tuna-17 實驗 A/B 的前置）。

為什麼要這支：真機不能反傳，所以真機實驗必然是「模擬端訓練 -> 匯出角度 -> 真機只做前向」。
而 s16 目前沒有儲存角度，所以這裡用**完全相同的程式路徑**重訓（同 seed、同步數、同 lr），
並且**拿論文記錄的指標來驗證重訓確實重現了同一個模型** —— 對不上就中止，不將就。

電路定義（來自 s12_torch_capacity.probs_torch，big-endian：軸 k = qubit k）：
    for i in range(n): RY(encode(x_i)) on qubit i
    for d in range(depth):
        for i in range(n): RY(w[d,i,0]) on i ; RZ(w[d,i,1]) on i
        for (c,t) in ring(n, step = 1 if d even else 2): CX(c, t)
    讀出 = 前 3 個 qubit 的基底模式 -> 8 類（與 n 無關）

用法（在 q01-gpu venv，因為需要 torch）：
    python export_hw_circuits.py --n 5 --depth 8 --seed 0 --samples 16
輸出：runs/hw_n{n}_d{depth}_s{seed}.json   （角度、X、y、期望機率）
      runs/hw_n{n}_d{depth}_s{seed}/sample*.qasm
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parent
ML = HERE.parents[0] / "ml"
sys.path.insert(0, str(ML))

import s09_capacity_scan as s09  # noqa: E402
import s12_torch_capacity as s12  # noqa: E402

STEPS, LR = 1200, 0.05
GOLD_ROWS = ML / "out" / "s16_capacity_final_5seed.json"


def qasm_for(n: int, depth: int, x: np.ndarray, w: np.ndarray) -> str:
    """手寫 OpenQASM 2.0。n <= 10，閘只用 ry/rz/cx。

    qubit 編號沿用我們的習慣（qubit 0 是最上位），送出前由平台的轉譯器對映到實體 qubit。
    """
    q = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[%d];" % n, "creg c[%d];" % n]
    for i in range(n):
        # x 已經編碼過了（Xb = s09.encode(Z_te)），不能再編一次。
        # 這裡一開始寫成 s09.encode(x[i]) —— 二次編碼會把值全推到 pi，
        # 症狀是「16 個樣本全部預測同一類」，由 QASM vs 模擬器的比對抓到。
        q.append("ry(%.17g) q[%d];" % (x[i], i))
    for d in range(depth):
        for i in range(n):
            q.append("ry(%.17g) q[%d];" % (w[d, i, 0], i))
            q.append("rz(%.17g) q[%d];" % (w[d, i, 1], i))
        for c, t in s12.ring(n, 1 if d % 2 == 0 else 2):
            q.append("cx q[%d],q[%d];" % (c, t))
    q.append("measure q -> c;")
    return chr(10).join(q) + chr(10)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--depth", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--samples", type=int, default=16)
    a = ap.parse_args()

    torch.set_default_dtype(torch.float64)
    Z_tr, y_tr, Z_te, y_te = s09.make_data()

    # --- 重訓（與 s16 完全相同的路徑）---
    rng = np.random.default_rng(a.seed)
    w = torch.tensor(rng.normal(0, 0.3, size=(a.depth, a.n, 2)), requires_grad=True)
    Xa, Xb = s09.encode(Z_tr[:, :a.n]), s09.encode(Z_te[:, :a.n])
    opt = torch.optim.Adam([w], lr=LR)
    for _ in range(STEPS):
        loss = s12.ce_loss(a.n, a.depth, Xa, y_tr, w)
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        Pa = s12.probs_torch(a.n, a.depth, Xa, w).numpy()
        Pb = s12.probs_torch(a.n, a.depth, Xb, w).numpy()
    train_acc = float((Pa.argmax(1) == y_tr).mean())
    test_acc = float((Pb.argmax(1) == y_te).mean())
    print("重訓 n=%d depth=%d seed=%d -> train_acc %.4f  test_acc %.4f"
          % (a.n, a.depth, a.seed, train_acc, test_acc))

    # --- 驗證：必須與論文記錄的數字一致 ---
    rows = json.loads(GOLD_ROWS.read_text(encoding="utf-8"))["rows"]
    hit = [r for r in rows if r["n_qubit"] == a.n and r["depth"] == a.depth and r["seed"] == a.seed]
    if not hit:
        raise SystemExit("s16 的紀錄裡沒有 n=%d depth=%d seed=%d 這一格" % (a.n, a.depth, a.seed))
    ref = hit[0]
    d_tr = abs(train_acc - ref["train_acc"])
    d_te = abs(test_acc - ref["test_acc"])
    print("  論文紀錄 train %.4f test %.4f  |  差 %.4f / %.4f"
          % (ref["train_acc"], ref["test_acc"], d_tr, d_te))
    if d_tr > 0.005 or d_te > 0.005:
        raise SystemExit("★ 重訓沒有重現論文紀錄的那一格，中止（不將就）")
    print("  ==> 重現成功，這組角度就是論文那一格")

    # --- 分層抽樣：每個類別盡量平均 ---
    per = max(1, a.samples // s09.N_CLASS)
    pick = []
    for c in range(s09.N_CLASS):
        idx = np.where(y_te == c)[0]
        pick.extend(idx[:per].tolist())
    pick = pick[:a.samples]
    print("  抽樣 %d 個測試樣本，涵蓋 %d 個類別" % (len(pick), len(set(y_te[pick].tolist()))))

    outdir = HERE / "runs" / ("hw_n%d_d%d_s%d" % (a.n, a.depth, a.seed))
    outdir.mkdir(parents=True, exist_ok=True)
    wl = w.detach().numpy().tolist()
    rec = {"n": a.n, "depth": a.depth, "seed": a.seed, "steps": STEPS, "lr": LR,
           "train_acc": train_acc, "test_acc": test_acc,
           "s16_record": ref, "thetas_shape": [a.depth, a.n, 2], "thetas": wl,
           "samples": []}
    for k, i in enumerate(pick):
        x = Xb[i]
        qtext = qasm_for(a.n, a.depth, x, w.detach().numpy())
        (outdir / ("sample%02d.qasm" % k)).write_text(qtext, encoding="utf-8")
        rec["samples"].append({"k": k, "test_index": int(i), "y": int(y_te[i]),
                               "x": [float(v) for v in x],
                               "expected_class_probs": [float(v) for v in Pb[i]],
                               "pred": int(Pb[i].argmax())})
    (HERE / "runs" / ("hw_n%d_d%d_s%d.json" % (a.n, a.depth, a.seed))).write_text(
        json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  匯出 %d 份 QASM -> %s" % (len(pick), outdir))
    sim_acc = float(np.mean([Pb[i].argmax() == y_te[i] for i in pick]))
    print("  這 %d 個樣本在模擬端的準確率 = %.4f（真機要跟這個比）" % (len(pick), sim_acc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
