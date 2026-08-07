import time
import logging
from typing import Callable, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state import SDLCState
from .nodes import (
    pm_prd_node, software_architect_node, database_optimizer_node,
    consistency_gate_node, backend_architect_node, frontend_developer_node,
    code_reviewer_node, devops_node, route_prd_approval, route_consistency_gate
)

# Configure standard logger
logger = logging.getLogger("openclaw_sdlc_agent.graph")

def trace_node(node_func: Callable[[SDLCState], Dict[str, Any]]) -> Callable[[SDLCState], Dict[str, Any]]:
    def wrapper(state: SDLCState) -> Dict[str, Any]:
        node_name = node_func.__name__
        start_time = time.perf_counter()

        # Initialize logs safely
        logs = list(state.get("logs") or [])
        logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting node: {node_name}")

        try:
            # Execute node
            result = node_func(state)
            if not isinstance(result, dict):
                result = {}
        except Exception as e:
            # Catch exceptions gracefully, record error, log and return safe dict
            logger.exception(f"Exception crashed node {node_name}: {e}")
            logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Node {node_name} crashed with exception: {e}")

            result = {
                "status": f"ERROR_{node_name.upper()}",
                "logs": logs
            }

            # Special default values for critical testing/audit nodes to satisfy conditional edge types
            if node_name == "consistency_gate_node":
                result["consistency_audit"] = {
                    "gate_result": "FAIL",
                    "mismatch_count": -1,
                    "remediation_instructions": {
                        "for_software_architect": f"Node crashed: {e}",
                        "for_database_optimizer": f"Node crashed: {e}"
                    },
                    "error": str(e)
                }
            elif node_name == "code_reviewer_node":
                result["review_result"] = {
                    "review_passed": False,
                    "score": 0,
                    "issues": [f"Node crashed: {e}"],
                    "error": str(e)
                }

        duration = time.perf_counter() - start_time
        logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Completed node: {node_name} in {duration:.4f} seconds")

        # Merge tracking data into result
        if "logs" not in result:
            result["logs"] = logs
        else:
            if isinstance(result["logs"], list):
                result["logs"] = logs + [item for item in result["logs"] if item not in logs]
            else:
                result["logs"] = logs

        # Record execution time trace
        node_execution_times = dict(state.get("node_execution_times") or {})
        node_execution_times[node_name] = duration
        result["node_execution_times"] = node_execution_times

        return result
    return wrapper

def build_sdlc_graph():
    workflow = StateGraph(SDLCState)
    
    workflow.add_node("pm_prd", trace_node(pm_prd_node))
    workflow.add_node("software_architect", trace_node(software_architect_node))
    workflow.add_node("database_optimizer", trace_node(database_optimizer_node))
    workflow.add_node("consistency_gate", trace_node(consistency_gate_node))
    workflow.add_node("backend_dev", trace_node(backend_architect_node))
    workflow.add_node("frontend_dev", trace_node(frontend_developer_node))
    workflow.add_node("code_reviewer", trace_node(code_reviewer_node))
    workflow.add_node("devops", trace_node(devops_node))
    
    workflow.add_edge(START, "pm_prd")
    
    workflow.add_conditional_edges("pm_prd", route_prd_approval, {
        "approved": "software_architect",
        "rejected": "pm_prd"
    })
    
    workflow.add_edge("pm_prd", "database_optimizer")
    workflow.add_edge("software_architect", "consistency_gate")
    workflow.add_edge("database_optimizer", "consistency_gate")
    
    workflow.add_conditional_edges("consistency_gate", route_consistency_gate, {
        "pass": "backend_dev",
        "retry": "software_architect",
        "fail_halt": END
    })
    
    workflow.add_edge("backend_dev", "frontend_dev")
    workflow.add_edge("frontend_dev", "code_reviewer")
    workflow.add_edge("code_reviewer", "devops")
    workflow.add_edge("devops", END)
    
    memory = MemorySaver()
    
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["software_architect", "devops"]
    )
    return app
