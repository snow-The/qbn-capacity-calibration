"""C1 第二步：慣例對**準確率**的影響有多大。

第一步證明的是「換框架不變（1e-16）、換慣例差很多（1.15）」—— 但那是在固定角度下
看 ⟨Z⟩ 的差。真正要報的數字是：**同一份訓練預算，不同慣例各自收斂到多少準確率？**

設計原則：古典的部分**完全固定**，只換量子層的慣例。這樣準確率的差異
只可能來自慣例，不會混進前端或讀出層的差異。

  x(10) → 線性(10→4) → tanh → scale(kind) → 4 個角
        → 量子層（4 qubit, depth 2, euler order）→ 4 個 ⟨Z⟩
        → 線性(4→C) → softmax

任務：合成資料（與 s09 同風格），10 維輸入、4 類，類別訊號只在前 3 維。
用合成資料的理由：這一步要量的是「慣例的影響」，不是 MNIST 的絕對水準；
合成資料可以完全控制訊號結構並且跑得快。

跑在 /root/pl/.venv（PennyLane 0.45.1，原論文用的框架）。
"""
import json
import os
import pathlib
import sys

import numpy as np
import pennylane as qml
import pennylane.numpy as pnp

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

N_QUBIT, DEPTH, N_CLASS, DIM = 4, 2, 4, 10
RING = [(i, (i + 1) % N_QUBIT) for i in range(N_QUBIT)]
EULER_ORDERS = {
    "RZ-RY-RX": ("rz", "ry", "rx"),
    "RX-RY-RZ": ("rx", "ry", "rz"),
    "RY-RZ-RX": ("ry", "rz", "rx"),
    "RY-RX-RZ": ("ry", "rx", "rz"),
}
SCALINGS = ("pi_tanh", "pi_minmax", "two_arctan")
GATE = {"ry": qml.RY, "rz": qml.RZ, "rx": qml.RX}

# 規模刻意壓小：每個慣例要跑 N_TRAIN x EPOCHS 次 QNode，
# 原本 120x60 = 7200 次要好幾分鐘，12 個慣例就是一小時以上。
# 這裡要量的是「慣例之間的相對差異」，不是絕對水準，所以縮小不影響結論。
# test 放大到 512：訓練成本是 N_TRAIN x EPOCHS 次 QNode（不變），
# 而 512 個樣本讓單點標準誤從 0.088 降到 sqrt(0.25/512) = 0.022 —— 排名才可靠。
# 多種子確認：資料種子可由環境變數覆寫（見 協定-C1.md 9.4）。
SEED = int(os.environ.get("C1_SEED", "20260921"))
N_TRAIN, N_TEST, EPOCHS, LR = 32, 512, 20, 0.25
dev = qml.device("default.qubit", wires=N_QUBIT)


def scale(kind, v):
    if kind == "pi_tanh":
        return np.pi * v                       # v 已經過 tanh
    if kind == "pi_minmax":
        lo, hi = v.min(), v.max()
        return np.pi * (2 * (v - lo) / (hi - lo) - 1) if hi > lo else v * 0.0
    if kind == "two_arctan":
        return 2.0 * pnp.arctan(2.0 * v)       # 先放大再 arctan，避免擠在 0 附近
    raise ValueError(kind)


@qml.qnode(dev, interface="autograd", diff_method="backprop")
def qlayer(angles, theta, order):
    for i in range(N_QUBIT):
        qml.RY(angles[i], wires=i)
    for d in range(DEPTH):
        for i in range(N_QUBIT):
            for k, g in enumerate(order):
                GATE[g](theta[d, i, k], wires=i)
        for c, t in RING:
            qml.CNOT(wires=[c, t])
    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBIT)]


def make_data():
    rng = np.random.default_rng(SEED)
    def gen(n):
        y = rng.integers(0, N_CLASS, size=n)
        Z = rng.normal(0, 1.0, size=(n, DIM))
        # 類別訊號只放進前 3 維（其餘是雜訊）
        for c in range(N_CLASS):
            Z[y == c, :3] += np.array([np.cos(2 * np.pi * c / N_CLASS),
                                       np.sin(2 * np.pi * c / N_CLASS), 1.0]) * 1.2
        return Z, y
    return gen(N_TRAIN), gen(N_TEST)


def run(euler, scaling, data):
    (Xtr, ytr), (Xte, yte) = data
    rng = np.random.default_rng(SEED)
    W1 = pnp.array(rng.normal(0, 0.3, size=(N_QUBIT, DIM)), requires_grad=True)
    b1 = pnp.array(np.zeros(N_QUBIT), requires_grad=True)
    th = pnp.array(rng.normal(0, 0.3, size=(DEPTH, N_QUBIT, 3)), requires_grad=True)
    W2 = pnp.array(rng.normal(0, 0.3, size=(N_CLASS, N_QUBIT)), requires_grad=True)
    b2 = pnp.array(np.zeros(N_CLASS), requires_grad=True)
    params = [W1, b1, th, W2, b2]
    order = EULER_ORDERS[euler]

    # ★ 參數一律用「傳進去」而不是靠閉包。
    # 第一版讓 forward() 閉包捕捉外層的 W1/b1/th/W2/b2，而 loss_fn 裡解包的
    # 同名變數只是區域變數 —— forward 用的還是初始參數，輸出與輸入 p 無關。
    # autograd 直接給了 UserWarning: Output seems independent of input，
    # 而且 12 組全部停在隨機水準（4 類 = 0.25）。
    def forward(X, W1, b1, th, W2, b2):
        h = pnp.tanh(X @ W1.T + b1)
        out = []
        for row in h:
            a = scale(scaling, row)
            out.append(qlayer(a, th, order))
        Z = pnp.stack(out)
        return Z @ W2.T + b2

    def loss_fn(p):
        logits = forward(pnp.asarray(Xtr), *p)
        m = logits - logits.max(axis=1, keepdims=True)
        logp = m - pnp.log(pnp.exp(m).sum(axis=1, keepdims=True))
        return -logp[pnp.arange(len(ytr)), ytr].mean()

    import autograd
    grad = autograd.grad(loss_fn)
    for _ in range(EPOCHS):
        g = grad(params)
        params = [p - LR * gi for p, gi in zip(params, g)]

    logits = forward(pnp.asarray(Xte), *params)
    acc = float((np.asarray(logits).argmax(1) == yte).mean())
    return acc, float(loss_fn(params))


# 12 個條件的 max-min 在「純雜訊」下的期望值約為 3.26 sigma（n=12 的極差常數）。
# 這是判定「範圍是否為真效應」的對照基準。
RANGE_K = 3.26

def noise_range(n_test):
    return RANGE_K * float(np.sqrt(0.25 / n_test))

data = make_data()
print("合成任務：%d 維輸入、%d 類、train %d / test %d、%d epochs、seed=%d"
      % (DIM, N_CLASS, N_TRAIN, N_TEST, EPOCHS, SEED))
print()
rows = []
for euler in EULER_ORDERS:
    for scaling in SCALINGS:
        acc, loss = run(euler, scaling, data)
        rows.append({"euler": euler, "scaling": scaling, "test_acc": acc, "train_loss": loss})
        print("  %-10s %-12s  test_acc = %.4f   train_loss = %.4f" % (euler, scaling, acc, loss),
              flush=True)

accs = np.array([r["test_acc"] for r in rows])
print()
print("  ==== 12 種慣例的準確率：min %.4f / max %.4f / 範圍 %.4f ===="
      % (accs.min(), accs.max(), accs.max() - accs.min()))
(pathlib.Path(__file__).resolve().parent / "out").mkdir(exist_ok=True)
(pathlib.Path(__file__).resolve().parent / "out" / "synth_conventions.json").write_text(
    json.dumps({"rows": rows, "range": float(accs.max() - accs.min())}, indent=1), encoding="utf-8")
