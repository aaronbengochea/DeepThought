"""Execution agent node - executes plan steps using tools."""

import logging
import time
from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import (
    ExecutionResult,
    PlanStepType,
    ToolCallResult,
)
from deepthought.tools import (
    add_values,
    divide_values,
    multiply_values,
    query_dynamodb,
    subtract_values,
)

logger = logging.getLogger(__name__)

# Map operation names to tool functions
OPERATION_TO_TOOL = {
    "add": add_values,
    "add_values": add_values,
    "subtract": subtract_values,
    "subtract_values": subtract_values,
    "multiply": multiply_values,
    "multiply_values": multiply_values,
    "divide": divide_values,
    "divide_values": divide_values,
}


async def execution_node(state: AgentState) -> dict[str, Any]:
    """
    Execution agent: Executes the plan from orchestrator.

    Has access to tools:
    - query_dynamodb: Query DynamoDB by primary key
    - add_values: Perform addition of two values
    - multiply_values: Perform multiplication of two values
    - divide_values: Perform division of two values

    Args:
        state: Current agent state with the plan.

    Returns:
        Updated state with execution results.
    """
    plan = state.get("plan")
    if plan is None:
        return {
            "execution_result": None,
            "error": "No plan available for execution",
            "current_step": "execution_failed",
        }

    tool_results: list[ToolCallResult] = []
    executed_steps: list[int] = []
    db_item: dict[str, Any] | None = None
    final_value: int | float | None = None
    operation: str = "add"

    for step in plan.steps:
        if step.step_type == PlanStepType.QUERY_DATABASE:
            executed_steps.append(step.step_number)
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

                if result is None:
                    logger.warning(f"Item not found: {step.parameters}")

            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                logger.error(f"Database query failed: {e}")
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
            # Get the operation from step parameters
            operation = step.parameters.get("operation", "add")
            function_name = step.parameters.get("function", "add_values")

            # Get the appropriate tool
            tool = OPERATION_TO_TOOL.get(operation) or OPERATION_TO_TOOL.get(function_name)

            if tool and db_item:
                executed_steps.append(step.step_number)
                start_time = time.perf_counter()
                try:
                    val1 = db_item.get("val1")
                    val2 = db_item.get("val2")

                    if val1 is None or val2 is None:
                        raise ValueError("val1 or val2 not found in database item")

                    # Execute the tool
                    result = tool.invoke({"val1": val1, "val2": val2})

                    # Handle division by zero error message
                    if isinstance(result, str) and result.startswith("Error:"):
                        raise ValueError(result)

                    final_value = result
                    execution_time = (time.perf_counter() - start_time) * 1000

                    tool_results.append(
                        ToolCallResult(
                            tool_name=function_name,
                            input_params={"val1": val1, "val2": val2},
                            output=result,
                            success=True,
                            execution_time_ms=execution_time,
                        )
                    )
                except Exception as e:
                    execution_time = (time.perf_counter() - start_time) * 1000
                    logger.error(f"Calculation failed: {e}")
                    tool_results.append(
                        ToolCallResult(
                            tool_name=function_name,
                            input_params={"val1": db_item.get("val1"), "val2": db_item.get("val2")},
                            output=None,
                            success=False,
                            error_message=str(e),
                            execution_time_ms=execution_time,
                        )
                    )

    execution_result = ExecutionResult(
        plan_id=plan.plan_id,
        executed_steps=executed_steps,
        tool_results=tool_results,
        final_value=final_value,
        success=all(tr.success for tr in tool_results) and len(tool_results) > 0,
    )

    return {
        "execution_result": execution_result,
        "current_step": "execution_complete",
        "messages": [AIMessage(content=f"Executed {len(tool_results)} tools, operation: {operation}, result: {final_value}")],
    }
