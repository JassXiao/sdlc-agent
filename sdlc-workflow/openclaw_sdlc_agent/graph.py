from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state import SDLCState
from .nodes import (
    pm_prd_node, software_architect_node, database_optimizer_node,
    consistency_gate_node, backend_architect_node, frontend_developer_node,
    code_reviewer_node, devops_node, route_prd_approval, route_consistency_gate
)

def build_sdlc_graph():
    workflow = StateGraph(SDLCState)
    
    workflow.add_node("pm_prd", pm_prd_node)
    workflow.add_node("software_architect", software_architect_node)
    workflow.add_node("database_optimizer", database_optimizer_node)
    workflow.add_node("consistency_gate", consistency_gate_node)
    workflow.add_node("backend_dev", backend_architect_node)
    workflow.add_node("frontend_dev", frontend_developer_node)
    workflow.add_node("code_reviewer", code_reviewer_node)
    workflow.add_node("devops", devops_node)
    
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
