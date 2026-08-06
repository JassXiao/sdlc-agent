#!/bin/bash

# 1. 以可编辑模式将当前 Agent 注册到当前 Python 环境
pip install -e .

# 2. 使用 OpenClaw 正确的 --path 参数安装当前目录
openclaw agent install --path .
