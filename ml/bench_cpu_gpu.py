"""實測：我們的張量形狀下 CPU vs GPU（同一顆 n=10/depth=8 電路、batch 80）。"""
import sys, time, pathlib
import numpy as np, torch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import s09_capacity_scan as s09
import s12_torch_capacity as s12

N, DEPTH, BATCH, STEPS = 10, 8, 80, 60
rng = np.random.default_rng(7)
Xa = rng.random((BATCH, N)); w = rng.normal(0, 0.3, size=(DEPTH, N, 2))

def run(dev):
    torch.set_default_dtype(torch.float64)
    wt = torch.tensor(w, dtype=torch.complex128 if False else torch.float64, device=dev, requires_grad=True)
    X = torch.as_tensor(Xa, dtype=torch.float64, device=dev)
    sim = s12.TorchSim(N, BATCH, dev)
    t0 = time.perf_counter()
    for _ in range(STEPS):
        sim = s12.TorchSim(N, BATCH, dev)
        for i in range(N): sim.ry(X[:, i], i)
        for dd in range(DEPTH):
            for i in range(N):
                sim.ry(wt[dd, i, 0].reshape(1), i); sim.rz(wt[dd, i, 1].reshape(1), i)
            for c, t in s09.ring(N, 1 if dd % 2 == 0 else 2): sim.cx(c, t)
        p = sim.class_probs()
        loss = -torch.log(torch.clamp(p[:, 0], min=1e-12)).mean()
        loss.backward(); wt.grad = None
    return (time.perf_counter() - t0) / STEPS

print("torch", torch.__version__, "| cuda avail:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
for dev in (["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"]):
    try:
        dt = run(dev)
        print("%-5s : %.4f s/step  (forward+backward, batch=%d)" % (dev, dt, BATCH), flush=True)
    except Exception as e:
        print("%-5s : FAIL %s %s" % (dev, type(e).__name__, str(e)[:90]), flush=True)
