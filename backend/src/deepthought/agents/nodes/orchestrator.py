"""Orchestrator agent node - creates comprehensive plans for task execution using LLM reasoning."""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from deepthought.agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from deepthought.agents.state import AgentState
from deepthought.llm import get_llm
from deepthought.models.agents import Plan, PlanStep, PlanStepType

logger = logging.getLogger(__name__)

# Mapping from plan action strings to PlanStepType
ACTION_TO_STEP_TYPE = {
    "query_database": PlanStepType.QUERY_DATABASE,
    "execute_operation": PlanStepType.EXECUTE_FUNCTION,
    "verify_result": PlanStepType.VERIFY_RESULT,
    "format_response": PlanStepType.FORMAT_RESPONSE,
}

# Mapping from operation names to function names
OPERATION_TO_FUNCTION = {
    "add": "add_values",
    "subtract": "subtract_values",
    "multiply": "multiply_values",
    "divide": "divide_values",
}


def _parse_llm_plan(response_text: str, state: AgentState) -> Plan:
    """Parse the LLM response into a Plan object.

    Args:
        response_text: The raw LLM response text.
        state: The current agent state.

    Returns:
        A Plan object.

    Raises:
        ValueError: If the response cannot be parsed.
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON block in response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            # Try to find JSON object directly
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
        else:
            raise ValueError("No JSON found in response")

        plan_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON in LLM response: {e}")

    # Extract operation
    operation = plan_data.get("operation", "add")

    # Build PlanStep objects
    steps = []
    for step_data in plan_data.get("steps", []):
        action = step_data.get("action", "")
        step_type = ACTION_TO_STEP_TYPE.get(action, PlanStepType.EXECUTE_FUNCTION)

        # Build parameters
        parameters = step_data.get("parameters", {})
        if action == "execute_operation":
            # Add the function name based on operation
            parameters["function"] = OPERATION_TO_FUNCTION.get(operation, "add_values")
            parameters["operation"] = operation

        steps.append(
            PlanStep(
                step_number=step_data.get("step_number", len(steps) + 1),
                step_type=step_type,
                description=step_data.get("description", ""),
                parameters=parameters,
                depends_on=step_data.get("depends_on", []),
            )
        )

    return Plan(
        plan_id=state["request_id"],
        created_at=datetime.now(timezone.utc),
        task_description=plan_data.get("task_understanding", state["task_description"]),
        steps=steps,
        expected_outcome=plan_data.get("expected_outcome", "Calculation result"),
    )


def _create_fallback_plan(state: AgentState) -> Plan:
    """Create a fallback plan when LLM fails.

    Uses the default operation specified in input_params or defaults to 'add'.

    Args:
        state: The current agent state.

    Returns:
        A Plan object with default steps.
    """
    input_params = state["input_params"]
    operation = input_params.get("operation", "add")
    function_name = OPERATION_TO_FUNCTION.get(operation, "add_values")

    return Plan(
        plan_id=state["request_id"],
        created_at=datetime.now(timezone.utc),
        task_description=state["task_description"],
        steps=[
            PlanStep(
                step_number=1,
                step_type=PlanStepType.QUERY_DATABASE,
                description="Query DynamoDB to retrieve calculation item",
                parameters={
                    "pk": input_params["partition_key"],
                    "sk": input_params["sort_key"],
                },
                depends_on=[],
            ),
            PlanStep(
                step_number=2,
                step_type=PlanStepType.EXECUTE_FUNCTION,
                description=f"Perform {operation} operation on val1 and val2",
                parameters={"function": function_name, "operation": operation},
                depends_on=[1],
            ),
            PlanStep(
                step_number=3,
                step_type=PlanStepType.VERIFY_RESULT,
                description=f"Verify the {operation} result is correct",
                parameters={"operation": operation},
                depends_on=[1, 2],
            ),
            PlanStep(
                step_number=4,
                step_type=PlanStepType.FORMAT_RESPONSE,
                description="Format verified result into JSON response",
                parameters={"operation": operation},
                depends_on=[3],
            ),
        ],
        expected_outcome=f"Structured JSON with val1, val2, {operation} result, and verification status",
    )


async def orchestrator_node(state: AgentState) -> dict[str, Any]:
    """
    Orchestrator agent: Uses LLM to create a comprehensive step-by-step plan.

    The orchestrator analyzes the task and determines:
    - Which operation to perform (add, multiply, divide)
    - The sequence of steps needed
    - Expected outcomes

    Args:
        state: Current agent state with request context.

    Returns:
        Updated state with the generated plan.
    """
    start_time = time.perf_counter()
    input_params = state["input_params"]

    # Build the user message with task details
    user_message = f"""
Task: {state["task_description"]}

Input Parameters:
- Partition Key: {input_params["partition_key"]}
- Sort Key: {input_params["sort_key"]}
- Requested Operation: {input_params.get("operation", "add")}

Please create an execution plan for this calculation task.
"""

    try:
        # Get the LLM and invoke it
        llm = get_llm()
        messages = [
            HumanMessage(content=ORCHESTRATOR_SYSTEM_PROMPT + user_message)
        ]

        response = await llm.ainvoke(messages)
        response_text = response.content if hasattr(response, "content") else str(response)

        logger.debug(f"Orchestrator LLM response: {response_text}")

        # Parse the LLM response into a Plan
        logger.info(f"Orchestrator LLM raw response: {response_text[:500]}")
        plan = _parse_llm_plan(response_text, state)
        logger.info(f"Parsed plan: {len(plan.steps)} steps, types={[s.step_type.value for s in plan.steps]}")

        duration_ms = (time.perf_counter() - start_time) * 1000
        return {
            "plan": plan,
            "current_step": "orchestrator_complete",
            "node_timings": {"orchestrator": duration_ms},
            "messages": [AIMessage(content=f"Created plan with {len(plan.steps)} steps for {input_params.get('operation', 'add')} operation")],
        }

    except Exception as e:
        logger.warning(f"LLM planning failed, using fallback: {e}")

        # Use fallback plan if LLM fails
        plan = _create_fallback_plan(state)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return {
            "plan": plan,
            "current_step": "orchestrator_complete",
            "node_timings": {"orchestrator": duration_ms},
            "messages": [AIMessage(content=f"Created fallback plan with {len(plan.steps)} steps (LLM unavailable)")],
        }
