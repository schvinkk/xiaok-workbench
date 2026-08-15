#!/bin/bash
# 小凯求职工作台 —— Linux / macOS 启动脚本
cd "$(dirname "$0")"
echo "安装依赖(如已安装则跳过)..."
pip3 install -r requirements.txt -q 2>/dev/null
echo "启动中..."
python3 app.py
