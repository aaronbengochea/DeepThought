"""Pair management and operation endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_pairs_db_client
from deepthought.db import DynamoDBClient
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
