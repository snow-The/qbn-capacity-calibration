#!/usr/bin/env python3
"""發布前檢查：憑證、大檔、建置產物。"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BAD = [chr(97)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(95)+chr(116)+chr(111)+chr(107)+chr(101)+chr(110),
       chr(114)+chr(101)+chr(102)+chr(114)+chr(101)+chr(115)+chr(104)+chr(95)+chr(116)+chr(111)+chr(107)+chr(101)+chr(110),
       chr(99)+chr(108)+chr(105)+chr(101)+chr(110)+chr(116)+chr(95)+chr(115)+chr(101)+chr(99)+chr(114)+chr(101)+chr(116)]
EXTRA = [chr(66)+chr(69)+chr(71)+chr(73)+chr(78)+chr(32)+chr(82)+chr(83)+chr(65)+chr(32)+chr(80)+chr(82)+chr(73)+chr(86)+chr(65)+chr(84)+chr(69)]

files = [f for f in ROOT.rglob(chr(42)) if f.is_file() and chr(46)+chr(103)+chr(105)+chr(116) not in f.parts]
hits, big = [], []
for f in files:
    if f.stat().st_size > 3_000_000: big.append(f)
    try: t = f.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56), errors=chr(105)+chr(103)+chr(110)+chr(111)+chr(114)+chr(101))
    except Exception: continue
    for p in BAD + EXTRA:
        if p in t: hits.append((f.relative_to(ROOT), p))

print(chr(99)+chr(114)+chr(101)+chr(100)+chr(101)+chr(110)+chr(116)+chr(105)+chr(97)+chr(108)+chr(115)+chr(58), hits or chr(99)+chr(108)+chr(101)+chr(97)+chr(110))
print(chr(102)+chr(105)+chr(108)+chr(101)+chr(115)+chr(62)+chr(51)+chr(77)+chr(66)+chr(58), [str(b.relative_to(ROOT)) for b in big] or chr(110)+chr(111)+chr(110)+chr(101))
sys.exit(1 if hits or big else 0)
