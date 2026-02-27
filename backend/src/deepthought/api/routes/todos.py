"""Todo list and item management endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_todos_db_client
from deepthought.db import DynamoDBClient
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
