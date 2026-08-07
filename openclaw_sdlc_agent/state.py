from typing import TypedDict, List, Dict, Any

class SDLCState(TypedDict):
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
    test_result: Dict[str, Any]
    review_result: Dict[str, Any]
    deploy_result: Dict[str, Any]
    status: str
