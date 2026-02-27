"""Todo list and item management endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_todos_db_client
from deepthought.db import DynamoDBClient
from collections import defaultdict

from deepthought.models.todos import (
    TodoItemCreate,
    TodoItemResponse,
    TodoItemUpdate,
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
        "Returns all todo lists for the authenticated user with item and completed counts per list."
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


@router.delete(
    "/lists/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo list",
    description="Deletes a todo list and all its items for the authenticated user.",
)
async def delete_list(
    list_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> None:
    """Delete a todo list and all its items.

    1. Verify the list exists (404 if not)
    2. Query all ITEM#{list_id}# entries for the list
    3. Batch delete the list entry + all item entries
    """
    user_email = current_user["pk"]

    list_sk = f"LIST#{list_id}"
    existing = await todos_db.get_item(pk=user_email, sk=list_sk)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo list not found",
        )

    items = await todos_db.query(pk=user_email, sk_prefix=f"ITEM#{list_id}#")

    to_delete: list[tuple[str, str]] = [(user_email, list_sk)]
    to_delete.extend((user_email, item["sk"]) for item in items)

    await todos_db.batch_delete(to_delete)


@router.post(
    "/lists/{list_id}/items",
    response_model=TodoItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a todo item",
    description="Adds a new item to an existing todo list.",
)
async def add_item(
    list_id: str,
    request: TodoItemCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> TodoItemResponse:
    """Add a new item to a todo list.

    1. Verify the parent list exists (404 if not)
    2. Count existing items to determine sort_order
    3. Store with pk=user_email, sk=ITEM#{list_id}#{item_id}
    4. Return the created item
    """
    user_email = current_user["pk"]

    existing = await todos_db.get_item(pk=user_email, sk=f"LIST#{list_id}")
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo list not found",
        )

    existing_items = await todos_db.query(pk=user_email, sk_prefix=f"ITEM#{list_id}#")
    sort_order = len(existing_items)

    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    item: dict[str, Any] = {
        "pk": user_email,
        "sk": f"ITEM#{list_id}#{item_id}",
        "item_id": item_id,
        "list_id": list_id,
        "text": request.text,
        "completed": False,
        "sort_order": sort_order,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await todos_db.put_item(item)

    return TodoItemResponse(
        item_id=item_id,
        list_id=list_id,
        text=request.text,
        completed=False,
        completed_at=None,
        sort_order=sort_order,
        created_at=now,
        updated_at=now,
    )


def _item_to_response(item: dict[str, Any]) -> TodoItemResponse:
    """Map a raw DynamoDB item to a TodoItemResponse."""
    completed_at_raw = item.get("completed_at")
    return TodoItemResponse(
        item_id=item["item_id"],
        list_id=item["list_id"],
        text=item["text"],
        completed=item.get("completed", False),
        completed_at=datetime.fromisoformat(completed_at_raw) if completed_at_raw else None,
        sort_order=item.get("sort_order", 0),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
    )


@router.get(
    "/lists/{list_id}/items",
    response_model=list[TodoItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List items in a todo list",
    description="Returns all items for a specific todo list, sorted by sort_order.",
)
async def list_items(
    list_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> list[TodoItemResponse]:
    """List all items for a todo list.

    1. Verify the parent list exists (404 if not)
    2. Query all ITEM#{list_id}# entries
    3. Return items sorted by sort_order ascending
    """
    user_email = current_user["pk"]

    existing = await todos_db.get_item(pk=user_email, sk=f"LIST#{list_id}")
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo list not found",
        )

    items = await todos_db.query(pk=user_email, sk_prefix=f"ITEM#{list_id}#")
    results = [_item_to_response(item) for item in items]
    results.sort(key=lambda r: r.sort_order)
    return results


@router.patch(
    "/lists/{list_id}/items/{item_id}",
    response_model=TodoItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a todo item",
    description=(
        "Partially updates a todo item. Supports changing text and toggling "
        "completion status. When completed transitions to true, completed_at is "
        "set automatically; when toggled back to false, completed_at is cleared."
    ),
)
async def update_item(
    list_id: str,
    item_id: str,
    request: TodoItemUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> TodoItemResponse:
    """Update a todo item.

    1. Find the item by sk=ITEM#{list_id}#{item_id} (404 if not found)
    2. Build update dict from non-None request fields
    3. Handle completed toggle: set/clear completed_at accordingly
    4. Apply partial update via update_item
    """
    user_email = current_user["pk"]
    item_sk = f"ITEM#{list_id}#{item_id}"

    existing = await todos_db.get_item(pk=user_email, sk=item_sk)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo item not found",
        )

    now = datetime.now(timezone.utc)
    updates: dict[str, Any] = {"updated_at": now.isoformat()}

    if request.text is not None:
        updates["text"] = request.text

    if request.completed is not None:
        updates["completed"] = request.completed
        if request.completed and not existing.get("completed"):
            updates["completed_at"] = now.isoformat()
        elif not request.completed and existing.get("completed"):
            updates["completed_at"] = None

    await todos_db.update_item(pk=user_email, sk=item_sk, updates=updates)

    return TodoItemResponse(
        item_id=item_id,
        list_id=list_id,
        text=request.text if request.text is not None else existing["text"],
        completed=request.completed
        if request.completed is not None
        else existing.get("completed", False),
        completed_at=(
            datetime.fromisoformat(updates["completed_at"])
            if "completed_at" in updates and updates["completed_at"] is not None
            else (
                datetime.fromisoformat(existing["completed_at"])
                if existing.get("completed_at")
                else None
            )
        ),
        sort_order=existing.get("sort_order", 0),
        created_at=datetime.fromisoformat(existing["created_at"]),
        updated_at=now,
    )


@router.delete(
    "/lists/{list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo item",
    description="Deletes a single item from a todo list.",
)
async def delete_item(
    list_id: str,
    item_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> None:
    """Delete a single todo item.

    1. Verify the item exists (404 if not)
    2. Delete by composite key (pk=user_email, sk=ITEM#{list_id}#{item_id})
    """
    user_email = current_user["pk"]
    item_sk = f"ITEM#{list_id}#{item_id}"

    existing = await todos_db.get_item(pk=user_email, sk=item_sk)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo item not found",
        )

    await todos_db.delete_item(pk=user_email, sk=item_sk)
