#!/usr/bin/env python3
"""發布前檢查：憑證、大檔、建置產物，以及**不該公開的內容**。

三種檢查：
  1. credentials  — 掃描疑似金鑰字串（BAD / EXTRA 用 chr() 拼接，避免這個檔案自己被命中）
  2. files>3MB    — 單檔超過 3 MB 會擋下
  3. forbidden    — PUBLIC.md 宣告為「不公開」的路徑若出現，直接失敗

第 3 項是為了讓「同步時不小心把內部文件帶進公開 repo」變成不可能，
而不是靠人記得。要改政策請同時改這裡與 PUBLIC.md。
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# --- 1. 疑似憑證 ----------------------------------------------------------
BAD = [chr(97)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(95)+chr(116)+chr(111)+chr(107)+chr(101)+chr(110),
       chr(114)+chr(101)+chr(102)+chr(114)+chr(101)+chr(115)+chr(104)+chr(95)+chr(116)+chr(111)+chr(107)+chr(101)+chr(110),
       chr(99)+chr(108)+chr(105)+chr(101)+chr(110)+chr(116)+chr(95)+chr(115)+chr(101)+chr(99)+chr(114)+chr(101)+chr(116)]
EXTRA = [chr(66)+chr(69)+chr(71)+chr(73)+chr(78)+chr(32)+chr(82)+chr(83)+chr(65)+chr(32)+chr(80)+chr(82)+chr(73)+chr(86)+chr(65)+chr(84)+chr(69)]

# --- 3. 不該公開的路徑（與 PUBLIC.md 一致）--------------------------------
FORBIDDEN = [
    "docs",         # 內部文件集：答辯講稿、主答分工、自我評估、狀態與決策筆記
    "ml/_verify",   # 第三方 HuggingFace 模型卡，我們沒有版權
]

files = [f for f in ROOT.rglob(chr(42)) if f.is_file() and chr(46)+chr(103)+chr(105)+chr(116) not in f.parts]
hits, big = [], []
for f in files:
    if f.stat().st_size > 3_000_000:
        big.append(f)
    try:
        t = f.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56), errors=chr(105)+chr(103)+chr(110)+chr(111)+chr(114)+chr(101))
    except Exception:
        continue
    for p in BAD + EXTRA:
        if p in t:
            hits.append((f.relative_to(ROOT), p))

leaks = [r for r in FORBIDDEN if (ROOT / r).exists()]

print(chr(99)+chr(114)+chr(101)+chr(100)+chr(101)+chr(110)+chr(116)+chr(105)+chr(97)+chr(108)+chr(115)+chr(58), hits or chr(99)+chr(108)+chr(101)+chr(97)+chr(110))
print(chr(102)+chr(105)+chr(108)+chr(101)+chr(115)+chr(62)+chr(51)+chr(77)+chr(66)+chr(58), [str(b.relative_to(ROOT)) for b in big] or chr(110)+chr(111)+chr(110)+chr(101))
print("forbidden:", leaks or "clean")

if leaks:
    print()
    print("!! 公開 repo 出現不該公開的路徑：" + ", ".join(leaks))
    print("   這些是內部文件，應只存在於工作 repo。")
    print("   若已決定要公開，請同時更新 PUBLIC.md 與本檔的 FORBIDDEN 清單。")

sys.exit(1 if (hits or big or leaks) else 0)
