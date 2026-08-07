import sys
import os
import pytest
from typing import Dict, Any

# Ensure current directory is in system path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from openclaw_sdlc_agent.state import SDLCState
from openclaw_sdlc_agent.graph import trace_node
from openclaw_sdlc_agent.nodes import route_consistency_gate, route_prd_approval


def test_sdlc_state_annotations():
    """Verify that SDLCState can be initialized and has expected structure."""
    # Since it is a TypedDict, we construct it as a dict
    state: SDLCState = {
        "user_prompt": "Build a task manager",
        "logs": ["Init"],
        "node_execution_times": {}
    }
    assert state["user_prompt"] == "Build a task manager"
    assert state["logs"] == ["Init"]
    assert isinstance(state["node_execution_times"], dict)


def test_trace_node_success():
    """Verify trace_node records node execution times and logs successfully."""
    @trace_node
    def dummy_success_node(state: SDLCState) -> Dict[str, Any]:
        return {"status": "SUCCESS", "custom_key": "custom_val"}

    initial_state: SDLCState = {
        "user_prompt": "test",
        "logs": ["Initial log"],
        "node_execution_times": {}
    }

    result = dummy_success_node(initial_state)

    # 1. Check custom result is preserved
    assert result["status"] == "SUCCESS"
    assert result["custom_key"] == "custom_val"

    # 2. Check execution times are recorded
    assert "node_execution_times" in result
    assert "dummy_success_node" in result["node_execution_times"]
    assert isinstance(result["node_execution_times"]["dummy_success_node"], float)
    assert result["node_execution_times"]["dummy_success_node"] >= 0

    # 3. Check logs are appended
    assert "logs" in result
    assert len(result["logs"]) > 1
    assert any("Starting node: dummy_success_node" in log for log in result["logs"])
    assert any("Completed node: dummy_success_node" in log for log in result["logs"])


def test_trace_node_crash_and_graceful_capture():
    """Verify trace_node gracefully catches node crashes and logs the error."""
    @trace_node
    def dummy_crash_node(state: SDLCState) -> Dict[str, Any]:
        raise ValueError("Simulated Tester collapse!")

    initial_state: SDLCState = {
        "user_prompt": "test",
        "logs": [],
        "node_execution_times": {}
    }

    # Should not raise exception
    result = dummy_crash_node(initial_state)

    # Status should indicate error
    assert result["status"] == "ERROR_DUMMY_CRASH_NODE"

    # Execution time should still be recorded
    assert "dummy_crash_node" in result["node_execution_times"]

    # Logs should contain exception details
    assert any("crashed with exception: Simulated Tester collapse!" in log for log in result["logs"])


def test_trace_node_consistency_gate_specific_crash():
    """Verify trace_node populates specific fallback values when consistency_gate crashes."""
    @trace_node
    def consistency_gate_node(state: SDLCState) -> Dict[str, Any]:
        raise RuntimeError("Consistency Gate crashed!")

    initial_state: SDLCState = {
        "user_prompt": "test",
        "logs": []
    }

    result = consistency_gate_node(initial_state)

    assert result["status"] == "ERROR_CONSISTENCY_GATE_NODE"
    assert "consistency_audit" in result
    assert result["consistency_audit"]["gate_result"] == "FAIL"
    assert "error" in result["consistency_audit"]
    assert "Consistency Gate crashed!" in result["consistency_audit"]["error"]


def test_route_consistency_gate_graceful_handling():
    """Verify route_consistency_gate handles missing/malformed/crashed audits gracefully."""
    # Case 1: Missing consistency_audit (None)
    state_none: SDLCState = {
        "consistency_audit": None,
        "consistency_retries": 0
    }
    assert route_consistency_gate(state_none) == "fail_halt"

    # Case 2: Malformed consistency_audit (not dict)
    state_invalid_type: SDLCState = {
        "consistency_audit": "this is a string, not dict",
        "consistency_retries": 0
    }
    assert route_consistency_gate(state_invalid_type) == "fail_halt"

    # Case 3: Failed audit, below retry limit
    state_failed_retry: SDLCState = {
        "consistency_audit": {"gate_result": "FAIL"},
        "consistency_retries": 1
    }
    assert route_consistency_gate(state_failed_retry) == "retry"

    # Case 4: Failed audit, retry limit exceeded
    state_failed_halt: SDLCState = {
        "consistency_audit": {"gate_result": "FAIL"},
        "consistency_retries": 3
    }
    assert route_consistency_gate(state_failed_halt) == "fail_halt"

    # Case 5: Passing audit
    state_passing: SDLCState = {
        "consistency_audit": {"gate_result": "PASS"},
        "consistency_retries": 0
    }
    assert route_consistency_gate(state_passing) == "pass"


def test_route_prd_approval_graceful_handling():
    """Verify route_prd_approval is robust and returns expected paths."""
    state_approved: SDLCState = {"prd_approved": True}
    assert route_prd_approval(state_approved) == "approved"

    state_rejected: SDLCState = {"prd_approved": False}
    assert route_prd_approval(state_rejected) == "rejected"

    state_missing: SDLCState = {}
    assert route_prd_approval(state_missing) == "rejected"
