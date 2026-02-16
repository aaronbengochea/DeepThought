"""Conditional edge routing functions for the agent graph."""

from typing import Literal

from deepthought.agents.state import AgentState
from deepthought.models.agents import VerificationStatus


def route_after_orchestrator(state: AgentState) -> Literal["execution", "error"]:
    """
    Route after orchestrator node.

    Routes to:
    - "execution": Plan was created successfully
    - "error": Plan creation failed or error occurred

    Args:
        state: Current agent state.

    Returns:
        The next node to route to.
    """
    if state.get("error") or state.get("plan") is None:
        return "error"
    return "execution"


def route_after_execution(
    state: AgentState,
) -> Literal["verification", "retry", "error"]:
    """
    Route after execution node.

    Routes to:
    - "verification": Execution succeeded
    - "retry": Execution failed but can retry
    - "error": Execution failed and max retries reached

    Args:
        state: Current agent state.

    Returns:
        The next node to route to.
    """
    execution_result = state.get("execution_result")

    if execution_result is None:
        return "error"

    if not execution_result.success:
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            return "retry"
        return "error"

    return "verification"


def route_after_verification(
    state: AgentState,
) -> Literal["response", "retry_execution", "error"]:
    """
    Route after verification node.

    Routes to:
    - "response": Verification passed
    - "retry_execution": Verification failed but can retry execution
    - "error": Verification failed and max retries reached

    Args:
        state: Current agent state.

    Returns:
        The next node to route to.
    """
    verification_result = state.get("verification_result")

    if verification_result is None:
        return "error"

    if verification_result.overall_status == VerificationStatus.FAILED:
        retry_count = state.get("retry_count", 0)
        if retry_count < 2:
            return "retry_execution"
        return "error"

    return "response"
