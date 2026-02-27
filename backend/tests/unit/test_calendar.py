"""Unit tests for calendar endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from deepthought.api.routes.calendar import (
    create_event,
    delete_event,
    get_event,
    list_events,
    update_event,
)
from deepthought.models.calendar import CalendarEventCreate, CalendarEventUpdate


MOCK_USER = {"pk": "test@example.com", "first_name": "Test", "last_name": "User"}

NOW_ISO = "2026-02-20T10:00:00+00:00"
END_ISO = "2026-02-20T11:00:00+00:00"
CREATED_ISO = "2026-02-15T08:00:00+00:00"


def _make_db_event(
    event_id: str = "evt-1",
    title: str = "Team standup",
    start: str = NOW_ISO,
    end: str = END_ISO,
    rrule: str | None = None,
    description: str | None = None,
) -> dict:
    item = {
        "pk": "test@example.com",
        "sk": f"{start}#{event_id}",
        "event_id": event_id,
        "title": title,
        "start_time": start,
        "end_time": end,
        "created_at": CREATED_ISO,
        "updated_at": CREATED_ISO,
    }
    if rrule:
        item["rrule"] = rrule
    if description:
        item["description"] = description
    return item


class TestCreateEvent:
    """Tests for POST /calendar endpoint."""

    async def test_creates_event_successfully(self):
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = CalendarEventCreate(
            title="Meeting",
            start_time=datetime.fromisoformat(NOW_ISO),
            end_time=datetime.fromisoformat(END_ISO),
        )
        result = await create_event(
            request=request, current_user=MOCK_USER, calendar_db=mock_db
        )

        assert result.title == "Meeting"
        assert result.event_id is not None
        assert result.start_time == datetime.fromisoformat(NOW_ISO)
        assert result.end_time == datetime.fromisoformat(END_ISO)
        mock_db.put_item.assert_called_once()

    async def test_stores_correct_sk_format(self):
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = CalendarEventCreate(
            title="Meeting",
            start_time=datetime.fromisoformat(NOW_ISO),
            end_time=datetime.fromisoformat(END_ISO),
        )
        result = await create_event(
            request=request, current_user=MOCK_USER, calendar_db=mock_db
        )

        stored = mock_db.put_item.call_args[0][0]
        assert stored["sk"] == f"{NOW_ISO}#{result.event_id}"
        assert stored["pk"] == "test@example.com"

    async def test_includes_optional_fields(self):
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = CalendarEventCreate(
            title="Recurring",
            start_time=datetime.fromisoformat(NOW_ISO),
            end_time=datetime.fromisoformat(END_ISO),
            description="Weekly sync",
            rrule="FREQ=WEEKLY;BYDAY=MO",
        )
        result = await create_event(
            request=request, current_user=MOCK_USER, calendar_db=mock_db
        )

        assert result.description == "Weekly sync"
        assert result.rrule == "FREQ=WEEKLY;BYDAY=MO"
        stored = mock_db.put_item.call_args[0][0]
        assert stored["description"] == "Weekly sync"
        assert stored["rrule"] == "FREQ=WEEKLY;BYDAY=MO"


class TestListEvents:
    """Tests for GET /calendar endpoint."""

    async def test_returns_empty_list_when_no_events(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        result = await list_events(
            start=datetime.fromisoformat("2026-02-01T00:00:00+00:00"),
            end=datetime.fromisoformat("2026-02-28T23:59:59+00:00"),
            current_user=MOCK_USER,
            calendar_db=mock_db,
        )
        assert result == []

    async def test_includes_events_in_range(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[_make_db_event()])

        result = await list_events(
            start=datetime.fromisoformat("2026-02-01T00:00:00+00:00"),
            end=datetime.fromisoformat("2026-02-28T23:59:59+00:00"),
            current_user=MOCK_USER,
            calendar_db=mock_db,
        )
        assert len(result) == 1
        assert result[0].title == "Team standup"

    async def test_excludes_events_outside_range(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[_make_db_event()])

        result = await list_events(
            start=datetime.fromisoformat("2026-03-01T00:00:00+00:00"),
            end=datetime.fromisoformat("2026-03-31T23:59:59+00:00"),
            current_user=MOCK_USER,
            calendar_db=mock_db,
        )
        assert len(result) == 0

    async def test_expands_recurring_events(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(
            return_value=[
                _make_db_event(
                    start="2026-02-02T09:00:00+00:00",
                    end="2026-02-02T10:00:00+00:00",
                    rrule="FREQ=DAILY;COUNT=5",
                )
            ]
        )

        result = await list_events(
            start=datetime.fromisoformat("2026-02-01T00:00:00+00:00"),
            end=datetime.fromisoformat("2026-02-28T23:59:59+00:00"),
            current_user=MOCK_USER,
            calendar_db=mock_db,
        )
        assert len(result) == 5

    async def test_results_sorted_by_start_time(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(
            return_value=[
                _make_db_event(event_id="late", start="2026-02-20T15:00:00+00:00",
                               end="2026-02-20T16:00:00+00:00"),
                _make_db_event(event_id="early", start="2026-02-20T08:00:00+00:00",
                               end="2026-02-20T09:00:00+00:00"),
            ]
        )

        result = await list_events(
            start=datetime.fromisoformat("2026-02-01T00:00:00+00:00"),
            end=datetime.fromisoformat("2026-02-28T23:59:59+00:00"),
            current_user=MOCK_USER,
            calendar_db=mock_db,
        )
        assert result[0].event_id == "early"
        assert result[1].event_id == "late"


class TestGetEvent:
    """Tests for GET /calendar/{event_id} endpoint."""

    async def test_returns_event_by_id(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[_make_db_event(event_id="evt-42")])

        result = await get_event(
            event_id="evt-42", current_user=MOCK_USER, calendar_db=mock_db
        )
        assert result.event_id == "evt-42"
        assert result.title == "Team standup"

    async def test_raises_404_when_not_found(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        with pytest.raises(Exception) as exc_info:
            await get_event(
                event_id="nonexistent", current_user=MOCK_USER, calendar_db=mock_db
            )
        assert exc_info.value.status_code == 404


class TestUpdateEvent:
    """Tests for PATCH /calendar/{event_id} endpoint."""

    async def test_updates_title_without_start_change(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[_make_db_event(event_id="evt-1")])
        mock_db.update_item = AsyncMock(return_value={})

        request = CalendarEventUpdate(title="Renamed standup")
        result = await update_event(
            event_id="evt-1", request=request,
            current_user=MOCK_USER, calendar_db=mock_db,
        )

        assert result.title == "Renamed standup"
        mock_db.update_item.assert_called_once()
        mock_db.delete_item.assert_not_called()

    async def test_recreates_item_when_start_time_changes(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[_make_db_event(event_id="evt-1")])
        mock_db.delete_item = AsyncMock(return_value=None)
        mock_db.put_item = AsyncMock(return_value=None)

        new_start = datetime.fromisoformat("2026-02-21T14:00:00+00:00")
        request = CalendarEventUpdate(start_time=new_start)
        result = await update_event(
            event_id="evt-1", request=request,
            current_user=MOCK_USER, calendar_db=mock_db,
        )

        assert result.start_time == new_start
        mock_db.delete_item.assert_called_once()
        mock_db.put_item.assert_called_once()
        new_item = mock_db.put_item.call_args[0][0]
        assert new_item["sk"].startswith("2026-02-21")

    async def test_raises_404_when_event_not_found(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        request = CalendarEventUpdate(title="New title")
        with pytest.raises(Exception) as exc_info:
            await update_event(
                event_id="missing", request=request,
                current_user=MOCK_USER, calendar_db=mock_db,
            )
        assert exc_info.value.status_code == 404


class TestDeleteEvent:
    """Tests for DELETE /calendar/{event_id} endpoint."""

    async def test_deletes_event_successfully(self):
        event = _make_db_event(event_id="evt-1")
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[event])
        mock_db.delete_item = AsyncMock(return_value=None)

        await delete_event(
            event_id="evt-1", current_user=MOCK_USER, calendar_db=mock_db
        )

        mock_db.delete_item.assert_called_once_with(
            pk="test@example.com", sk=event["sk"]
        )

    async def test_raises_404_when_event_not_found(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        with pytest.raises(Exception) as exc_info:
            await delete_event(
                event_id="missing", current_user=MOCK_USER, calendar_db=mock_db
            )
        assert exc_info.value.status_code == 404
