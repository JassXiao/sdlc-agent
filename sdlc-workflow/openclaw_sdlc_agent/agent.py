import os
import sys
import json
import uuid
import argparse
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from .graph import build_sdlc_graph
from .exporter import save_sdlc_project_to_disk
from .metrics_collector import MetricsCollector

class SDLCOpenClawAgent:
    """支持全局 OpenClaw 模型登录与网关鉴权的 SDLC Agent"""

    def __init__(self, model_name: str = "openai/gpt-5.6-terra", tools: Optional[List[str]] = None):
        self.model_name = model_name
        self.tools = tools or ["exec", "read", "write"]

        # 1. 提取模型 ID
        clean_model_name = model_name.split("/")[-1] if "/" in model_name else model_name

        # 2. 从 OpenClaw 运行环境中获取全局凭证或 Base URL
        # 若全局启用了 OpenClaw Gateway 代理，读取代理配置；若无则自动复用全局 Token
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENCLAW_API_KEY") or "openclaw-global-session"
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENCLAW_GATEWAY_URL")

        init_kwargs = {
            "model": clean_model_name,
            "temperature": 0.2,
            "api_key": api_key,
        }
        if base_url:
            init_kwargs["base_url"] = base_url

        self.llm = ChatOpenAI(**init_kwargs)

        # 3. 初始化工作流图
        try:
            self.app = build_sdlc_graph(llm=self.llm, tools=self.tools)
        except TypeError:
            self.app = build_sdlc_graph()

    def run(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or str(uuid.uuid4())
        thread_config = {"configurable": {"thread_id": sid}}
        
        initial_input = {
            "user_prompt": prompt,
            "model_used": self.model_name,
            "tools_enabled": self.tools,
            "consistency_retries": 0,
            "prd_approved": True,
            "deploy_approved": True,
            "logs": [f"Initialized with openclaw global model: {self.model_name}"]
        }

        collector = MetricsCollector(session_id=sid, model_used=self.model_name)

        try:
            final_state = self.app.invoke(initial_input, thread_config)
            result_text = final_state.get("audit_report") or final_state.get("prd") or f"SDLC 任务已通过全局模型完成（模型: {self.model_name}）"

            collector.stop()
            retries = final_state.get("consistency_retries", 0)
            report = collector.generate_report(status="success", retries=retries)
            print("\n" + "="*40 + "\nExecution Summary Report:\n" + report + "="*40 + "\n")

            return {
                "status": "success",
                "session_id": sid,
                "model": self.model_name,
                "result": result_text,
                "output": final_state
            }
        except Exception as e:
            collector.stop()
            report = collector.generate_report(status=f"error ({str(e)})", retries=0)
            print("\n" + "="*40 + "\nExecution Summary Report (FAILED):\n" + report + "="*40 + "\n")
            return {
                "status": "error",
                "session_id": sid,
                "error": str(e)
            }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw SDLC Agent Entrypoint")
    parser.add_argument("-m", "--message", type=str, help="User prompt/message")
    parser.add_argument("-s", "--session-id", type=str, help="OpenClaw Session/Thread ID")
    parser.add_argument("--model", type=str, default="openai/gpt-5.6-terra", help="LLM Model ID")
    parser.add_argument("--tools", type=str, help="JSON or comma-separated tools list")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    prompt = args.message
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("Error: No message provided.", file=sys.stderr)
        sys.exit(1)

    tools_list = []
    if args.tools:
        try:
            tools_list = json.loads(args.tools)
        except json.JSONDecodeError:
            tools_list = [t.strip() for t in args.tools.split(",") if t.strip()]

    agent = SDLCOpenClawAgent(
        model_name=args.model,
        tools=tools_list if tools_list else None
    )

    result = agent.run(prompt, session_id=args.session_id)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Agent Response: {result.get('result')}")
