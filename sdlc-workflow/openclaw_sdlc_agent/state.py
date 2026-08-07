from typing import TypedDict, List, Dict, Any

class SDLCState(TypedDict, total=False):
    # Core requirements
    user_prompt: str
    prd: Dict[str, Any]
    prd_approved: bool
    deploy_approved: bool
    human_feedback: str
    openapi_yaml: str
    ddl_sql: str
    consistency_audit: Dict[str, Any]
    consistency_retries: int
    backend_code: List[Dict[str, Any]]
    frontend_code: List[Dict[str, Any]]
    review_result: Dict[str, Any]
    deploy_result: Dict[str, Any]
    status: str

    # Model and settings
    model_used: str
    tools_enabled: List[str]

    # Workflow tracking, logging and telemetry
    logs: List[str]
    audit_report: str
    node_execution_times: Dict[str, float]
