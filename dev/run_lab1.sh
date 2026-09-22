#!/usr/bin/env bash
# 執行 Lab 1 維度掃描。輸出同時寫到 results/lab1/lab1_stdout.txt。
# 用法：wsl -d QBN -u root -- bash <repo-root>/dev/run_lab1.sh
set -e
cd <repo-root>
mkdir -p results/lab1
export PYTHONIOENCODING=utf-8
/root/qbn/.venv/bin/python dev/lab1_dim_sweep.py 2>&1 | tee results/lab1/lab1_stdout.txt
echo "EXIT=$?"
