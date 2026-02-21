"""Calendar event management endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_calendar_db_client
from deepthought.db import DynamoDBClient
from deepthought.models.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)

router = APIRouter()


def _item_to_response(item: dict[str, Any]) -> CalendarEventResponse:
    """Map a raw DynamoDB item to a CalendarEventResponse."""
    return CalendarEventResponse(
        event_id=item["event_id"],
        title=item["title"],
        description=item.get("description"),
        start_time=datetime.fromisoformat(item["start_time"]),
        end_time=datetime.fromisoformat(item["end_time"]),
        rrule=item.get("rrule"),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
    )


async def _find_event(
    calendar_db: DynamoDBClient, user_email: str, event_id: str
) -> dict[str, Any]:
    """Query all events for the user and return the one matching event_id.

    The calendar sk is {start_time}#{event_id}, so a full pk query is required
    to locate an event by event_id alone.

    Raises:
        HTTPException 404: If no event with the given event_id is found.
    """
    items = await calendar_db.query(pk=user_email)
    item = next((i for i in items if i.get("event_id") == event_id), None)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return item


@router.post(
    "/",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a calendar event",
    description="Creates a new calendar event for the authenticated user.",
)
async def create_event(
    request: CalendarEventCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    calendar_db: DynamoDBClient = Depends(get_calendar_db_client),
) -> CalendarEventResponse:
    """Create a new calendar event.

    1. Generate a unique event_id
    2. Store in DynamoDB with pk=user_email, sk={start_time}#{event_id}
    3. Return the created event
    """
    user_email = current_user["pk"]
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sk = f"{request.start_time.isoformat()}#{event_id}"

    item: dict[str, Any] = {
        "pk": user_email,
        "sk": sk,
        "event_id": event_id,
        "title": request.title,
        "start_time": request.start_time.isoformat(),
        "end_time": request.end_time.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    if request.description is not None:
        item["description"] = request.description
    if request.rrule is not None:
        item["rrule"] = request.rrule

    await calendar_db.put_item(item)

    return CalendarEventResponse(
        event_id=event_id,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        rrule=request.rrule,
        created_at=now,
        updated_at=now,
    )
