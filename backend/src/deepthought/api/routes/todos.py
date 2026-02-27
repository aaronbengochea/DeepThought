"""Todo list and item management endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_todos_db_client
from deepthought.db import DynamoDBClient
from collections import defaultdict

from deepthought.models.todos import (
    TodoListCreate,
    TodoListResponse,
)

router = APIRouter()


@router.post(
    "/lists",
    response_model=TodoListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a todo list",
    description="Creates a new todo list for the authenticated user.",
)
async def create_list(
    request: TodoListCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> TodoListResponse:
    """Create a new todo list.

    1. Generate a unique list_id
    2. Store in DynamoDB with pk=user_email, sk=LIST#{list_id}
    3. Return the created list with zero item counts
    """
    user_email = current_user["pk"]
    list_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    item: dict[str, Any] = {
        "pk": user_email,
        "sk": f"LIST#{list_id}",
        "list_id": list_id,
        "title": request.title,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await todos_db.put_item(item)

    return TodoListResponse(
        list_id=list_id,
        title=request.title,
        item_count=0,
        completed_count=0,
        created_at=now,
        updated_at=now,
    )


@router.get(
    "/lists",
    response_model=list[TodoListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all todo lists",
    description=(
        "Returns all todo lists for the authenticated user with item and "
        "completed counts per list."
    ),
)
async def list_lists(
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> list[TodoListResponse]:
    """List all todo lists with item/completed counts.

    1. Query all LIST# entries for the user
    2. Query all ITEM# entries for the user
    3. Aggregate item counts and completed counts per list_id
    4. Return lists sorted by created_at ascending
    """
    user_email = current_user["pk"]

    lists = await todos_db.query(pk=user_email, sk_prefix="LIST#")
    items = await todos_db.query(pk=user_email, sk_prefix="ITEM#")

    item_counts: dict[str, int] = defaultdict(int)
    completed_counts: dict[str, int] = defaultdict(int)
    for item in items:
        lid = item["list_id"]
        item_counts[lid] += 1
        if item.get("completed"):
            completed_counts[lid] += 1

    results = [
        TodoListResponse(
            list_id=lst["list_id"],
            title=lst["title"],
            item_count=item_counts.get(lst["list_id"], 0),
            completed_count=completed_counts.get(lst["list_id"], 0),
            created_at=datetime.fromisoformat(lst["created_at"]),
            updated_at=datetime.fromisoformat(lst["updated_at"]),
        )
        for lst in lists
    ]

    results.sort(key=lambda r: r.created_at)
    return results
