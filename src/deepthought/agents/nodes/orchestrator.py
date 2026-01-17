"""Orchestrator agent node - creates comprehensive plans for task execution."""

from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage

from deepthought.agents.state import AgentState
from deepthought.models.agents import Plan, PlanStep, PlanStepType


async def orchestrator_node(state: AgentState) -> dict[str, Any]:
    """
    Orchestrator agent: Creates a comprehensive step-by-step plan.

    For the calculation task:
    1. Query DynamoDB by primary key to retrieve val1 and val2
    2. Execute add_values(val1, val2) function
    3. Pass results to verification
    4. Format response

    Args:
        state: Current agent state with request context.

    Returns:
        Updated state with the generated plan.
    """
    input_params = state["input_params"]

    # Create the plan for the calculation task
    plan = Plan(
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
                description="Add val1 and val2 from retrieved item",
                parameters={"function": "add_values"},
                depends_on=[1],
            ),
            PlanStep(
                step_number=3,
                step_type=PlanStepType.VERIFY_RESULT,
                description="Verify the addition result is correct",
                parameters={},
                depends_on=[1, 2],
            ),
            PlanStep(
                step_number=4,
                step_type=PlanStepType.FORMAT_RESPONSE,
                description="Format verified result into JSON response",
                parameters={},
                depends_on=[3],
            ),
        ],
        expected_outcome="Structured JSON with val1, val2, sum, and verification status",
    )

    return {
        "plan": plan,
        "current_step": "orchestrator_complete",
        "messages": [AIMessage(content=f"Created plan with {len(plan.steps)} steps")],
    }
