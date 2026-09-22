"""去相位消融的真機匯出：把「插入去相位通道」換成「插入延遲」。

為什麼要換：去相位是**非么正**通道，真機不提供「去相位閘」，硬體只給你閘 ＋ 等待。
而 T1/T2 衰減本身就是物理上的去相位機制 —— 所以真機版就是把通道換成 delay。

⚠️ 與論文的**宣告差異**（必須寫進論文）：
  s17 沒有儲存訓練好的角度，所以這裡用 s16 的訓練配方（Adam 1200 步）重訓同一個電路
  （n=5, depth=2, 環形 CX，與 s17 同族），並與 s16 的紀錄對帳。
  因為真機版的唯一變因是「延遲插在哪裡」，角度本身不是變因，這個替代是可控的。

⚠️ dt 未宣告：Tuna-17 的 target 沒有 dt，所以「delay(1) 是幾微秒」未知。
  因此延遲長度用**整數刻度**並掃描，靠實測而非換算。

四臂的真機對應：
  A            無延遲（基線）
  B(tau)       編碼層後插入 delay(tau)  → 預期分布被壓平
  C(tau)       測量前插入 delay(tau)    → 預期預測指標不變（T5 定理）
  D            真機做不到獨立的退極化通道 → **不送**，在論文明說

★ 真機版多出一個可檢驗的張力：延遲期間除 T2 去相位外還有 T1 振幅衰減，
  而 T1 會改變對角元 ⇒ 臂 C 在真機上**不會**逐位元等於臂 A。
  那個偏差本身就是可量測的硬體特性（而且模擬端完全看不到）。

用法：python ablation_export.py --delays 0,1,4,16 --samples 8
輸出：runs/ablation/<tag>/sample*.qasm ＋ runs/ablation/<tag>.json
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

import s09_capacity_scan as s09  # noqa: E402
import s12_torch_capacity as s12  # noqa: E402

N, DEPTH, SEED, STEPS, LR = 5, 2, 0, 1200, 0.05
GOLD = ML / "out" / "s16_capacity_final_5seed.json"
OUTROOT = HERE / "runs" / "ablation"


def qasm_ablation(x, w, delay_after_encoding: int, delay_before_measure: int) -> str:
    """延遲以整數刻度給（dt 未宣告，故不換算成時間）。"""
    q = ["OPENQASM 2.0;", 'include "qelib1.inc";',
         "qreg q[%d];" % N, "creg c[%d];" % N]
    for i in range(N):
        q.append("ry(%.17g) q[%d];" % (x[i], i))
    if delay_after_encoding:
        q.append("barrier q;")
        q.append("delay(%d) q;" % delay_after_encoding)
    for d in range(DEPTH):
        for i in range(N):
            q.append("ry(%.17g) q[%d];" % (w[d, i, 0], i))
            q.append("rz(%.17g) q[%d];" % (w[d, i, 1], i))
        for c, t in s12.ring(N, 1 if d % 2 == 0 else 2):
            q.append("cx q[%d],q[%d];" % (c, t))
    if delay_before_measure:
        q.append("barrier q;")
        q.append("delay(%d) q;" % delay_before_measure)
    q.append("measure q -> c;")
    return chr(10).join(q) + chr(10)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delays", default="0,1,4,16")
    ap.add_argument("--samples", type=int, default=8)
    a = ap.parse_args()

    torch.set_default_dtype(torch.float64)
    Z_tr, y_tr, Z_te, y_te = s09.make_data()
    rng = np.random.default_rng(SEED)
    w = torch.tensor(rng.normal(0, 0.3, size=(DEPTH, N, 2)), requires_grad=True)
    Xa, Xb = s09.encode(Z_tr[:, :N]), s09.encode(Z_te[:, :N])
    opt = torch.optim.Adam([w], lr=LR)
    for _ in range(STEPS):
        loss = s12.ce_loss(N, DEPTH, Xa, y_tr, w)
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        Pb = s12.probs_torch(N, DEPTH, Xb, w).numpy()
    acc = float((Pb.argmax(1) == y_te).mean())
    ref = [r for r in json.loads(GOLD.read_text(encoding="utf-8"))["rows"]
           if r["n_qubit"] == N and r["depth"] == DEPTH and r["seed"] == SEED][0]
    print("重訓 n=%d depth=%d: test_acc %.4f vs 論文 %.4f | 差 %.4f"
          % (N, DEPTH, acc, ref["test_acc"], abs(acc - ref["test_acc"])), flush=True)
    if abs(acc - ref["test_acc"]) > 0.005:
        raise SystemExit("★ 重訓沒重現，中止")
    wl = w.detach().numpy()

    per = max(1, a.samples // s09.N_CLASS)
    pick = []
    for c in range(s09.N_CLASS):
        pick.extend(np.where(y_te == c)[0][:per].tolist())
    pick = pick[:a.samples]
    delays = [int(v) for v in a.delays.split(",")]

    arms = [("A", 0, 0)] + [("B%d" % t, t, 0) for t in delays[1:]] + \
           [("C%d" % t, 0, t) for t in delays[1:]]
    for name, d_enc, d_meas in arms:
        tag = "%s_n%d_d%d_s%d" % (name, N, DEPTH, SEED)
        outdir = OUTROOT / tag
        outdir.mkdir(parents=True, exist_ok=True)
        # ⚠️ delay 不是合法 OpenQASM 2.0（qelib1.inc 沒有它），Qiskit 的 parser
        # 會拋「cannot use non-builtin custom instruction delay before definition」，
        # 而宣告成 opaque 又會讓它不再是真正的 Delay。所以延遲臂要由送出器
        # 用 Qiskit 原生 API（qc.delay）建構 —— 這裡把參數一併寫出來。
        rec = {"arm": name, "delay_after_encoding": d_enc,
               "delay_before_measure": d_meas, "tag": tag,
               "n": N, "depth": DEPTH, "seed": SEED, "samples": []}
        for k, i in enumerate(pick):
            (outdir / ("sample%02d.qasm" % k)).write_text(
                qasm_ablation(Xb[i], wl, d_enc, d_meas), encoding="utf-8")
            rec["samples"].append({"k": k, "y": int(y_te[i]),
                                   "expected_class_probs": [float(v) for v in Pb[i]],
                                   "pred": int(Pb[i].argmax()),
                                   "x": [float(v) for v in Xb[i]],
                                   "w": wl.tolist()})
        (OUTROOT / (tag + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
        print("  臂 %-5s 延遲(編碼後=%d, 測量前=%d) -> %d 份 QASM"
              % (name, d_enc, d_meas, len(pick)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
