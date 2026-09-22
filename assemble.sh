#!/bin/bash
# 從筆電的 QBN repo 匯出乾淨的論文 repo。
# 用法：在筆電上 bash assemble.sh
set -euo pipefail

SRC="C:/Users/qq134/source/repos/QBN/projects/qbn-capacity-calibration"
DST="C:/Users/qq134/source/repos/QBN-paper"

echo "=== 1. 匯出需要的目錄 ==="
for p in paper theory formal hardware ml c1; do
  if [ -d "$SRC/$p" ]; then
    rm -rf "$DST/$p"
    cp -r "$SRC/$p" "$DST/$p"
    echo "  + $p"
  else
    echo "  ! $p 不存在，跳過"
  fi
done

echo "=== 2. 文件 ==="
mkdir -p "$DST/docs"
for f in 實驗協定.md; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/docs/" && echo "  + docs/$f"
done

echo "=== 3. 清中間產物 ==="
find "$DST" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$DST" -type f \( -name "*.aux" -o -name "*.log" -o -name "*.fls" -o -name "*.fdb_latexmk" \
     -o -name "*.xdv" -o -name "*.out" -o -name "*.blg" -o -name "*.bbl" -o -name "*.synctex.gz" \) \
     -delete 2>/dev/null || true
rm -rf "$DST/paper/_verify" "$DST/paper/submission" 2>/dev/null || true
rm -f "$DST"/paper/_probe_*.pdf "$DST"/paper/_p*.png 2>/dev/null || true
echo "  完成"

echo "=== 4. 憑證掃描（必須是空的）==="
HITS=$(grep -ril "access_token\|refresh_token\|PRIVATE KEY\|client_secret\|password" "$DST" 2>/dev/null || true)
if [ -n "$HITS" ]; then
  echo "  *** 發現可疑檔案，發佈前必須處理：***"
  echo "$HITS"
  exit 1
else
  echo "  乾淨"
fi

echo "=== 5. 大型檔案（>5MB）==="
find "$DST" -type f -size +5M -exec ls -lh {} \; 2>/dev/null || echo "  無"

echo "=== 6. 統計 ==="
echo "  檔案數: $(find "$DST" -type f | wc -l)"
echo "  總大小: $(du -sh "$DST" | cut -f1)"
echo
echo "=== 完成。接下來：cd $DST && git init -b main && git add -A && git commit ==="
