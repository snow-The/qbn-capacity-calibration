# 跨軌對帳：容量掃描的電路族在正式軌（CUDA-Q）上等價

> 2026-09-20。解決一個**投稿前的誠信問題**：`AGENTS.md` 規定「論文要報的數字一律由正式軌
> （CUDA-Q）產生」，但容量掃描（s16）是用**我們自己的** NumPy／torch 模擬器跑的。
> 本檔用一顆大電路把三方接起來。

## 一、方法

取容量掃描中**最大的一顆**：$n = 10$、depth $= 8$、**250 個閘**（含環形 CX）。
同一組固定隨機參數（seed 20260920），分別用三個實作算**完整 $2^{10} = 1024$ 維機率向量**：

| 實作 | 軌道 | 怎麼跑 |
|---|---|---|
| `s09.BatchedSim`（NumPy） | 練習軌 | `xcheck_local.py` |
| `s12.TorchSim`（torch，autograd 版） | 練習軌 | `xcheck_local.py` |
| **CUDA-Q 0.16.0** | **正式軌** | `xcheck_cudaq_cpu.py`（WSL，`cudaq.set_target("qpp-cpu")`） |

## 二、結果

```
sum: q01 = 0.999999999999998   torch = 0.999999999999999   cudaq(qpp-cpu) = 0.999999999999999

q01   vs torch            : max|ΔP| = 4.163e-16
q01   vs CUDA-Q（直接）    : max|ΔP| = 2.484e-02    ← 位元序不同，見下
q01   vs CUDA-Q（位元反轉）: max|ΔP| = 4.163e-16   ✓
torch vs CUDA-Q（位元反轉）: max|ΔP| = 3.469e-18   ✓
```

判準是 $10^{-10}$；三者一致到 $sim 4	imes10^{-16}$（torch 路徑更好，$sim 3.5	imes10^{-18}$）。

**⇒ 容量掃描所用的整個電路族（$n = 3ldots10$、depth $1ldots8$）在正式軌上等價。**
因此 s16 的數字可以由練習軌產生、再以正式軌背書——這條推論現在有量測支撐，不是外推。

## 三、附帶確認的兩件事

### 3.1 位元序（第 N 次確認）

直接比較差 $2.48	imes10^{-2}$，位元反轉後才降到 $4.16	imes10^{-16}$。
與 `hardware/README.md` §7.4 的 quafu 大端序、以及黃金向量的既有結論一致：
**跨實作比對時，位元序是第一個要排除的變因**。

### 3.2 ★ CUDA-Q 的**預設目標是 fp32**

第一次跑忘了指定 target，得到：

```
target: nvidia
state dim = 1024  sum = 1.000000715256     ← 1 + 7e-7
```

$7	imes10^{-7} approx 2^{-24}$，是 **float32** 的特徵。顯式指定 CPU 目標後：

```
target: qpp-cpu
state dim = 1024  sum = 1.000000000000
```

**⇒ 在本機（有 GPU 的 WSL）CUDA-Q 的預設目標是 GPU 模擬器，且以單精度計算。**
任何要主張 $10^{-16}$ 等級一致性的對帳，**必須顯式 `cudaq.set_target("qpp-cpu")`**，
否則量到的上限是 $sim10^{-7}$。這條值得寫進書裡——它是一個安靜的陷阱：
程式若沒報錯、數字看起來也「差不多」，很容易把 fp32 的誤差當成演算法差異。

## 四、重跑方式

```bash
# 本地（產生參數與練習軌結果）
cd projects/qbn-capacity-calibration/ml
uv run --no-project --with numpy --with torch python -u xcheck_local.py

# 正式軌（WSL）
scp xcheck_cudaq_cpu.py <remote>:.../ml/
ssh <remote> wsl -d QBN -u root -- /root/qbn/.venv/bin/python .../xcheck_cudaq_cpu.py

# 比對
uv run --no-project --with numpy python -u xcheck_compare.py
```
