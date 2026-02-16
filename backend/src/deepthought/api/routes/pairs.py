"""Pair management and operation endpoints."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.state import CompiledStateGraph

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_agent_graph, get_logs_db_client, get_pairs_db_client
from deepthought.db import DynamoDBClient
from deepthought.models.logs import AgentStepOutput, OperateRequest, OperationLogResponse
from deepthought.models.pairs import PairCreate, PairResponse

router = APIRouter()


@router.post(
    "/",
    response_model=PairResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a number pair",
    description="Creates a new number pair for the authenticated user. Returns the created pair.",
)
async def create_pair(
    request: PairCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    pairs_db: DynamoDBClient = Depends(get_pairs_db_client),
) -> PairResponse:
    """Create a new number pair.

    1. Generate a unique pair_id
    2. Store the pair in DynamoDB (pk=user_email, sk=PAIR#{pair_id})
    3. Return the created pair
    """
    user_email = current_user["pk"]
    pair_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    pair_item: dict[str, Any] = {
        "pk": user_email,
        "sk": pair_id,
        "val1": request.val1,
        "val2": request.val2,
        "created_at": now.isoformat(),
    }
    await pairs_db.put_item(pair_item)

    return PairResponse(
        pair_id=pair_id,
        val1=request.val1,
        val2=request.val2,
        created_at=now,
    )


@router.get(
    "/",
    response_model=list[PairResponse],
    status_code=status.HTTP_200_OK,
    summary="List all pairs for the current user",
    description="Returns all number pairs belonging to the authenticated user.",
)
async def list_pairs(
    current_user: dict[str, Any] = Depends(get_current_user),
    pairs_db: DynamoDBClient = Depends(get_pairs_db_client),
) -> list[PairResponse]:
    """List all number pairs for the authenticated user.

    Queries DynamoDB with pk=user_email to retrieve all pairs
    belonging to this user. The sk is the pair_id (UUID).
    """
    user_email = current_user["pk"]
    items = await pairs_db.query(pk=user_email)

    pairs = [
        PairResponse(
            pair_id=item["sk"],
            val1=item["val1"],
            val2=item["val2"],
            created_at=item["created_at"],
        )
        for item in items
    ]

    return pairs


@router.post(
    "/{pair_id}/operate",
    response_model=OperationLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an operation on a pair",
    description="Runs an operation (add, subtract, multiply, divide) on a number pair using the agent pipeline.",
)
async def operate_on_pair(
    pair_id: str,
    request: OperateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    pairs_db: DynamoDBClient = Depends(get_pairs_db_client),
    logs_db: DynamoDBClient = Depends(get_logs_db_client),
    graph: CompiledStateGraph = Depends(get_agent_graph),
) -> OperationLogResponse:
    """Execute an operation on a number pair through the agent pipeline.

    1. Fetch the pair from DynamoDB, verify ownership
    2. Invoke the agent graph with val1, val2, and operation
    3. Capture telemetry from the final state
    4. Store the operation log in the logs table
    5. Return the log with all agent steps
    """
    user_email = current_user["pk"]

    # Fetch pair and verify ownership
    pair = await pairs_db.get_item(pk=user_email, sk=pair_id)
    if pair is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pair not found",
        )

    # Build initial state with direct values (skips DB query in execution node)
    request_id = str(uuid.uuid4())
    initial_state: dict[str, Any] = {
        "request_id": request_id,
        "task_description": f"Perform {request.operation} on val1={pair['val1']} and val2={pair['val2']}",
        "input_params": {
            "val1": pair["val1"],
            "val2": pair["val2"],
            "operation": request.operation,
            "partition_key": f"PAIR#{pair_id}",
            "sort_key": "DIRECT",
        },
        "plan": None,
        "execution_result": None,
        "verification_result": None,
        "formatted_response": None,
        "messages": [],
        "node_timings": {},
        "current_step": "start",
        "error": None,
        "should_retry": False,
        "retry_count": 0,
    }

    # Execute the agent graph and time each phase
    start_time = time.perf_counter()
    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        ) from e
    total_duration_ms = (time.perf_counter() - start_time) * 1000

    # Build agent steps from final state with per-node timing
    agent_steps: list[AgentStepOutput] = []
    node_timings: dict[str, float] = final_state.get("node_timings", {})

    plan = final_state.get("plan")
    if plan is not None:
        agent_steps.append(AgentStepOutput(
            agent_name="orchestrator",
            output=plan.model_dump(mode="json"),
            duration_ms=node_timings.get("orchestrator", 0.0),
        ))

    execution_result = final_state.get("execution_result")
    if execution_result is not None:
        agent_steps.append(AgentStepOutput(
            agent_name="execution",
            output=execution_result.model_dump(mode="json"),
            duration_ms=node_timings.get("execution", 0.0),
        ))

    verification_result = final_state.get("verification_result")
    if verification_result is not None:
        agent_steps.append(AgentStepOutput(
            agent_name="verification",
            output=verification_result.model_dump(mode="json"),
            duration_ms=node_timings.get("verification", 0.0),
        ))

    formatted_response = final_state.get("formatted_response")
    if formatted_response is not None:
        agent_steps.append(AgentStepOutput(
            agent_name="response",
            output=formatted_response.model_dump(mode="json"),
            duration_ms=node_timings.get("response", 0.0),
        ))

    # Determine result and success
    result_value = None
    success = False
    if execution_result is not None:
        result_value = execution_result.final_value
        success = execution_result.success

    # Store the log
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    log_item: dict[str, Any] = {
        "pk": pair_id,
        "sk": f"OP#{now.isoformat()}#{log_id}",
        "log_id": log_id,
        "pair_id": pair_id,
        "operation": request.operation,
        "agent_steps": [step.model_dump(mode="json") for step in agent_steps],
        "result": result_value,
        "success": success,
        "total_duration_ms": total_duration_ms,
        "created_at": now.isoformat(),
    }
    await logs_db.put_item(log_item)

    return OperationLogResponse(
        log_id=log_id,
        pair_id=pair_id,
        operation=request.operation,
        agent_steps=agent_steps,
        result=result_value,
        success=success,
        created_at=now,
    )


@router.get(
    "/{pair_id}/logs",
    response_model=list[OperationLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get operation logs for a pair",
    description="Returns all operation logs for a specific pair. Verifies pair ownership first.",
)
async def get_pair_logs(
    pair_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    pairs_db: DynamoDBClient = Depends(get_pairs_db_client),
    logs_db: DynamoDBClient = Depends(get_logs_db_client),
) -> list[OperationLogResponse]:
    """Get all operation logs for a pair.

    1. Verify the pair exists and belongs to the current user
    2. Query the logs table with pk=pair_id
    3. Return all logs sorted by timestamp (newest first)
    """
    user_email = current_user["pk"]

    # Verify pair ownership
    pair = await pairs_db.get_item(pk=user_email, sk=pair_id)
    if pair is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pair not found",
        )

    # Query logs for this pair
    items = await logs_db.query(pk=pair_id)

    logs = [
        OperationLogResponse(
            log_id=item["log_id"],
            pair_id=item["pair_id"],
            operation=item["operation"],
            agent_steps=[
                AgentStepOutput(**step) for step in item["agent_steps"]
            ],
            result=item.get("result"),
            success=item["success"],
            created_at=item["created_at"],
        )
        for item in items
    ]

    # Return newest first (sk is OP#{timestamp}#{uuid}, so reverse sort)
    logs.reverse()

    return logs
