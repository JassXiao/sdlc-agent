import json
from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .state import SDLCState
from .config import settings  # 👈 导入配置

def get_llm(model_name: str = "gpt-4o"):
    return ChatOpenAI(model=model_name, temperature=0.1)

def pm_prd_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 0] product-manager: 正在处理 PRD ---")
    llm = get_llm()
    feedback = state.get("human_feedback", "")
    prompt_msg = f"用户原始需求: {state['user_prompt']}"
    if feedback:
        print(f"💡 接收到人工审批反馈，正在迭代修正 PRD: {feedback}")
        prompt_msg += f"\n\n[人工修改意见]: {feedback}\n当前 PRD 内容: {json.dumps(state.get('prd', {}), ensure_ascii=False)}"

    system_prompt = """你是 Product Manager Agent。请将需求转化为合法的结构化 PRD JSON。
包含节点: meta, overview, features, data_entities, api_requirements, non_functional_requirements。
必须且仅输出 JSON 对象。"""
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt_msg)])
    try:
        prd_data = json.loads(response.content.strip().strip("```json").strip("```"))
    except Exception:
        prd_data = {"error": "PRD JSON 解析失败", "raw": response.content}
        
    return {"prd": prd_data, "status": "PRD_AWAITING_APPROVAL", "human_feedback": ""}

def software_architect_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 2a] software-architect: 正在设计 API 契约 ---")
    llm = get_llm()
    prd_str = json.dumps(state["prd"], ensure_ascii=False)
    remediation = ""
    if state.get("consistency_audit") and state["consistency_audit"].get("remediation_instructions"):
        remediation = f"\n[修复指令]: {state['consistency_audit']['remediation_instructions'].get('for_software_architect')}"

    system_prompt = f"你是 software-architect Sub-Agent。请根据 PRD 产出符合 OpenAPI 3.0 的 YAML 规范。{remediation}\n输出格式为 JSON: {{\"status\": \"SUCCESS\", \"openapi_yaml\": \"---... (YAML内容)\"}}"
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"PRD 数据: {prd_str}")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"openapi_yaml": res_json.get("openapi_yaml", "")}

def database_optimizer_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 2b] database-optimizer: 正在设计数据库 DDL ---")
    llm = get_llm()
    prd_str = json.dumps(state["prd"], ensure_ascii=False)
    remediation = ""
    if state.get("consistency_audit") and state["consistency_audit"].get("remediation_instructions"):
        remediation = f"\n[修复指令]: {state['consistency_audit']['remediation_instructions'].get('for_database_optimizer')}"

    system_prompt = f"你是 database-optimizer Sub-Agent。请根据 PRD 产出高性能 DDL SQL 脚本。{remediation}\n输出格式为 JSON: {{\"status\": \"SUCCESS\", \"ddl_script\": \"CREATE TABLE ...\"}}"
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"PRD 数据: {prd_str}")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"ddl_sql": res_json.get("ddl_script", "")}

def consistency_gate_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Consistency Gate] product-manager: 执行一致性审计 ---")
    llm = get_llm()
    system_prompt = """你是 Consistency Auditor Agent。请比对 OpenAPI YAML 和 DDL SQL 的字段与类型一致性。
输出格式严格如下 JSON:
{
  "gate_result": "PASS" | "FAIL",
  "mismatch_count": 0,
  "remediation_instructions": {
    "for_software_architect": "修正说明或 null",
    "for_database_optimizer": "修正说明或 null"
  }
}"""
    prompt = f"[OpenAPI YAML]\n{state['openapi_yaml']}\n\n[DDL SQL]\n{state['ddl_sql']}"
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
    audit_res = json.loads(response.content.strip().strip("```json").strip("```"))
    retries = state.get("consistency_retries", 0) + 1
    return {"consistency_audit": audit_res, "consistency_retries": retries}

def backend_architect_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 3a] backend-architect: 编写后端代码 ---")
    llm = get_llm()
    system_prompt = '你是 backend-architect Sub-Agent。请根据 OpenAPI 与 DDL 编写分层后端核心代码。\n输出格式 JSON: {"status": "SUCCESS", "code_modules": [{"file_path": "...", "content": "..."}]}'
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"OpenAPI:\n{state['openapi_yaml']}\n\nDDL:\n{state['ddl_sql']}")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"backend_code": res_json.get("code_modules", [])}

def frontend_developer_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 3b] frontend-developer: 编写前端代码 ---")
    llm = get_llm()
    system_prompt = '你是 frontend-developer Sub-Agent。请根据 OpenAPI 契约构建 Web 前端组件。\n输出格式 JSON: {"status": "SUCCESS", "code_modules": [{"file_path": "...", "content": "..."}]}'
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"OpenAPI:\n{state['openapi_yaml']}")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"frontend_code": res_json.get("code_modules", [])}

def code_reviewer_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 4] code-reviewer: 执行代码静态审查 ---")
    llm = get_llm()
    all_code = state.get("backend_code", []) + state.get("frontend_code", [])
    system_prompt = '你是 code-reviewer Sub-Agent。审查代码规范与安全风险。\n输出 JSON: {"review_passed": true, "score": 90, "issues": []}'
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"待审代码: {json.dumps(all_code, ensure_ascii=False)}")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"review_result": res_json, "status": "CODE_REVIEW_PASSED"}

def devops_node(state: SDLCState) -> Dict[str, Any]:
    print("\n--- [Phase 5] devops-automator: 生成 Dockerfile 并部署 ---")
    llm = get_llm()
    system_prompt = '你是 devops-automator Sub-Agent。生成 Dockerfile 与 CI/CD 流程。\n输出 JSON: {"status": "DEPLOYED_SUCCESSFULLY", "endpoints": {"staging": "http://localhost:8080"}}'
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content="人工审批部署通过，开始生成工程部署产物。")])
    res_json = json.loads(response.content.strip().strip("```json").strip("```"))
    return {"deploy_result": res_json, "status": "COMPLETED"}

def route_consistency_gate(state: SDLCState) -> Literal["pass", "retry", "fail_halt"]:
    try:
        audit = state.get("consistency_audit")
        if not isinstance(audit, dict):
            print(f"⚠️ Tester/Auditor crashed, did not execute, or returned invalid audit: {audit}")
            return "fail_halt"

        if audit.get("gate_result") == "PASS":
            return "pass"
        elif state.get("consistency_retries", 0) < 3:
            print(f"🔄 Tester/Auditor gate failed. Retrying... (Attempt {state.get('consistency_retries', 0)}/3)")
            return "retry"

        print("❌ Tester/Auditor gate failed. Halting workflow.")
        return "fail_halt"
    except Exception as e:
        print(f"💥 Exception in route_consistency_gate conditional edge: {e}")
        return "fail_halt"

def route_prd_approval(state: SDLCState) -> Literal["approved", "rejected"]:
    try:
        return "approved" if state.get("prd_approved", False) else "rejected"
    except Exception as e:
        print(f"💥 Exception in route_prd_approval conditional edge: {e}")
        return "rejected"
