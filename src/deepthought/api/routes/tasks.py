"""Task execution endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.graph import CompiledGraph

from deepthought.api.dependencies import get_agent_graph
from deepthought.models import TaskRequest, TaskResponse

router = APIRouter()


@router.post(
    "/calculate",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a calculation task",
    description="Queries DynamoDB for values and performs addition using the multi-agent system.",
)
async def execute_calculation_task(
    request: TaskRequest,
    graph: CompiledGraph = Depends(get_agent_graph),
) -> TaskResponse:
    """
    Execute a calculation task through the multi-agent pipeline.

    Flow:
    1. Orchestrator creates plan
    2. Execution agent queries DB and performs addition
    3. Verification agent validates result
    4. Response agent formats output
    """
    request_id = str(uuid.uuid4())

    # Initialize state
    initial_state: dict[str, Any] = {
        "request_id": request_id,
        "task_description": f"Query DynamoDB for {request.partition_key}/{request.sort_key} and add val1 + val2",
        "input_params": {
            "partition_key": request.partition_key,
            "sort_key": request.sort_key,
            "operation": request.operation,
        },
        "plan": None,
        "execution_result": None,
        "verification_result": None,
        "formatted_response": None,
        "messages": [],
        "current_step": "start",
        "error": None,
        "should_retry": False,
        "retry_count": 0,
    }

    # Execute the graph
    try:
        final_state = await graph.ainvoke(initial_state)
        formatted = final_state.get("formatted_response")

        if formatted is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent execution completed without a response",
            )

        return TaskResponse(
            success=formatted.success,
            request_id=request_id,
            data=formatted.data,
            execution_summary=formatted.metadata,
            errors=None if formatted.success else [formatted.message],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        ) from e
