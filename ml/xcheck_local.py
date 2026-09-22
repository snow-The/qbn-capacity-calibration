"""大電路三方對帳（本地端）：固定參數下，q01 NumPy 版與 torch 版算出的完整機率向量。"""
import json, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import s09_capacity_scan as s09
import s12_torch_capacity as s12
import torch
N, DEPTH, SEED = 10, 8, 20260920
rng = np.random.default_rng(SEED)
Xa = rng.random((1, N))                      # 逐樣本角度編碼（batch=1）
w = rng.normal(0.0, 0.3, size=(DEPTH, N, 2)) # 可訓練參數
out = pathlib.Path(__file__).resolve().parent / "out"
out.mkdir(exist_ok=True)
(out / "xcheck_params.json").write_text(json.dumps({"N": N, "DEPTH": DEPTH, "Xa": Xa.tolist(), "w": w.tolist()}), encoding="utf-8")
# q01 NumPy 版：完整 2^n 機率（不用 class_probs，直接看狀態）
sim = s09.BatchedSim(N, 1)
for i in range(N): sim.apply_gate_1q("ry", Xa[:, i], i)
for d in range(DEPTH):
    for i in range(N):
        sim.apply_gate_1q("ry", w[d, i, 0], i); sim.apply_gate_1q("rz", w[d, i, 1], i)
    for c, t in s09.ring(N, 1 if d % 2 == 0 else 2): sim.apply_cx(c, t)
p_np = np.abs(sim.psi[0]) ** 2
# torch 版
torch.set_default_dtype(torch.float64)
wt = torch.tensor(w, requires_grad=False)
tsim = s12.TorchSim(N, 1)
X = torch.tensor(Xa, dtype=torch.float64)
for i in range(N): tsim.ry(X[:, i], i)
for d in range(DEPTH):
    for i in range(N):
        tsim.ry(wt[d, i, 0].reshape(1), i); tsim.rz(wt[d, i, 1].reshape(1), i)
    for c, t in s09.ring(N, 1 if d % 2 == 0 else 2): tsim.cx(c, t)
p_t = (tsim.psi.abs() ** 2)[0].numpy()
print("閘數 =", N + DEPTH * (2 * N + N))
print("max|P_q01 - P_torch| = %.3e" % np.max(np.abs(p_np - p_t)))
print("sum = %.12f / %.12f" % (p_np.sum(), p_t.sum()))
(out / "xcheck_local.json").write_text(json.dumps({"N": N, "DEPTH": DEPTH, "p_q01": p_np.tolist(), "p_torch": p_t.tolist(), "max_abs_diff": float(np.max(np.abs(p_np - p_t)))}), encoding="utf-8")
print("已寫出 xcheck_params.json / xcheck_local.json")