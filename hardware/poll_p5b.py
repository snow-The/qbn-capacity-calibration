"""第二支輪詢：挖原始回傳 + 把這次觀測追加進 p5_queue_samples.jsonl。

為什麼要記歷史：單看一次「queue=735」判斷不了佇列有沒有在前進，
要有時間序列才看得出趨勢。既有的 jsonl 就是在做這件事。
"""
import datetime
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from quafu import Task, User

REPO = pathlib.Path("/mnt/c/Users/qq134/source/repos/QBN")
HW = REPO / "projects/qbn-capacity-calibration/hardware"
tok = pathlib.Path("/mnt/c/Users/qq134/.dsh/quafu.token").read_text(encoding="utf-8").strip()
tid = (HW / "runs" / "scqp5_qbn5_book.taskid").read_text(encoding="utf-8").strip()

u = User(api_token=tok)
bs = u.get_available_backends()
p5 = bs["ScQ-P5"]

t = Task(user=u)
res = t.retrieve(tid)
print("task_status:", res.task_status)
print("taskname  :", res.taskname)
print("measures  :", res.measures)
print("raw .res  :", json.dumps(res.res, ensure_ascii=False)[:600] if not isinstance(res.res, str) else res.res[:600])
print("transpiled circuit qubits:", getattr(res.transpiled_circuit, "qnum", "?"))

line = {
    "t": datetime.datetime.now().isoformat(timespec="seconds"),
    "p5": p5.task_in_queue,
    "sim10": bs["ScQ-Sim10"].task_in_queue,
    "baihua": bs["Baihua"].task_in_queue,
    "our_status": res.task_status,
    "ours_has_counts": bool(getattr(res, "counts", None)),
}
out = HW / "runs" / "p5_queue_samples.jsonl"
with out.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(line, ensure_ascii=False) + chr(10))
print()
print("appended:", json.dumps(line, ensure_ascii=False))
print("history:")
for ln in out.read_text(encoding="utf-8").splitlines():
    d = json.loads(ln)
    print("  %s  p5=%-5s our_status=%s" % (d["t"], d.get("p5"), d.get("our_status")))
