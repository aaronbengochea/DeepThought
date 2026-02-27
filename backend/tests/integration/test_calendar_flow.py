"""Integration tests for the calendar API flow through HTTP.

Tests the complete request/response pipeline including middleware,
serialization, JWT auth headers, and dependency injection overrides.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from deepthought.api.app import create_app
from deepthought.api.auth import create_access_token
from deepthought.api.dependencies import (
    get_calendar_db_client,
    get_users_db_client,
)


MOCK_USER_ITEM = {
    "pk": "user@example.com",
    "first_name": "Test",
    "last_name": "User",
}

NOW_ISO = "2026-02-20T10:00:00+00:00"
END_ISO = "2026-02-20T11:00:00+00:00"
CREATED_ISO = "2026-02-15T08:00:00+00:00"


def _make_db_event(event_id: str = "evt-1", **overrides: str) -> dict:
    item = {
        "pk": "user@example.com",
        "sk": f"{overrides.get('start_time', NOW_ISO)}#{event_id}",
        "event_id": event_id,
        "title": overrides.get("title", "Team standup"),
        "start_time": overrides.get("start_time", NOW_ISO),
        "end_time": overrides.get("end_time", END_ISO),
        "created_at": CREATED_ISO,
        "updated_at": CREATED_ISO,
    }
    if "description" in overrides:
        item["description"] = overrides["description"]
    if "rrule" in overrides:
        item["rrule"] = overrides["rrule"]
    return item


@pytest.fixture
def mock_users_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=MOCK_USER_ITEM)
    return mock


@pytest.fixture
def mock_calendar_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=None)
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    mock.update_item = AsyncMock(return_value={})
    mock.delete_item = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def app(mock_users_db, mock_calendar_db):
    application = create_app()
    application.dependency_overrides[get_users_db_client] = lambda: mock_users_db
    application.dependency_overrides[get_calendar_db_client] = lambda: mock_calendar_db
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def make_auth_header(email: str = "user@example.com") -> dict[str, str]:
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Create event
# ---------------------------------------------------------------------------


class TestCreateEventFlow:
    """Tests for POST /api/v1/calendar."""

    def test_create_event_success(self, client, mock_calendar_db):
        resp = client.post(
            "/api/v1/calendar/",
            json={
                "title": "Lunch meeting",
                "start_time": NOW_ISO,
                "end_time": END_ISO,
            },
            headers=make_auth_header(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Lunch meeting"
        assert "event_id" in body
        assert "created_at" in body
        mock_calendar_db.put_item.assert_called_once()

    def test_create_event_with_optional_fields(self, client, mock_calendar_db):
        resp = client.post(
            "/api/v1/calendar/",
            json={
                "title": "Weekly sync",
                "start_time": NOW_ISO,
                "end_time": END_ISO,
                "description": "Team sync",
                "rrule": "FREQ=WEEKLY;BYDAY=MO",
            },
            headers=make_auth_header(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["description"] == "Team sync"
        assert body["rrule"] == "FREQ=WEEKLY;BYDAY=MO"

    def test_create_event_without_auth_returns_401(self, client):
        resp = client.post(
            "/api/v1/calendar/",
            json={"title": "Test", "start_time": NOW_ISO, "end_time": END_ISO},
        )
        assert resp.status_code == 401

    def test_create_event_missing_fields_returns_422(self, client):
        resp = client.post(
            "/api/v1/calendar/",
            json={"title": "No dates"},
            headers=make_auth_header(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List events
# ---------------------------------------------------------------------------


class TestListEventsFlow:
    """Tests for GET /api/v1/calendar."""

    def test_list_events_empty(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[])

        resp = client.get(
            "/api/v1/calendar/",
            params={"start": "2026-02-01T00:00:00+00:00", "end": "2026-02-28T23:59:59+00:00"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_events_returns_matching(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[_make_db_event()])

        resp = client.get(
            "/api/v1/calendar/",
            params={"start": "2026-02-01T00:00:00+00:00", "end": "2026-02-28T23:59:59+00:00"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["title"] == "Team standup"

    def test_list_events_without_auth_returns_401(self, client):
        resp = client.get(
            "/api/v1/calendar/",
            params={"start": "2026-02-01T00:00:00+00:00", "end": "2026-02-28T23:59:59+00:00"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get event
# ---------------------------------------------------------------------------


class TestGetEventFlow:
    """Tests for GET /api/v1/calendar/{event_id}."""

    def test_get_event_success(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[_make_db_event("evt-42")])

        resp = client.get(
            "/api/v1/calendar/evt-42",
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        assert resp.json()["event_id"] == "evt-42"

    def test_get_event_not_found_returns_404(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[])

        resp = client.get(
            "/api/v1/calendar/nonexistent",
            headers=make_auth_header(),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update event
# ---------------------------------------------------------------------------


class TestUpdateEventFlow:
    """Tests for PATCH /api/v1/calendar/{event_id}."""

    def test_update_event_title(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[_make_db_event("evt-1")])

        resp = client.patch(
            "/api/v1/calendar/evt-1",
            json={"title": "Renamed"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"
        mock_calendar_db.update_item.assert_called_once()

    def test_update_event_start_time_recreates(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[_make_db_event("evt-1")])

        resp = client.patch(
            "/api/v1/calendar/evt-1",
            json={"start_time": "2026-02-21T14:00:00+00:00"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        mock_calendar_db.delete_item.assert_called_once()
        assert mock_calendar_db.put_item.call_count == 1

    def test_update_nonexistent_returns_404(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[])

        resp = client.patch(
            "/api/v1/calendar/missing",
            json={"title": "Nope"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete event
# ---------------------------------------------------------------------------


class TestDeleteEventFlow:
    """Tests for DELETE /api/v1/calendar/{event_id}."""

    def test_delete_event_success(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[_make_db_event("evt-1")])

        resp = client.delete(
            "/api/v1/calendar/evt-1",
            headers=make_auth_header(),
        )

        assert resp.status_code == 204
        mock_calendar_db.delete_item.assert_called_once()

    def test_delete_nonexistent_returns_404(self, client, mock_calendar_db):
        mock_calendar_db.query = AsyncMock(return_value=[])

        resp = client.delete(
            "/api/v1/calendar/missing",
            headers=make_auth_header(),
        )

        assert resp.status_code == 404

    def test_delete_without_auth_returns_401(self, client):
        resp = client.delete("/api/v1/calendar/evt-1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Full CRUD flow
# ---------------------------------------------------------------------------


class TestCalendarEndToEndFlow:
    """Tests the full create → get → update → delete flow."""

    def test_full_crud_lifecycle(self, client, mock_calendar_db):
        # 1. Create
        create_resp = client.post(
            "/api/v1/calendar/",
            json={"title": "Sprint planning", "start_time": NOW_ISO, "end_time": END_ISO},
            headers=make_auth_header(),
        )
        assert create_resp.status_code == 201
        event_id = create_resp.json()["event_id"]

        # 2. Get
        event_item = _make_db_event(event_id, title="Sprint planning")
        mock_calendar_db.query = AsyncMock(return_value=[event_item])

        get_resp = client.get(
            f"/api/v1/calendar/{event_id}",
            headers=make_auth_header(),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Sprint planning"

        # 3. Update
        update_resp = client.patch(
            f"/api/v1/calendar/{event_id}",
            json={"title": "Sprint retro"},
            headers=make_auth_header(),
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Sprint retro"

        # 4. Delete
        delete_resp = client.delete(
            f"/api/v1/calendar/{event_id}",
            headers=make_auth_header(),
        )
        assert delete_resp.status_code == 204
