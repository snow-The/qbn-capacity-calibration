#!/usr/bin/env bash
# WSL 內的環境安裝與版本確認。用腳本檔執行以避免 PowerShell 的引號/PATH 問題。
#
# 用法（在 Windows 端）：
#   wsl -d QBN -u root -- bash /mnt/c/Users/qq134/source/repos/QBN/dev/wsl_install.sh
set -e

export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
VENV=/root/qbn/.venv
PY="$VENV/bin/python"

echo "=== 現況 ==="
"$PY" -c "import cudaq; print('cudaq', cudaq.__version__.split('(')[0].strip())"
"$PY" -c "import torch; print('torch', torch.__version__)" 2>/dev/null || echo "torch: 未安裝"
"$PY" -c "import model2vec; print('model2vec', model2vec.__version__)" 2>/dev/null || echo "model2vec: 未安裝"

echo
echo "=== 安裝 model2vec ==="
VIRTUAL_ENV="$VENV" uv pip install model2vec 2>&1 | tail -6

echo
echo "=== 安裝後確認 ==="
"$PY" -c "import model2vec; print('model2vec', model2vec.__version__)"
"$PY" -c "
import model2vec, inspect
print('可用成員（前 20 個）:', [a for a in dir(model2vec) if not a.startswith('_')][:20])
"
echo
echo "DONE"
