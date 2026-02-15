"""Unit tests for pair endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deepthought.api.routes.pairs import create_pair, get_pair_logs, list_pairs, operate_on_pair
from deepthought.models.logs import OperateRequest
from deepthought.models.pairs import PairCreate


MOCK_USER = {"pk": "test@example.com", "first_name": "Test", "last_name": "User"}


class TestCreatePair:
    """Tests for POST /pairs endpoint."""

    async def test_creates_pair_successfully(self):
        """Test that a pair is created and returned."""
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = PairCreate(val1=10, val2=20)
        result = await create_pair(
            request=request,
            current_user=MOCK_USER,
            pairs_db=mock_db,
        )

        assert result.val1 == 10
        assert result.val2 == 20
        assert result.pair_id is not None
        assert result.created_at is not None
        mock_db.put_item.assert_called_once()

    async def test_stores_correct_item_in_db(self):
        """Test that the correct item structure is stored in DynamoDB."""
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = PairCreate(val1=42, val2=58)
        result = await create_pair(
            request=request,
            current_user=MOCK_USER,
            pairs_db=mock_db,
        )

        stored_item = mock_db.put_item.call_args[0][0]
        assert stored_item["pk"] == "test@example.com"
        assert stored_item["sk"] == result.pair_id
        assert stored_item["val1"] == 42
        assert stored_item["val2"] == 58
        assert "created_at" in stored_item

    async def test_creates_pair_with_float_values(self):
        """Test that float values are accepted."""
        mock_db = MagicMock()
        mock_db.put_item = AsyncMock(return_value=None)

        request = PairCreate(val1=3.14, val2=2.71)
        result = await create_pair(
            request=request,
            current_user=MOCK_USER,
            pairs_db=mock_db,
        )

        assert result.val1 == 3.14
        assert result.val2 == 2.71


class TestListPairs:
    """Tests for GET /pairs endpoint."""

    async def test_returns_empty_list_when_no_pairs(self):
        """Test that an empty list is returned when user has no pairs."""
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        result = await list_pairs(current_user=MOCK_USER, pairs_db=mock_db)

        assert result == []
        mock_db.query.assert_called_once_with(pk="test@example.com")

    async def test_returns_pairs_for_user(self):
        """Test that pairs are returned correctly."""
        now = datetime.now(timezone.utc).isoformat()
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[
            {"sk": "pair-id-1", "val1": 10, "val2": 20, "created_at": now},
            {"sk": "pair-id-2", "val1": 30, "val2": 40, "created_at": now},
        ])

        result = await list_pairs(current_user=MOCK_USER, pairs_db=mock_db)

        assert len(result) == 2
        assert result[0].pair_id == "pair-id-1"
        assert result[0].val1 == 10
        assert result[1].pair_id == "pair-id-2"
        assert result[1].val1 == 30


class TestOperateOnPair:
    """Tests for POST /pairs/{pair_id}/operate endpoint."""

    async def test_pair_not_found_returns_404(self):
        """Test that a 404 is returned when the pair doesn't exist."""
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value=None)
        mock_logs_db = MagicMock()
        mock_graph = MagicMock()

        with pytest.raises(Exception) as exc_info:
            await operate_on_pair(
                pair_id="nonexistent-id",
                request=OperateRequest(operation="add"),
                current_user=MOCK_USER,
                pairs_db=mock_pairs_db,
                logs_db=mock_logs_db,
                graph=mock_graph,
            )
        assert exc_info.value.status_code == 404

    async def test_successful_operation_stores_log(self):
        """Test that a successful operation stores a log entry."""
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "test@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 5,
        })

        mock_logs_db = MagicMock()
        mock_logs_db.put_item = AsyncMock(return_value=None)

        # Mock the graph to return a minimal final state
        mock_execution_result = MagicMock()
        mock_execution_result.final_value = 15
        mock_execution_result.success = True
        mock_execution_result.model_dump = MagicMock(return_value={"final_value": 15})

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "plan": None,
            "execution_result": mock_execution_result,
            "verification_result": None,
            "formatted_response": None,
            "node_timings": {"execution": 5.0},
        })

        result = await operate_on_pair(
            pair_id="pair-123",
            request=OperateRequest(operation="add"),
            current_user=MOCK_USER,
            pairs_db=mock_pairs_db,
            logs_db=mock_logs_db,
            graph=mock_graph,
        )

        assert result.pair_id == "pair-123"
        assert result.operation == "add"
        assert result.result == 15
        assert result.success is True
        mock_logs_db.put_item.assert_called_once()

    async def test_graph_failure_returns_500(self):
        """Test that a graph execution failure returns 500."""
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "test@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 0,
        })

        mock_logs_db = MagicMock()
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        with pytest.raises(Exception) as exc_info:
            await operate_on_pair(
                pair_id="pair-123",
                request=OperateRequest(operation="divide"),
                current_user=MOCK_USER,
                pairs_db=mock_pairs_db,
                logs_db=mock_logs_db,
                graph=mock_graph,
            )
        assert exc_info.value.status_code == 500


class TestGetPairLogs:
    """Tests for GET /pairs/{pair_id}/logs endpoint."""

    async def test_pair_not_found_returns_404(self):
        """Test that a 404 is returned when the pair doesn't exist."""
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value=None)
        mock_logs_db = MagicMock()

        with pytest.raises(Exception) as exc_info:
            await get_pair_logs(
                pair_id="nonexistent-id",
                current_user=MOCK_USER,
                pairs_db=mock_pairs_db,
                logs_db=mock_logs_db,
            )
        assert exc_info.value.status_code == 404

    async def test_returns_empty_list_when_no_logs(self):
        """Test that an empty list is returned when no logs exist."""
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "test@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 20,
        })

        mock_logs_db = MagicMock()
        mock_logs_db.query = AsyncMock(return_value=[])

        result = await get_pair_logs(
            pair_id="pair-123",
            current_user=MOCK_USER,
            pairs_db=mock_pairs_db,
            logs_db=mock_logs_db,
        )

        assert result == []

    async def test_returns_logs_for_pair(self):
        """Test that logs are returned and reversed (newest first)."""
        now = datetime.now(timezone.utc).isoformat()
        mock_pairs_db = MagicMock()
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "test@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 20,
        })

        mock_logs_db = MagicMock()
        mock_logs_db.query = AsyncMock(return_value=[
            {
                "log_id": "log-1",
                "pair_id": "pair-123",
                "operation": "add",
                "agent_steps": [],
                "result": 30,
                "success": True,
                "created_at": now,
            },
            {
                "log_id": "log-2",
                "pair_id": "pair-123",
                "operation": "multiply",
                "agent_steps": [],
                "result": 200,
                "success": True,
                "created_at": now,
            },
        ])

        result = await get_pair_logs(
            pair_id="pair-123",
            current_user=MOCK_USER,
            pairs_db=mock_pairs_db,
            logs_db=mock_logs_db,
        )

        assert len(result) == 2
        # Reversed: log-2 should be first (newest)
        assert result[0].log_id == "log-2"
        assert result[1].log_id == "log-1"
