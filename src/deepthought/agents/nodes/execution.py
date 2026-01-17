"""Execution agent node - executes the plan created by the orchestrator."""

import time
from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import (
    ExecutionResult,
    PlanStepType,
    ToolCallResult,
)
from deepthought.tools import add_values, query_dynamodb


async def execution_node(state: AgentState) -> dict[str, Any]:
    """
    Execution agent: Executes the plan from orchestrator.

    Has access to tools:
    - query_dynamodb: Query DynamoDB by primary key
    - add_values: Perform addition of two values

    Args:
        state: Current agent state with the plan.

    Returns:
        Updated state with execution results.
    """
    plan = state["plan"]
    if plan is None:
        return {
            "error": "No plan available for execution",
            "current_step": "execution_failed",
        }

    tool_results: list[ToolCallResult] = []
    db_item: dict[str, Any] | None = None
    final_value: int | float | None = None

    for step in plan.steps:
        if step.step_type == PlanStepType.QUERY_DATABASE:
            # Execute DynamoDB query
            start_time = time.perf_counter()
            try:
                result = await query_dynamodb.ainvoke(
                    {"pk": step.parameters["pk"], "sk": step.parameters["sk"]}
                )
                db_item = result
                execution_time = (time.perf_counter() - start_time) * 1000

                tool_results.append(
                    ToolCallResult(
                        tool_name="query_dynamodb",
                        input_params=step.parameters,
                        output=result,
                        success=result is not None,
                        error_message=None if result else "Item not found",
                        execution_time_ms=execution_time,
                    )
                )
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                tool_results.append(
                    ToolCallResult(
                        tool_name="query_dynamodb",
                        input_params=step.parameters,
                        output=None,
                        success=False,
                        error_message=str(e),
                        execution_time_ms=execution_time,
                    )
                )

        elif step.step_type == PlanStepType.EXECUTE_FUNCTION:
            if step.parameters.get("function") == "add_values" and db_item:
                start_time = time.perf_counter()
                try:
                    val1 = db_item.get("val1")
                    val2 = db_item.get("val2")

                    if val1 is None or val2 is None:
                        raise ValueError("val1 or val2 not found in database item")

                    result = add_values.invoke({"val1": val1, "val2": val2})
                    final_value = result
                    execution_time = (time.perf_counter() - start_time) * 1000

                    tool_results.append(
                        ToolCallResult(
                            tool_name="add_values",
                            input_params={"val1": val1, "val2": val2},
                            output=result,
                            success=True,
                            execution_time_ms=execution_time,
                        )
                    )
                except Exception as e:
                    execution_time = (time.perf_counter() - start_time) * 1000
                    tool_results.append(
                        ToolCallResult(
                            tool_name="add_values",
                            input_params={"val1": db_item.get("val1"), "val2": db_item.get("val2")},
                            output=None,
                            success=False,
                            error_message=str(e),
                            execution_time_ms=execution_time,
                        )
                    )

    execution_result = ExecutionResult(
        plan_id=plan.plan_id,
        executed_steps=[tr.tool_name for tr in tool_results],  # type: ignore[misc]
        tool_results=tool_results,
        final_value=final_value,
        success=all(tr.success for tr in tool_results),
    )

    return {
        "execution_result": execution_result,
        "current_step": "execution_complete",
        "messages": [AIMessage(content=f"Executed {len(tool_results)} tools")],
    }
