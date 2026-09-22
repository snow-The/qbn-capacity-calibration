"""在 CUDA-Q 上執行 cases.json 的閘列表，回報 ⟨Z⟩。

跑在 /root/qbn/.venv（CUDA-Q 0.16.0，正式軌）。

為什麼要「產生一個 .py 模組」而不是動態 exec：
  CUDA-Q 的 @cudaq.kernel 會用 inspect 取原始碼來做編譯，
  所以 kernel 必須定義在**真實檔案**裡。實測直接 exec 會拋
  RuntimeError: @cudaq.kernel could not retrieve source for function ... (<string>)。
  因此這裡先把 60 個 kernel 寫成 _kernels.py，再 import 進來跑。
"""
import importlib
import json
import pathlib
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cudaq

HERE = pathlib.Path(__file__).resolve().parent
cases = json.loads((HERE / "out" / "cases.json").read_text(encoding="utf-8"))
N = cases["n_qubit"]

lines = ["import cudaq", "", "N = %d" % N, ""]
for i, c in enumerate(cases["cases"]):
    lines.append("@cudaq.kernel")
    lines.append("def k_%d():" % i)
    lines.append("    q = cudaq.qvector(%d)" % N)
    for name, qs, ang in c["gates"]:
        if name == "cx":
            lines.append("    x.ctrl(q[%d], q[%d])" % (qs[0], qs[1]))
        else:
            lines.append("    %s(%.17g, q[%d])" % (name, ang, qs[0]))
    lines.append("")
(HERE / "_kernels.py").write_text(chr(10).join(lines), encoding="utf-8")

cudaq.set_target("qpp-cpu")
sys.path.insert(0, str(HERE))
import _kernels  # noqa: E402
importlib.reload(_kernels)

idx = np.arange(1 << N)
out = []
for i, c in enumerate(cases["cases"]):
    st = np.array(cudaq.get_state(getattr(_kernels, "k_%d" % i)))
    p = np.abs(st) ** 2
    zs = []
    # ★ 位元序：cudaq.get_state() 是 little-endian（bit q ↔ qubit q），
    # 而 cudaq.sample() 是 big-endian —— 兩者不同，專案文件已記錄。
    # 這裡一開始跟著 NumPy 參考寫成 big-endian，結果 max|d<Z>| 高達 0.756，
    # 由與 PennyLane（4.4e-16）的三方比對抓到。
    for q in range(N):
        bit = (idx >> q) & 1
        zs.append(float(np.sum(p * (1 - 2 * bit))))
    out.append({"id": c["id"], "z_cudaq": zs})

(HERE / "out" / "cudaq.json").write_text(json.dumps({"cases": out}, indent=1), encoding="utf-8")
print("CUDA-Q 執行 %d 個案例 -> out/cudaq.json" % len(out))
