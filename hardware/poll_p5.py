"""查 ScQ-P5 真機任務的狀態與結果。

依 hardware/README.md：
  * Task.retrieve(taskid) 是「查詢」，不消耗額度（額度只在任務真的成立時才計）
  * P5 要排隊 700+，所以當初是用 send(wait=False) 非同步送單，先存 taskid 再等
  * 回傳的 ExecResult 帶 counts / probabilities / logicalq_res

token 只從檔案讀，永不回顯（只印長度與尾四碼）。
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from quafu import Task, User

REPO = pathlib.Path("/mnt/c/Users/qq134/source/repos/QBN")
HW = REPO / "projects/qbn-capacity-calibration/hardware"
TOKENS = [
    pathlib.Path("/mnt/c/Users/qq134/.dsh/quafu.token"),
    pathlib.Path.home() / ".dsh" / "quafu.token",
]

tokfile = next((p for p in TOKENS if p.exists()), None)
if tokfile is None:
    raise SystemExit("找不到 quafu.token")
tok = tokfile.read_text(encoding="utf-8").strip()
print("token: %d chars, ...%s" % (len(tok), tok[-4:]))

tid = (HW / "runs" / "scqp5_qbn5_book.taskid").read_text(encoding="utf-8").strip()
print("taskid:", tid)

u = User(api_token=tok)

try:
    bs = u.get_available_backends()
    for name in ("ScQ-P5", "ScQ-Sim10", "Baihua"):
        b = bs.get(name)
        if b is not None:
            print("backend %-10s qubits=%-4s status=%-9s queue=%s" % (
                name, b.qubit_num, b.status, getattr(b, "task_in_queue", "?")))
except Exception as exc:
    print("backend query failed:", type(exc).__name__, exc)

print()
t = Task(user=u)
try:
    res = t.retrieve(tid)
except Exception as exc:
    print("retrieve raised:", type(exc).__name__, exc)
    raise SystemExit(1)

print("ExecResult attrs:", [a for a in dir(res) if not a.startswith("_")])
for attr in ("taskid", "status", "task_status", "error", "message"):
    if hasattr(res, attr):
        try:
            print("  %s = %r" % (attr, getattr(res, attr)))
        except Exception as exc:
            print("  %s -> %s" % (attr, exc))
counts = getattr(res, "counts", None)
if counts:
    print("counts: %d keys, total shots %d" % (len(counts), sum(counts.values())))
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:10]
    print("top-10:", top)
    out = HW / "runs" / "scqp5_qbn5_book_counts.json"
    out.write_text(json.dumps({"taskid": tid, "counts": counts}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("written:", out)
else:
    print("counts 還是空的 —— 任務仍在佇列中")
