"""用 opensquirrel 逐一驗證產生的 cQASM —— 送出去之前的最後一道關卡。"""
import json, pathlib, sys
from opensquirrel import Circuit

ROOT = pathlib.Path("/home/b02/qi")
man = json.loads((ROOT / "cqasm" / "manifest.json").read_text(encoding="utf-8"))
bad = []
for m in man:
    p = ROOT / m["path"]
    try:
        c = Circuit.from_string(p.read_text(encoding="utf-8"))
    except Exception as e:
        bad.append((m["tag"], m["k"], str(e).split(chr(10))[0][:100]))
print("驗證 %d 個檔案，失敗 %d 個" % (len(man), len(bad)))
for t, k, e in bad[:20]:
    print("  FAIL %s k=%d :: %s" % (t, k, e))

# 抽一個出來人工檢查
import collections
seen = set()
for m in man:
    if m["tag"] in seen:
        continue
    seen.add(m["tag"])
    p = ROOT / m["path"]
    print()
    print("=== %s k=%d (delay_after=%s before=%s depth=%s) ===" % (
        m["tag"], m["k"], m["delay_after_encoding"], m["delay_before_measure"], m["depth"]))
    print(p.read_text(encoding="utf-8")[:600])
    if len(seen) >= 3:
        break
