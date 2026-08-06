import os
import zipfile
from pathlib import Path

# 定义源码内容
FILES = {
    "requirements.txt": """langgraph>=0.2.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
pydantic>=2.0
pyyaml
""",

    "setup.py": """from setuptools import setup, find_packages

setup(
    name="openclaw-sdlc-agent",
    version="1.0.0",
    description="An enterprise SDLC Agent with MemorySaver checkpointer and Human-in-the-Loop approval for OpenClaw.",
    author="Dev Team",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.2.0",
        "langchain-openai>=0.1.0",
        "langchain-core>=0.2.0",
        "pydantic>=2.0",
        "pyyaml",
    ],
    entry_points={
        "openclaw.agents": [
            "sdlc_agent = openclaw_sdlc_agent.agent:SDLCOpenClawAgent",
        ],
    },
    python_requires=">=3.10",
)
""",

    "openclaw.yaml": """openclaw_version: "1.0"
agent:
  name: "sdlc_agent"
  display_name: "Software Development Lifecycle Agent"
  description: "全流程自动化软件工程 Agent，支持 PRD 迭代、API/DDL 审计、前后端代码生成与人工审批（HITL）中断管理。"
  version: "1.0.0"
  entrypoint: "openclaw_sdlc_agent.agent:SDLCOpenClawAgent"
  
  config:
    env:
      - name: "OPENAI_API_KEY"
        required: true
        description: "OpenAI API 密钥"
      - name: "OPENAI_MODEL"
        default: "gpt-4o"
        description: "使用的 LLM 模型标识"

  capabilities:
    - human_in_the_loop
    - state_checkpointing
    - disk_export
""",

    "README.md": """# OpenClaw SDLC Agent

全流程自动化软件工程 Agent，基于 LangGraph + MemorySaver 实现断点持久化与 Human-in-the-Loop (HITL) 人工审批。

## 安装说明

```bash
# 解压并本地可编辑安装
pip install -e .
