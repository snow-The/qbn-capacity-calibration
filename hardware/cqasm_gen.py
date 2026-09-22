"""從資料集 JSON 產生 cQASM 3.0 電路 —— 不經過 Qiskit、不經過 transpiler。

為什麼不用 Qiskit：
  - Qiskit 的 transpile 會插入 SWAP 並改寫電路，導致送出的電路與原稿不同，
    事後無法對回樣本（2026-09-21 實際踩到）。
  - OpenQASM 2.0 不支援延遲，消融的 B/C 臂無法表達。
cQASM 3.0 直接支援 `wait(N) q[i]`，且 QI 後端原生吃 cQASM。
"""
import json, pathlib, re

ROOT = pathlib.Path("/home/b02/qi")
DATA = ROOT / "data"
OUT = ROOT / "cqasm"

def fnum(v):
    """cQASM 的數值格式：避免科學記號造成解析問題。"""
    return ("%.9f" % float(v)).rstrip("0").rstrip(".") or "0"

def to_cqasm(enc, layers, meas, delay_after_enc=0, delay_before_meas=0, n=None):
    """enc: 每個 qubit 的編碼角；layers: [[(ry,rz) x n] x depth]。"""
    n = n or len(enc)
    L = ["version 3.0", "", "qubit[%d] q" % n, "bit[%d] b" % n, ""]
    for i, a in enumerate(enc):
        L.append("Ry(%s) q[%d]" % (fnum(a), i))
    if delay_after_enc:
        for i in range(n):
            L.append("wait(%d) q[%d]" % (int(delay_after_enc), i))
    for layer in layers:
        # 環形 CNOT（與原稿一致，不動它）
        for i in range(n):
            L.append("CNOT q[%d], q[%d]" % (i, (i + 1) % n))
        for i, (ry, rz) in enumerate(layer):
            L.append("Ry(%s) q[%d]" % (fnum(ry), i))
            L.append("Rz(%s) q[%d]" % (fnum(rz), i))
    if delay_before_meas:
        for i in range(n):
            L.append("wait(%d) q[%d]" % (int(delay_before_meas), i))
    for i in range(n):
        L.append("b[%d] = measure q[%d]" % (i, i))
    return chr(10).join(L) + chr(10)

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    manifest = []
    for p in sorted(DATA.rglob("*.json")):
        if "cudaq" in str(p):
            continue
        d = load(p)
        tag = d.get("tag") or p.stem
        kind = "ablation" if "ablation" in str(p) else ("grid" if "grid" in str(p) else "hw")
        dae = int(d.get("delay_after_encoding") or 0)
        dbm = int(d.get("delay_before_measure") or 0)
        n = int(d.get("n") or 5)
        smp = d.get("samples") or []
        if not smp:
            print("  [略過] %s：沒有樣本" % tag)
            continue
        # 三種情況：有 x+w（ablation）、只有 x（hw）、兩者皆無（grid，全靠 QASM）
        has_x = "x" in smp[0]
        has_w = "w" in smp[0]
        sub = OUT / (tag if kind == "hw" else kind + "/" + tag)
        sub.mkdir(parents=True, exist_ok=True)
        for sm in smp:
            k = sm["k"]
            enc = [float(v) for v in sm["x"]] if has_x else None
            if has_w:
                layers = [[[float(g) for g in pair] for pair in lay] for lay in sm["w"]]
            else:
                # hw/grid 沒有 w：改讀既有的 OpenQASM，取其中的 ry/rz
                qp = (DATA / tag / ("sample%02d.qasm" % k)) if kind == "hw" \
                     else (DATA / kind / tag / ("sample%02d.qasm" % k))
                if not qp.is_file():
                    print("  [略過] %s k=%d：沒有 w 也沒有 qasm" % (tag, k))
                    continue
                txt = qp.read_text(encoding="utf-8")
                rys = [float(v) for v in re.findall(r"ry\(([-0-9.eE+]+)\)", txt, re.I)]
                rzs = [float(v) for v in re.findall(r"rz\(([-0-9.eE+]+)\)", txt, re.I)]
                # 前 n 個 ry 是編碼，其餘是各層的可訓練 ry；rz 依序對應各層
                if enc is None:
                    enc = rys[:n]
                train_ry = rys[n:]
                depth = len(train_ry) // n if n else 0
                layers = []
                for li in range(depth):
                    lay = []
                    for qi in range(n):
                        lay.append([train_ry[li * n + qi], rzs[li * n + qi]])
                    layers.append(lay)
            text = to_cqasm(enc, layers, n, dae, dbm, n=n)
            (sub / ("k%02d.cq" % k)).write_text(text, encoding="utf-8")
            manifest.append(dict(kind=kind, tag=tag, k=k, delay_after_encoding=dae,
                                 delay_before_measure=dbm, n=n, depth=len(layers),
                                 path=str((sub / ("k%02d.cq" % k)).relative_to(ROOT))))
            made += 1
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("產生 %d 個 cQASM 檔於 %s" % (made, OUT))
    import collections
    c = collections.Counter(m["tag"] for m in manifest)
    for k, v in sorted(c.items()):
        print("  %-22s %d" % (k, v))

if __name__ == "__main__":
    main()
