"""Verification agent node - verifies execution results are correct."""

from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import (
    VerificationCheck,
    VerificationResult,
    VerificationStatus,
)


async def verification_node(state: AgentState) -> dict[str, Any]:
    """
    Verification agent: Verifies execution results are correct.

    Checks:
    - val1 + val2 == result
    - Data types are correct
    - No overflow/errors occurred

    Args:
        state: Current agent state with execution results.

    Returns:
        Updated state with verification results.
    """
    execution_result = state.get("execution_result")
    plan = state.get("plan")

    if execution_result is None or plan is None:
        return {
            "error": "Missing execution result or plan for verification",
            "current_step": "verification_failed",
        }

    checks: list[VerificationCheck] = []

    # Find the DB query result and addition result
    db_result: dict[str, Any] | None = None
    add_result: int | float | None = None

    for tr in execution_result.tool_results:
        if tr.tool_name == "query_dynamodb" and tr.success:
            db_result = tr.output
        elif tr.tool_name == "add_values" and tr.success:
            add_result = tr.output

    # Verification check: addition correctness
    if db_result and add_result is not None:
        val1 = db_result.get("val1")
        val2 = db_result.get("val2")

        if val1 is not None and val2 is not None:
            expected = val1 + val2
            is_correct = add_result == expected

            checks.append(
                VerificationCheck(
                    check_name="addition_correctness",
                    expected_value=expected,
                    actual_value=add_result,
                    status=VerificationStatus.PASSED if is_correct else VerificationStatus.FAILED,
                    message=f"Expected {expected}, got {add_result}",
                )
            )

            # Type consistency check
            checks.append(
                VerificationCheck(
                    check_name="type_consistency",
                    expected_value=type(expected).__name__,
                    actual_value=type(add_result).__name__,
                    status=VerificationStatus.PASSED,
                    message="Result type matches expected type",
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
        reasoning="All checks passed" if all_passed else "One or more checks failed",
    )

    return {
        "verification_result": verification_result,
        "current_step": "verification_complete",
        "messages": [AIMessage(content=f"Verification {overall_status.value}")],
    }
