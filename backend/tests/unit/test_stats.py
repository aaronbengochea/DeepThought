"""Unit tests for stats endpoints and computation logic."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from deepthought.api.routes.stats import _build_daily_counts, pairs_stats, todos_stats


MOCK_USER = {"pk": "test@example.com", "first_name": "Test", "last_name": "User"}


class TestBuildDailyCounts:
    """Tests for the _build_daily_counts helper."""

    def test_returns_correct_number_of_days(self):
        result = _build_daily_counts([], last_n_days=10)
        assert len(result) == 10

    def test_zero_fills_empty_days(self):
        result = _build_daily_counts([], last_n_days=5)
        assert all(dc.count == 0 for dc in result)

    @patch("deepthought.api.routes.stats.datetime")
    def test_counts_dates_correctly(self, mock_dt):
        today = datetime(2026, 2, 26, tzinfo=timezone.utc).date()
        mock_dt.now.return_value = datetime(2026, 2, 26, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        dates = ["2026-02-26", "2026-02-26", "2026-02-25"]
        result = _build_daily_counts(dates, last_n_days=3)

        assert result[0].date == "2026-02-24"
        assert result[0].count == 0
        assert result[1].date == "2026-02-25"
        assert result[1].count == 1
        assert result[2].date == "2026-02-26"
        assert result[2].count == 2

    def test_ordered_oldest_to_newest(self):
        result = _build_daily_counts([], last_n_days=3)
        dates = [dc.date for dc in result]
        assert dates == sorted(dates)

    def test_ignores_dates_outside_window(self):
        today = datetime.now(timezone.utc).date()
        old_date = str(today - timedelta(days=30))
        result = _build_daily_counts([old_date], last_n_days=10)
        assert all(dc.count == 0 for dc in result)


class TestPairsStats:
    """Tests for GET /stats/pairs endpoint."""

    async def test_returns_total_and_daily_counts(self):
        today = datetime.now(timezone.utc)
        mock_db = MagicMock()
        mock_db.query = AsyncMock(
            return_value=[
                {"created_at": today.isoformat()},
                {"created_at": today.isoformat()},
                {"created_at": (today - timedelta(days=1)).isoformat()},
            ]
        )

        result = await pairs_stats(current_user=MOCK_USER, pairs_db=mock_db)

        assert result.total == 3
        assert len(result.daily_counts) == 10
        mock_db.query.assert_called_once_with(pk="test@example.com")

    async def test_returns_zero_total_with_no_pairs(self):
        mock_db = MagicMock()
        mock_db.query = AsyncMock(return_value=[])

        result = await pairs_stats(current_user=MOCK_USER, pairs_db=mock_db)

        assert result.total == 0
        assert len(result.daily_counts) == 10
        assert all(dc.count == 0 for dc in result.daily_counts)


class TestTodosStats:
    """Tests for GET /stats/todos endpoint."""

    async def test_returns_total_lists_and_completion_counts(self):
        today = datetime.now(timezone.utc)
        mock_db = MagicMock()
        mock_db.query_count = AsyncMock(return_value=5)
        mock_db.query_gsi_range = AsyncMock(
            return_value=[
                {"completed_at": today.isoformat()},
                {"completed_at": (today - timedelta(days=1)).isoformat()},
            ]
        )

        result = await todos_stats(current_user=MOCK_USER, todos_db=mock_db)

        assert result.total == 5
        assert len(result.daily_counts) == 10
        mock_db.query_count.assert_called_once_with(
            pk="test@example.com", sk_prefix="LIST#"
        )

    async def test_uses_correct_gsi_parameters(self):
        mock_db = MagicMock()
        mock_db.query_count = AsyncMock(return_value=0)
        mock_db.query_gsi_range = AsyncMock(return_value=[])

        await todos_stats(current_user=MOCK_USER, todos_db=mock_db)

        call_kwargs = mock_db.query_gsi_range.call_args[1]
        assert call_kwargs["index_name"] == "pk_completed_at_index"
        assert call_kwargs["pk_attr"] == "pk"
        assert call_kwargs["pk_value"] == "test@example.com"
        assert call_kwargs["sk_attr"] == "completed_at"

    async def test_returns_zero_with_no_lists_or_completions(self):
        mock_db = MagicMock()
        mock_db.query_count = AsyncMock(return_value=0)
        mock_db.query_gsi_range = AsyncMock(return_value=[])

        result = await todos_stats(current_user=MOCK_USER, todos_db=mock_db)

        assert result.total == 0
        assert all(dc.count == 0 for dc in result.daily_counts)
