"""Calendar event management endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any

from dateutil.rrule import rrulestr
from fastapi import APIRouter, Depends, HTTPException, Query, status

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


@router.get(
    "/",
    response_model=list[CalendarEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List calendar events in a date range",
    description=(
        "Returns events within [start, end]. Recurring events are expanded into "
        "individual instances using RRULE. One-off events are included if they overlap "
        "with the range. Results are sorted by start time."
    ),
)
async def list_events(
    start: datetime = Query(..., description="Range start (ISO 8601 with offset)"),
    end: datetime = Query(..., description="Range end (ISO 8601 with offset)"),
    current_user: dict[str, Any] = Depends(get_current_user),
    calendar_db: DynamoDBClient = Depends(get_calendar_db_client),
) -> list[CalendarEventResponse]:
    """List calendar events within a date range, expanding recurring events.

    1. Fetch all events for the user from DynamoDB
    2. For one-off events: include if they overlap with [start, end]
    3. For recurring events: expand RRULE instances within [start, end]
    4. Return all results sorted by start time
    """
    user_email = current_user["pk"]
    items = await calendar_db.query(pk=user_email)

    results: list[CalendarEventResponse] = []

    for item in items:
        event_start = datetime.fromisoformat(item["start_time"])
        event_end = datetime.fromisoformat(item["end_time"])
        rrule_str = item.get("rrule")

        if rrule_str:
            rule = rrulestr(rrule_str, dtstart=event_start)
            duration = event_end - event_start
            for instance in rule.between(start, end, inc=True):
                results.append(
                    CalendarEventResponse(
                        event_id=item["event_id"],
                        title=item["title"],
                        description=item.get("description"),
                        start_time=instance,
                        end_time=instance + duration,
                        rrule=rrule_str,
                        created_at=datetime.fromisoformat(item["created_at"]),
                        updated_at=datetime.fromisoformat(item["updated_at"]),
                    )
                )
        else:
            if event_start <= end and event_end >= start:
                results.append(_item_to_response(item))

    results.sort(key=lambda e: e.start_time)
    return results


@router.get(
    "/{event_id}",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a calendar event",
    description="Returns a single calendar event by ID for the authenticated user.",
)
async def get_event(
    event_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    calendar_db: DynamoDBClient = Depends(get_calendar_db_client),
) -> CalendarEventResponse:
    """Fetch a single calendar event by event_id.

    Queries all events for the user and returns the one matching event_id.
    The sk is {start_time}#{event_id}, so a full pk query is required to locate
    an event by event_id alone.
    """
    user_email = current_user["pk"]
    item = await _find_event(calendar_db, user_email, event_id)
    return _item_to_response(item)


@router.patch(
    "/{event_id}",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a calendar event",
    description=(
        "Partially updates a calendar event. If start_time changes, the item is "
        "recreated with a new sort key (sk is {start_time}#{event_id})."
    ),
)
async def update_event(
    event_id: str,
    request: CalendarEventUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    calendar_db: DynamoDBClient = Depends(get_calendar_db_client),
) -> CalendarEventResponse:
    """Partially update a calendar event.

    1. Find the event by event_id
    2. If start_time changes: delete old item, insert new one (sk is time-based)
    3. Otherwise: update_item with only the changed fields
    """
    user_email = current_user["pk"]
    item = await _find_event(calendar_db, user_email, event_id)

    old_sk: str = item["sk"]
    now = datetime.now(timezone.utc)

    new_title = request.title if request.title is not None else item["title"]
    new_description = request.description if request.description is not None else item.get("description")
    new_start = request.start_time if request.start_time is not None else datetime.fromisoformat(item["start_time"])
    new_end = request.end_time if request.end_time is not None else datetime.fromisoformat(item["end_time"])
    new_rrule = request.rrule if request.rrule is not None else item.get("rrule")

    start_time_changed = (
        request.start_time is not None
        and request.start_time.isoformat() != item["start_time"]
    )

    if start_time_changed:
        new_sk = f"{new_start.isoformat()}#{event_id}"
        new_item: dict[str, Any] = {
            "pk": user_email,
            "sk": new_sk,
            "event_id": event_id,
            "title": new_title,
            "start_time": new_start.isoformat(),
            "end_time": new_end.isoformat(),
            "created_at": item["created_at"],
            "updated_at": now.isoformat(),
        }
        if new_description is not None:
            new_item["description"] = new_description
        if new_rrule is not None:
            new_item["rrule"] = new_rrule
        await calendar_db.delete_item(pk=user_email, sk=old_sk)
        await calendar_db.put_item(new_item)
    else:
        updates: dict[str, Any] = {"updated_at": now.isoformat()}
        if request.title is not None:
            updates["title"] = new_title
        if request.description is not None:
            updates["description"] = new_description
        if request.end_time is not None:
            updates["end_time"] = new_end.isoformat()
        if request.rrule is not None:
            updates["rrule"] = new_rrule
        await calendar_db.update_item(pk=user_email, sk=old_sk, updates=updates)

    return CalendarEventResponse(
        event_id=event_id,
        title=new_title,
        description=new_description,
        start_time=new_start,
        end_time=new_end,
        rrule=new_rrule,
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=now,
    )
