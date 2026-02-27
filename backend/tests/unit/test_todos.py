"""Unit tests for todo endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from deepthought.api.routes.todos import (
    add_item,
    create_list,
    delete_item,
    delete_list,
    list_items,
    list_lists,
    update_item,
)
from deepthought.models.todos import TodoItemCreate, TodoItemUpdate, TodoListCreate


MOCK_USER = {"pk": "test@example.com", "first_name": "Test", "last_name": "User"}

CREATED_ISO = "2026-02-15T08:00:00+00:00"


def _make_db_list(list_id: str = "list-1", title: str = "Groceries") -> dict:
    return {
        "pk": "test@example.com",
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
    completed_at: str | None = None,
    sort_order: int = 0,
) -> dict:
    item = {
        "pk": "test@example.com",
        "sk": f"ITEM#{list_id}#{item_id}",
        "item_id": item_id,
        "list_id": list_id,
        "text": text,
        "completed": completed,
        "sort_order": sort_order,
        "created_at": CREATED_ISO,
        "updated_at": CREATED_ISO,
    }
    if completed_at:
        item["completed_at"] = completed_at
    return item


class TestCreateList:
    """Tests for POST /todos/lists endpoint."""

    async def test_creates_list_successfully(self):
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = TodoListCreate(title="Groceries")
        result = await create_list(
            request=request, current_user=MOCK_USER, todos_db=mock_db
        )

        assert result.title == "Groceries"
        assert result.list_id is not None
        assert result.item_count == 0
        assert result.completed_count == 0
        mock_db.put_item.assert_called_once()

    async def test_stores_correct_sk_format(self):
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = TodoListCreate(title="Work")
        result = await create_list(
            request=request, current_user=MOCK_USER, todos_db=mock_db
        )

        stored = mock_db.put_item.call_args[0][0]
        assert stored["sk"] == f"LIST#{result.list_id}"
        assert stored["pk"] == "test@example.com"


class TestListLists:
    """Tests for GET /todos/lists endpoint."""

    async def test_returns_empty_list_when_no_lists(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        result = await list_lists(current_user=MOCK_USER, todos_db=mock_db)
        assert result == []

    async def test_returns_lists_with_counts(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(
            side_effect=[
                [_make_db_list("list-1", "Groceries")],
                [
                    _make_db_item("list-1", "i1", completed=False),
                    _make_db_item("list-1", "i2", completed=True, completed_at=CREATED_ISO),
                    _make_db_item("list-1", "i3", completed=False),
                ],
            ]
        )

        result = await list_lists(current_user=MOCK_USER, todos_db=mock_db)

        assert len(result) == 1
        assert result[0].title == "Groceries"
        assert result[0].item_count == 3
        assert result[0].completed_count == 1

    async def test_multiple_lists_have_independent_counts(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(
            side_effect=[
                [_make_db_list("a"), _make_db_list("b", "Work")],
                [
                    _make_db_item("a", "i1", completed=True, completed_at=CREATED_ISO),
                    _make_db_item("b", "i2", completed=False),
                    _make_db_item("b", "i3", completed=True, completed_at=CREATED_ISO),
                ],
            ]
        )

        result = await list_lists(current_user=MOCK_USER, todos_db=mock_db)

        list_a = next(r for r in result if r.list_id == "a")
        list_b = next(r for r in result if r.list_id == "b")
        assert list_a.item_count == 1
        assert list_a.completed_count == 1
        assert list_b.item_count == 2
        assert list_b.completed_count == 1


class TestDeleteList:
    """Tests for DELETE /todos/lists/{list_id} endpoint."""

    async def test_deletes_list_and_items(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(
            return_value=[
                _make_db_item("list-1", "i1"),
                _make_db_item("list-1", "i2"),
            ]
        )
        mock_db.batch_delete = AsyncMock(return_value=None)

        await delete_list(list_id="list-1", current_user=MOCK_USER, todos_db=mock_db)

        call_args = mock_db.batch_delete.call_args[0][0]
        assert len(call_args) == 3  # 1 list + 2 items
        assert ("test@example.com", "LIST#list-1") in call_args

    async def test_deletes_list_with_no_items(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(return_value=[])
        mock_db.batch_delete = AsyncMock(return_value=None)

        await delete_list(list_id="list-1", current_user=MOCK_USER, todos_db=mock_db)

        call_args = mock_db.batch_delete.call_args[0][0]
        assert len(call_args) == 1

    async def test_raises_404_when_list_not_found(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        with pytest.raises(Exception) as exc_info:
            await delete_list(
                list_id="missing", current_user=MOCK_USER, todos_db=mock_db
            )
        assert exc_info.value.status_code == 404


class TestAddItem:
    """Tests for POST /todos/lists/{list_id}/items endpoint."""

    async def test_adds_item_successfully(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(return_value=[_make_db_item()])
        mock_db.put_item = AsyncMock(return_value=None)

        request = TodoItemCreate(text="Buy eggs")
        result = await add_item(
            list_id="list-1", request=request,
            current_user=MOCK_USER, todos_db=mock_db,
        )

        assert result.text == "Buy eggs"
        assert result.list_id == "list-1"
        assert result.completed is False
        assert result.sort_order == 1  # one existing item

    async def test_first_item_gets_sort_order_zero(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(return_value=[])
        mock_db.put_item = AsyncMock(return_value=None)

        request = TodoItemCreate(text="First task")
        result = await add_item(
            list_id="list-1", request=request,
            current_user=MOCK_USER, todos_db=mock_db,
        )

        assert result.sort_order == 0

    async def test_raises_404_when_list_not_found(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        request = TodoItemCreate(text="Orphan item")
        with pytest.raises(Exception) as exc_info:
            await add_item(
                list_id="missing", request=request,
                current_user=MOCK_USER, todos_db=mock_db,
            )
        assert exc_info.value.status_code == 404


class TestListItems:
    """Tests for GET /todos/lists/{list_id}/items endpoint."""

    async def test_returns_items_sorted_by_sort_order(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(
            return_value=[
                _make_db_item("list-1", "i2", "Second", sort_order=1),
                _make_db_item("list-1", "i1", "First", sort_order=0),
            ]
        )

        result = await list_items(
            list_id="list-1", current_user=MOCK_USER, todos_db=mock_db
        )

        assert len(result) == 2
        assert result[0].text == "First"
        assert result[1].text == "Second"

    async def test_returns_empty_list_for_list_with_no_items(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_list("list-1"))
        mock_db.query = AsyncMock(return_value=[])

        result = await list_items(
            list_id="list-1", current_user=MOCK_USER, todos_db=mock_db
        )
        assert result == []

    async def test_raises_404_when_list_not_found(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        with pytest.raises(Exception) as exc_info:
            await list_items(
                list_id="missing", current_user=MOCK_USER, todos_db=mock_db
            )
        assert exc_info.value.status_code == 404


class TestUpdateItem:
    """Tests for PATCH /todos/lists/{list_id}/items/{item_id} endpoint."""

    async def test_updates_text(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_item())
        mock_db.update_item = AsyncMock(return_value={})

        request = TodoItemUpdate(text="Buy almond milk")
        result = await update_item(
            list_id="list-1", item_id="item-1", request=request,
            current_user=MOCK_USER, todos_db=mock_db,
        )

        assert result.text == "Buy almond milk"
        assert result.completed is False

    async def test_marks_item_completed_sets_completed_at(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=_make_db_item(completed=False))
        mock_db.update_item = AsyncMock(return_value={})

        request = TodoItemUpdate(completed=True)
        result = await update_item(
            list_id="list-1", item_id="item-1", request=request,
            current_user=MOCK_USER, todos_db=mock_db,
        )

        assert result.completed is True
        assert result.completed_at is not None
        updates = mock_db.update_item.call_args[1]["updates"]
        assert updates["completed"] is True
        assert updates["completed_at"] is not None

    async def test_uncompleting_item_clears_completed_at(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(
            return_value=_make_db_item(completed=True, completed_at=CREATED_ISO)
        )
        mock_db.update_item = AsyncMock(return_value={})

        request = TodoItemUpdate(completed=False)
        result = await update_item(
            list_id="list-1", item_id="item-1", request=request,
            current_user=MOCK_USER, todos_db=mock_db,
        )

        assert result.completed is False
        assert result.completed_at is None
        updates = mock_db.update_item.call_args[1]["updates"]
        assert updates["completed_at"] is None

    async def test_raises_404_when_item_not_found(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        request = TodoItemUpdate(text="Updated")
        with pytest.raises(Exception) as exc_info:
            await update_item(
                list_id="list-1", item_id="missing", request=request,
                current_user=MOCK_USER, todos_db=mock_db,
            )
        assert exc_info.value.status_code == 404


class TestDeleteItem:
    """Tests for DELETE /todos/lists/{list_id}/items/{item_id} endpoint."""

    async def test_deletes_item_successfully(self):
        item = _make_db_item()
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=item)
        mock_db.delete_item = AsyncMock(return_value=None)

        await delete_item(
            list_id="list-1", item_id="item-1",
            current_user=MOCK_USER, todos_db=mock_db,
        )

        mock_db.delete_item.assert_called_once_with(
            pk="test@example.com", sk="ITEM#list-1#item-1"
        )

    async def test_raises_404_when_item_not_found(self):
        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        with pytest.raises(Exception) as exc_info:
            await delete_item(
                list_id="list-1", item_id="missing",
                current_user=MOCK_USER, todos_db=mock_db,
            )
        assert exc_info.value.status_code == 404
