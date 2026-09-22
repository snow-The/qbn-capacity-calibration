#!/usr/bin/env bash
# CUDA-Q 即時驗證：證明它真的在這台機器上跑得起來。
#
# 用法：wsl -d QBN -u root -- bash <repo-root>/dev/wsl_hello.sh
set -e
export PYTHONIOENCODING=utf-8
cd <repo-root>
/root/qbn/.venv/bin/python dev/hello_cudaq.py
