"""Response agent node - formats verified results into structured JSON."""

from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import FormattedResponse, VerificationStatus


async def response_node(state: AgentState) -> dict[str, Any]:
    """
    Response agent: Formats verified results into structured JSON.

    Creates a client-ready response with:
    - val1, val2, and sum from execution
    - Verification status
    - Metadata about the execution

    Args:
        state: Current agent state with all previous results.

    Returns:
        Updated state with formatted response.
    """
    execution_result = state.get("execution_result")
    verification_result = state.get("verification_result")
    plan = state.get("plan")
    error = state.get("error")

    # Handle error case
    if error:
        formatted = FormattedResponse(
            success=False,
            data={},
            metadata={"request_id": state["request_id"]},
            message=f"Error: {error}",
        )
        return {
            "formatted_response": formatted,
            "current_step": "complete",
            "messages": [AIMessage(content="Response formatted with error")],
        }

    # Handle missing data
    if execution_result is None or verification_result is None or plan is None:
        formatted = FormattedResponse(
            success=False,
            data={},
            metadata={"request_id": state["request_id"]},
            message="Incomplete execution - missing required data",
        )
        return {
            "formatted_response": formatted,
            "current_step": "complete",
            "messages": [AIMessage(content="Response formatted with missing data error")],
        }

    # Extract values from execution result
    db_result: dict[str, Any] | None = None
    add_result: int | float | None = None

    for tr in execution_result.tool_results:
        if tr.tool_name == "query_dynamodb" and tr.success:
            db_result = tr.output
        elif tr.tool_name == "add_values" and tr.success:
            add_result = tr.output

    # Build success response
    is_success = verification_result.overall_status == VerificationStatus.PASSED

    formatted = FormattedResponse(
        success=is_success,
        data={
            "val1": db_result.get("val1") if db_result else None,
            "val2": db_result.get("val2") if db_result else None,
            "result": add_result,
            "verification_status": verification_result.overall_status.value,
        },
        metadata={
            "request_id": state["request_id"],
            "plan_id": plan.plan_id,
            "steps_executed": len(execution_result.tool_results),
            "verification_confidence": verification_result.confidence_score,
            "verification_checks": len(verification_result.checks),
        },
        message="Calculation completed successfully" if is_success else "Calculation completed with verification failures",
    )

    return {
        "formatted_response": formatted,
        "current_step": "complete",
        "messages": [AIMessage(content="Response formatted")],
    }
