"""s16 補跑（可續跑版）：只算缺的格子，而且**每算完一格就立刻落地**。

為什麼要有這一版（一次真實的教訓）：
  2026-09-20 的 n=10 補跑跑到 21/25，但原版 `s16_capacity_final_5seed.py`
  **只在全部跑完後才寫檔**；程序一結束，21 格的訓練成果全部消失，
  檔案裡 n=10 是 0 列。算力可以再買，訓練結果不能重來——所以改成逐格寫入。

用法：
  python s16_capacity_final_5seed_resume.py --dry   # 只報告還缺哪幾格
  python s16_capacity_final_5seed_resume.py         # 補跑（自動跳過已完成）

設計要點：
  * 資料決定性：`s09.make_data(seed=12345)`，所以跨程序、跨裝置的格子可比。
  * 裝置快取：原版 `_cx_perm` 只快取 CPU 張量，每次呼叫都 `.to(device)`；
    CUDA 上等於每個 CX 閘做一次 host→device 拷貝（1200 步 × depth·n 個閘）。
    這裡按裝置快取（只改快取鍵，數值完全不變，不動 s12 檔案）。
  * 上機前自檢：CPU 與 CUDA 各跑 5 步，損失不一致就自動退回 CPU。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s09_capacity_scan as s09  # noqa: E402
import s12_torch_capacity as s12  # noqa: E402

# 完整的 qubit 軸。原本的「正式版」s16_capacity_final.py 悄悄窄化成 (3,4,6,8,10)
# 而且沒有留下任何理由，但論文寫的是「掃描延伸到 qubit 數 3–10」——措辭比實際網格寬。
# 前面的 s10/s11/s12 用的都是 range(3, 11)，所以窄化只發生在最後一步，不是設計決定。
# n >= 3 是硬需求：8 類需要 3 個 qubit 的投影讀出。
NS = tuple(range(3, 11))
# 深度軸同理：原本的 (1,2,4,6,8) 跳過 3、5、7，但論文的圖就是以深度為橫軸，
# 而且貢獻摘要寫的是「深度 1–8」。稀疏的橫軸會讓曲線在 L=3/5/7 處斷掉，
# 也讓「1–8」這個寫法比實際網格寬。改成連續的 1..8。
DEPTHS = tuple(range(1, 9))
SEEDS = (0, 1, 2, 3, 4)
STEPS, LR = 1200, 0.05
OUT = HERE / "out" / "s16_capacity_final_5seed.json"
BASELINES = {"nearest_centroid_6pc": 0.8233, "logistic_6pc": 0.8033,
             "nearest_centroid_3pc": 0.7067, "nearest_centroid_12pc": 0.8467}


def _cx_perm_device(n: int, c: int, t: int, device):
    """按裝置快取的 CX 置換索引（數值與原版完全相同）。"""
    key = (n, c, t, str(device))
    if key not in s12._PERM:
        idx = np.arange(1 << n)
        cbit = (idx >> (n - 1 - c)) & 1
        perm = idx ^ ((1 << (n - 1 - t)) * cbit)
        s12._PERM[key] = torch.as_tensor(perm.astype(np.int64), device=device)
    return s12._PERM[key]


s12._cx_perm = _cx_perm_device


def ece(P, y, bins=10):
    conf, pred = P.max(axis=1), P.argmax(axis=1)
    hit = (pred == y).astype(float)
    edges, out = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            out += float(m.mean()) * abs(hit[m].mean() - conf[m].mean())
    return float(out)


def train_cell(n, depth, seed, device, data, steps=STEPS):
    Z_tr, y_tr, Z_te, y_te = data
    rng = np.random.default_rng(seed)
    w = torch.tensor(rng.normal(0.0, 0.3, size=(depth, n, 2)),
                     dtype=torch.float64, device=device, requires_grad=True)
    Xa, Xb = s09.encode(Z_tr[:, :n]), s09.encode(Z_te[:, :n])
    opt = torch.optim.Adam([w], lr=LR)
    t0 = time.perf_counter()
    loss = None
    for _ in range(steps):
        loss = s12.ce_loss(n, depth, Xa, y_tr, w, device)
        opt.zero_grad()
        loss.backward()
        opt.step()
    dt = time.perf_counter() - t0
    with torch.no_grad():
        Pa = s12.probs_torch(n, depth, Xa, w, device).cpu().numpy()
        Pb = s12.probs_torch(n, depth, Xb, w, device).cpu().numpy()
    return {"n_qubit": n, "depth": depth, "seed": seed, "n_trainable": depth * n * 2,
            "train_acc": round(float((Pa.argmax(1) == y_tr).mean()), 4),
            "test_acc": round(float((Pb.argmax(1) == y_te).mean()), 4),
            "test_ece": round(ece(Pb, y_te), 4),
            "train_loss": round(float(loss.detach()), 4),
            "seconds": round(dt, 1)}


def device_ok(data) -> bool:
    """CPU 與 CUDA 各跑 5 步，損失不一致就不用 CUDA。"""
    try:
        a = train_cell(3, 1, 0, "cpu", data, steps=5)["train_loss"]
        b = train_cell(3, 1, 0, "cuda", data, steps=5)["train_loss"]
    except Exception as exc:
        print(f"  CUDA 自檢拋錯（{type(exc).__name__}: {exc}）⇒ 退回 CPU", flush=True)
        return False
    d = abs(a - b)
    print(f"  CPU/CUDA 5 步損失：{a:.10f} vs {b:.10f}  |Δ|={d:.2e}", flush=True)
    if d > 1e-9:
        print("  ⇒ 不一致，退回 CPU", flush=True)
        return False
    print("  ⇒ 一致，使用 CUDA", flush=True)
    return True


def build_payload(rows, device, session_seconds, started_rows):
    cells = []
    for n in NS:
        for depth in DEPTHS:
            sub = sorted([r for r in rows if r["n_qubit"] == n and r["depth"] == depth],
                         key=lambda r: r["seed"])
            if not sub:
                continue
            ta = np.array([r["train_acc"] for r in sub], dtype=float)
            te = np.array([r["test_acc"] for r in sub], dtype=float)
            cells.append({
                "n_qubit": n, "depth": depth, "n_trainable": depth * n * 2,
                "n_seeds": len(sub),
                "train_acc_mean": round(float(ta.mean()), 4),
                "train_acc_std": round(float(ta.std(ddof=1)), 4) if len(sub) > 1 else None,
                "test_acc_mean": round(float(te.mean()), 4),
                "test_acc_std": round(float(te.std(ddof=1)), 4) if len(sub) > 1 else None,
                "test_ece_mean": round(float(np.mean([r["test_ece"] for r in sub])), 4),
            })
    total = len(NS) * len(DEPTHS) * len(SEEDS)
    return {
        "experiment": "s16_capacity_final",
        "partial": len(rows) < total,
        "n_rows": len(rows), "n_cells_total": total,
        "rows_at_start": started_rows, "device": device,
        "classes": s09.N_CLASS, "dim": s09.DIM, "n_pc": s09.N_PC,
        "n_train": s09.N_TRAIN, "n_test": s09.N_TEST,
        "steps": STEPS, "lr": LR, "optimizer": "Adam",
        "seeds": list(SEEDS), "chance": 1.0 / s09.N_CLASS, "data_seed": 12345,
        "gradient": "torch autograd through batched statevector simulator "
                    "(s12, verified 1.3e-15 vs parameter-shift)",
        "readout": "qubits 0,1,2 -> 8 classes (fixed; n>=3 required)",
        "baselines": BASELINES,
        "session_seconds": round(session_seconds, 1),
        "seconds_sum": round(float(sum(r["seconds"] for r in rows)), 1),
        "cells": cells,
        "rows": sorted(rows, key=lambda r: (r["n_qubit"], r["depth"], r["seed"])),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只報告缺哪幾格")
    ap.add_argument("--force-cpu", action="store_true")
    args = ap.parse_args()

    torch.set_default_dtype(torch.float64)
    rows = []
    if OUT.exists():
        rows = json.loads(OUT.read_text(encoding="utf-8")).get("rows", [])
    started_rows = len(rows)
    done = {(r["n_qubit"], r["depth"], r["seed"]) for r in rows}
    todo = [(n, d, s) for n in NS for d in DEPTHS for s in SEEDS if (n, d, s) not in done]
    print(f"既有 {len(rows)} 列；總格數 {len(NS)*len(DEPTHS)*len(SEEDS)}；待補 {len(todo)} 格", flush=True)
    if todo:
        from collections import Counter
        print("  待補分佈:", dict(sorted(Counter(n for n, _, _ in todo).items())), flush=True)
    if args.dry or not todo:
        return 0

    device = "cpu"
    if not args.force_cpu and torch.cuda.is_available():
        print(f"CUDA: {torch.cuda.get_device_name(0)}", flush=True)
        device = "cuda"
    print(f"device = {device}", flush=True)

    data = s09.make_data()
    if device == "cuda" and not device_ok(data):
        device = "cpu"
        print(f"改用 device = {device}", flush=True)

    t_all = time.perf_counter()
    for i, (n, depth, seed) in enumerate(todo, 1):
        row = train_cell(n, depth, seed, device, data)
        rows.append(row)
        OUT.write_text(json.dumps(build_payload(rows, device, time.perf_counter() - t_all,
                                                started_rows), indent=1, ensure_ascii=False),
                       encoding="utf-8")
        eta = (time.perf_counter() - t_all) / i * (len(todo) - i)
        print("[%2d/%2d] n=%2d depth=%d seed=%d  train=%.4f test=%.4f ece=%.4f  "
              "%6.1fs  ETA %5.1f min" % (i, len(todo), n, depth, seed, row["train_acc"],
                                         row["test_acc"], row["test_ece"], row["seconds"],
                                         eta / 60), flush=True)
    print("完成：%d 列，耗時 %.1f s" % (len(rows), time.perf_counter() - t_all), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
