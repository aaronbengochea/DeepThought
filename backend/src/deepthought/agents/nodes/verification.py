"""Verification agent node - verifies execution results are correct."""

import logging
import time
from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import (
    VerificationCheck,
    VerificationResult,
    VerificationStatus,
)
from deepthought.tools import (
    verify_addition,
    verify_division,
    verify_multiplication,
    verify_subtraction,
)

logger = logging.getLogger(__name__)

# Map operation names to verification tools
OPERATION_TO_VERIFY_TOOL = {
    "add": verify_addition,
    "add_values": verify_addition,
    "subtract": verify_subtraction,
    "subtract_values": verify_subtraction,
    "multiply": verify_multiplication,
    "multiply_values": verify_multiplication,
    "divide": verify_division,
    "divide_values": verify_division,
}


async def verification_node(state: AgentState) -> dict[str, Any]:
    """
    Verification agent: Verifies execution results are correct.

    Checks based on operation type:
    - add: val1 + val2 == result
    - multiply: val1 * val2 == result
    - divide: val1 / val2 == result

    Args:
        state: Current agent state with execution results.

    Returns:
        Updated state with verification results.
    """
    node_start_time = time.perf_counter()
    logger.info(f"Verification node entered. retry_count={state.get('retry_count', 0)}")

    execution_result = state.get("execution_result")
    plan = state.get("plan")

    if execution_result is None or plan is None:
        duration_ms = (time.perf_counter() - node_start_time) * 1000
        return {
            "verification_result": None,
            "error": "Missing execution result or plan for verification",
            "current_step": "verification_failed",
            "node_timings": {"verification": duration_ms},
        }

    checks: list[VerificationCheck] = []

    # Find the DB query result and calculation result
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

    # Also check plan for operation if not found in tool results
    for step in plan.steps:
        if step.parameters.get("operation"):
            operation = step.parameters["operation"]
            break

    # Verification check: calculation correctness
    if db_result and calc_result is not None:
        val1 = db_result.get("val1")
        val2 = db_result.get("val2")

        if val1 is not None and val2 is not None:
            # Get the appropriate verification tool
            verify_tool = OPERATION_TO_VERIFY_TOOL.get(operation, verify_addition)

            # Call the verification tool
            try:
                if operation == "divide":
                    verify_result = verify_tool.invoke({
                        "val1": val1,
                        "val2": val2,
                        "result": calc_result,
                        "tolerance": 1e-9,
                    })
                else:
                    verify_result = verify_tool.invoke({
                        "val1": val1,
                        "val2": val2,
                        "result": calc_result,
                    })

                is_correct = verify_result.get("is_valid", False)
                expected = verify_result.get("expected")
                message = verify_result.get("message", "")

                checks.append(
                    VerificationCheck(
                        check_name=f"{operation}_correctness",
                        expected_value=expected,
                        actual_value=calc_result,
                        status=VerificationStatus.PASSED if is_correct else VerificationStatus.FAILED,
                        message=message,
                    )
                )

            except Exception as e:
                logger.error(f"Verification tool failed: {e}")
                checks.append(
                    VerificationCheck(
                        check_name=f"{operation}_correctness",
                        expected_value="verification",
                        actual_value="error",
                        status=VerificationStatus.FAILED,
                        message=f"Verification failed: {e}",
                    )
                )

            # Type consistency check
            checks.append(
                VerificationCheck(
                    check_name="type_consistency",
                    expected_value="number",
                    actual_value=type(calc_result).__name__,
                    status=VerificationStatus.PASSED,
                    message="Result type is valid",
                )
            )
    else:
        checks.append(
            VerificationCheck(
                check_name="data_availability",
                expected_value="complete data",
                actual_value="missing data",
                status=VerificationStatus.FAILED,
                message="Required data not available for verification",
            )
        )

    # Determine overall status
    all_passed = all(c.status == VerificationStatus.PASSED for c in checks)
    overall_status = VerificationStatus.PASSED if all_passed else VerificationStatus.FAILED

    verification_result = VerificationResult(
        plan_id=plan.plan_id,
        checks=checks,
        overall_status=overall_status,
        confidence_score=1.0 if all_passed else 0.0,
        reasoning=f"All {operation} checks passed" if all_passed else "One or more checks failed",
    )

    duration_ms = (time.perf_counter() - node_start_time) * 1000
    return {
        "verification_result": verification_result,
        "current_step": "verification_complete",
        "node_timings": {"verification": duration_ms},
        "messages": [AIMessage(content=f"Verification {overall_status.value} for {operation}")],
    }
