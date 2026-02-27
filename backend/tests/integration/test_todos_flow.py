"""Integration tests for the todos API flow through HTTP.

Tests the complete request/response pipeline including middleware,
serialization, JWT auth headers, and dependency injection overrides.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from deepthought.api.app import create_app
from deepthought.api.auth import create_access_token
from deepthought.api.dependencies import (
    get_todos_db_client,
    get_users_db_client,
)


MOCK_USER_ITEM = {
    "pk": "user@example.com",
    "first_name": "Test",
    "last_name": "User",
}

CREATED_ISO = "2026-02-15T08:00:00+00:00"


def _make_db_list(list_id: str = "list-1", title: str = "Groceries") -> dict:
    return {
        "pk": "user@example.com",
        "sk": f"LIST#{list_id}",
        "list_id": list_id,
        "title": title,
        "created_at": CREATED_ISO,
        "updated_at": CREATED_ISO,
    }


def _make_db_item(
    list_id: str = "list-1",
    item_id: str = "item-1",
    text: str = "Buy milk",
    completed: bool = False,
    sort_order: int = 0,
) -> dict:
    item = {
        "pk": "user@example.com",
        "sk": f"ITEM#{list_id}#{item_id}",
        "item_id": item_id,
        "list_id": list_id,
        "text": text,
        "completed": completed,
        "sort_order": sort_order,
        "created_at": CREATED_ISO,
        "updated_at": CREATED_ISO,
    }
    return item


@pytest.fixture
def mock_users_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=MOCK_USER_ITEM)
    return mock


@pytest.fixture
def mock_todos_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=None)
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    mock.update_item = AsyncMock(return_value={})
    mock.delete_item = AsyncMock(return_value=None)
    mock.batch_delete = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def app(mock_users_db, mock_todos_db):
    application = create_app()
    application.dependency_overrides[get_users_db_client] = lambda: mock_users_db
    application.dependency_overrides[get_todos_db_client] = lambda: mock_todos_db
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def make_auth_header(email: str = "user@example.com") -> dict[str, str]:
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Create list
# ---------------------------------------------------------------------------


class TestCreateListFlow:
    """Tests for POST /api/v1/todos/lists."""

    def test_create_list_success(self, client, mock_todos_db):
        resp = client.post(
            "/api/v1/todos/lists",
            json={"title": "Groceries"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Groceries"
        assert "list_id" in body
        assert body["item_count"] == 0
        assert body["completed_count"] == 0
        mock_todos_db.put_item.assert_called_once()

    def test_create_list_without_auth_returns_401(self, client):
        resp = client.post("/api/v1/todos/lists", json={"title": "Test"})
        assert resp.status_code == 401

    def test_create_list_missing_title_returns_422(self, client):
        resp = client.post(
            "/api/v1/todos/lists",
            json={},
            headers=make_auth_header(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List lists
# ---------------------------------------------------------------------------


class TestListListsFlow:
    """Tests for GET /api/v1/todos/lists."""

    def test_list_lists_empty(self, client, mock_todos_db):
        mock_todos_db.query = AsyncMock(return_value=[])

        resp = client.get("/api/v1/todos/lists", headers=make_auth_header())

        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_lists_with_counts(self, client, mock_todos_db):
        mock_todos_db.query = AsyncMock(
            side_effect=[
                [_make_db_list("list-1")],
                [
                    _make_db_item("list-1", "i1", completed=False),
                    _make_db_item("list-1", "i2", completed=True),
                ],
            ]
        )

        resp = client.get("/api/v1/todos/lists", headers=make_auth_header())

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["item_count"] == 2
        assert body[0]["completed_count"] == 1

    def test_list_lists_without_auth_returns_401(self, client):
        resp = client.get("/api/v1/todos/lists")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete list
# ---------------------------------------------------------------------------


class TestDeleteListFlow:
    """Tests for DELETE /api/v1/todos/lists/{list_id}."""

    def test_delete_list_success(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_todos_db.query = AsyncMock(return_value=[_make_db_item()])

        resp = client.delete(
            "/api/v1/todos/lists/list-1",
            headers=make_auth_header(),
        )

        assert resp.status_code == 204
        mock_todos_db.batch_delete.assert_called_once()

    def test_delete_list_not_found_returns_404(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=None)

        resp = client.delete(
            "/api/v1/todos/lists/missing",
            headers=make_auth_header(),
        )

        assert resp.status_code == 404

    def test_delete_list_without_auth_returns_401(self, client):
        resp = client.delete("/api/v1/todos/lists/list-1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Add item
# ---------------------------------------------------------------------------


class TestAddItemFlow:
    """Tests for POST /api/v1/todos/lists/{list_id}/items."""

    def test_add_item_success(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_todos_db.query = AsyncMock(return_value=[])

        resp = client.post(
            "/api/v1/todos/lists/list-1/items",
            json={"text": "Buy eggs"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["text"] == "Buy eggs"
        assert body["list_id"] == "list-1"
        assert body["completed"] is False
        assert body["sort_order"] == 0

    def test_add_item_to_nonexistent_list_returns_404(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=None)

        resp = client.post(
            "/api/v1/todos/lists/missing/items",
            json={"text": "Orphan"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 404

    def test_add_item_without_auth_returns_401(self, client):
        resp = client.post(
            "/api/v1/todos/lists/list-1/items",
            json={"text": "Nope"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List items
# ---------------------------------------------------------------------------


class TestListItemsFlow:
    """Tests for GET /api/v1/todos/lists/{list_id}/items."""

    def test_list_items_success(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_todos_db.query = AsyncMock(
            return_value=[
                _make_db_item("list-1", "i1", "First", sort_order=0),
                _make_db_item("list-1", "i2", "Second", sort_order=1),
            ]
        )

        resp = client.get(
            "/api/v1/todos/lists/list-1/items",
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["text"] == "First"
        assert body[1]["text"] == "Second"

    def test_list_items_nonexistent_list_returns_404(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=None)

        resp = client.get(
            "/api/v1/todos/lists/missing/items",
            headers=make_auth_header(),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update item
# ---------------------------------------------------------------------------


class TestUpdateItemFlow:
    """Tests for PATCH /api/v1/todos/lists/{list_id}/items/{item_id}."""

    def test_update_item_text(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_item())

        resp = client.patch(
            "/api/v1/todos/lists/list-1/items/item-1",
            json={"text": "Buy almond milk"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        assert resp.json()["text"] == "Buy almond milk"

    def test_complete_item(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_item())

        resp = client.patch(
            "/api/v1/todos/lists/list-1/items/item-1",
            json={"completed": True},
            headers=make_auth_header(),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["completed"] is True
        assert body["completed_at"] is not None

    def test_update_nonexistent_item_returns_404(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=None)

        resp = client.patch(
            "/api/v1/todos/lists/list-1/items/missing",
            json={"text": "Nope"},
            headers=make_auth_header(),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete item
# ---------------------------------------------------------------------------


class TestDeleteItemFlow:
    """Tests for DELETE /api/v1/todos/lists/{list_id}/items/{item_id}."""

    def test_delete_item_success(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_item())

        resp = client.delete(
            "/api/v1/todos/lists/list-1/items/item-1",
            headers=make_auth_header(),
        )

        assert resp.status_code == 204
        mock_todos_db.delete_item.assert_called_once()

    def test_delete_nonexistent_item_returns_404(self, client, mock_todos_db):
        mock_todos_db.get_item = AsyncMock(return_value=None)

        resp = client.delete(
            "/api/v1/todos/lists/list-1/items/missing",
            headers=make_auth_header(),
        )

        assert resp.status_code == 404

    def test_delete_item_without_auth_returns_401(self, client):
        resp = client.delete("/api/v1/todos/lists/list-1/items/item-1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Full CRUD flow
# ---------------------------------------------------------------------------


class TestTodosEndToEndFlow:
    """Tests the full create list → add items → complete → delete flow."""

    def test_full_todo_lifecycle(self, client, mock_todos_db):
        # 1. Create list
        create_resp = client.post(
            "/api/v1/todos/lists",
            json={"title": "Shopping"},
            headers=make_auth_header(),
        )
        assert create_resp.status_code == 201
        list_id = create_resp.json()["list_id"]

        # 2. Add item
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_list(list_id, "Shopping"))
        mock_todos_db.query = AsyncMock(return_value=[])

        item_resp = client.post(
            f"/api/v1/todos/lists/{list_id}/items",
            json={"text": "Bread"},
            headers=make_auth_header(),
        )
        assert item_resp.status_code == 201
        item_id = item_resp.json()["item_id"]

        # 3. Complete item
        mock_todos_db.get_item = AsyncMock(
            return_value=_make_db_item(list_id, item_id, "Bread")
        )

        complete_resp = client.patch(
            f"/api/v1/todos/lists/{list_id}/items/{item_id}",
            json={"completed": True},
            headers=make_auth_header(),
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["completed"] is True

        # 4. Delete item
        delete_item_resp = client.delete(
            f"/api/v1/todos/lists/{list_id}/items/{item_id}",
            headers=make_auth_header(),
        )
        assert delete_item_resp.status_code == 204

        # 5. Delete list
        mock_todos_db.get_item = AsyncMock(return_value=_make_db_list(list_id, "Shopping"))
        mock_todos_db.query = AsyncMock(return_value=[])

        delete_list_resp = client.delete(
            f"/api/v1/todos/lists/{list_id}",
            headers=make_auth_header(),
        )
        assert delete_list_resp.status_code == 204
