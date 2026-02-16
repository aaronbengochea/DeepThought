"""Response agent node - formats verified results into structured JSON."""

import logging
import time
from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import FormattedResponse, VerificationStatus
from deepthought.tools import format_json

logger = logging.getLogger(__name__)


async def response_node(state: AgentState) -> dict[str, Any]:
    """
    Response agent: Formats verified results into structured JSON.

    Creates a client-ready response with:
    - val1, val2, and result from execution
    - Operation performed (add, multiply, divide)
    - Verification status
    - Metadata about the execution

    Args:
        state: Current agent state with all previous results.

    Returns:
        Updated state with formatted response.
    """
    logger.info(f"Response node entered. current_step={state.get('current_step')}, error={state.get('error')}")
    node_start_time = time.perf_counter()

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
        duration_ms = (time.perf_counter() - node_start_time) * 1000
        return {
            "formatted_response": formatted,
            "current_step": "complete",
            "node_timings": {"response": duration_ms},
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
        duration_ms = (time.perf_counter() - node_start_time) * 1000
        return {
            "formatted_response": formatted,
            "current_step": "complete",
            "node_timings": {"response": duration_ms},
            "messages": [AIMessage(content="Response formatted with missing data error")],
        }

    # Extract values from execution result
    db_result: dict[str, Any] | None = None
    calc_result: int | float | None = None
    operation: str = "add"

    for tr in execution_result.tool_results:
        if tr.tool_name == "query_dynamodb" and tr.success:
            db_result = tr.output
        elif tr.tool_name in ("add_values", "subtract_values", "multiply_values", "divide_values") and tr.success:
            calc_result = tr.output
            # Extract operation from tool name
            if tr.tool_name == "add_values":
                operation = "add"
            elif tr.tool_name == "subtract_values":
                operation = "subtract"
            elif tr.tool_name == "multiply_values":
                operation = "multiply"
            elif tr.tool_name == "divide_values":
                operation = "divide"

    # Also check plan for operation
    for step in plan.steps:
        if step.parameters.get("operation"):
            operation = step.parameters["operation"]
            break

    # Build success response
    is_success = verification_result.overall_status == VerificationStatus.PASSED

    # Get verification message from checks
    verification_message = verification_result.reasoning
    if verification_result.checks:
        verification_message = verification_result.checks[0].message

    # Use format_json tool if available, otherwise build manually
    try:
        val1 = db_result.get("val1") if db_result else None
        val2 = db_result.get("val2") if db_result else None

        if val1 is not None and val2 is not None and calc_result is not None:
            tool_result = format_json.invoke({
                "val1": val1,
                "val2": val2,
                "result": calc_result,
                "operation": operation,
                "verification_passed": is_success,
                "verification_message": verification_message,
            })

            # Merge tool result with our data format
            data = {
                "val1": val1,
                "val2": val2,
                "result": calc_result,
                "operation": operation,
                "expression": tool_result.get("calculation", {}).get("expression", f"{val1} {operation} {val2} = {calc_result}"),
                "verification_status": verification_result.overall_status.value,
            }
        else:
            data = {
                "val1": val1,
                "val2": val2,
                "result": calc_result,
                "operation": operation,
                "verification_status": verification_result.overall_status.value,
            }
    except Exception as e:
        logger.warning(f"format_json tool failed, using fallback: {e}")
        data = {
            "val1": db_result.get("val1") if db_result else None,
            "val2": db_result.get("val2") if db_result else None,
            "result": calc_result,
            "operation": operation,
            "verification_status": verification_result.overall_status.value,
        }

    formatted = FormattedResponse(
        success=is_success,
        data=data,
        metadata={
            "request_id": state["request_id"],
            "plan_id": plan.plan_id,
            "steps_executed": len(execution_result.tool_results),
            "verification_confidence": verification_result.confidence_score,
            "verification_checks": len(verification_result.checks),
        },
        message=f"{operation.capitalize()} completed successfully" if is_success else f"{operation.capitalize()} completed with verification failures",
    )

    duration_ms = (time.perf_counter() - node_start_time) * 1000
    return {
        "formatted_response": formatted,
        "current_step": "complete",
        "node_timings": {"response": duration_ms},
        "messages": [AIMessage(content=f"Response formatted for {operation}")],
    }
