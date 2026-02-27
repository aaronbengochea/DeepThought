"""Gamification stats endpoints for pairs and todos."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_pairs_db_client, get_todos_db_client
from deepthought.db import DynamoDBClient
from deepthought.models.stats import DailyCount, StatsResponse

router = APIRouter()


def _build_daily_counts(dates: list[str], last_n_days: int = 10) -> list[DailyCount]:
    """Aggregate a list of YYYY-MM-DD date strings into rolling daily counts.

    Returns one DailyCount per day for the last N days (including today),
    with zero-filled days that have no entries.
    """
    today = datetime.now(timezone.utc).date()
    counts: dict[str, int] = defaultdict(int)
    for d in dates:
        counts[d] += 1

    return [
        DailyCount(
            date=str(today - timedelta(days=i)),
            count=counts.get(str(today - timedelta(days=i)), 0),
        )
        for i in range(last_n_days - 1, -1, -1)
    ]


@router.get(
    "/pairs",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Pairs stats",
    description="Returns total pair count and 10-day rolling daily insertion counts.",
)
async def pairs_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    pairs_db: DynamoDBClient = Depends(get_pairs_db_client),
) -> StatsResponse:
    """Get pairs stats: total count + 10-day rolling daily insertions.

    1. Query all pairs for the user
    2. Extract created_at dates
    3. Aggregate into daily counts for the last 10 days
    """
    user_email = current_user["pk"]
    pairs = await pairs_db.query(pk=user_email)

    dates = [datetime.fromisoformat(p["created_at"]).date().isoformat() for p in pairs]

    return StatsResponse(
        total=len(pairs),
        daily_counts=_build_daily_counts(dates),
    )


@router.get(
    "/todos",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Todos stats",
    description="Returns total todo list count and 10-day rolling daily completed task counts.",
)
async def todos_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    todos_db: DynamoDBClient = Depends(get_todos_db_client),
) -> StatsResponse:
    """Get todos stats: total list count + 10-day rolling daily completions.

    1. Count total lists via query_count with sk_prefix=LIST#
    2. Query the completed_at GSI for items completed in the last 10 days
    3. Aggregate completed_at dates into daily counts
    """
    user_email = current_user["pk"]

    total_lists = await todos_db.query_count(pk=user_email, sk_prefix="LIST#")

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=9)
    sk_start = f"{start_date.isoformat()}T00:00:00+00:00"
    sk_end = f"{today.isoformat()}T23:59:59+00:00"

    completed_items = await todos_db.query_gsi_range(
        index_name="pk_completed_at_index",
        pk_attr="pk",
        pk_value=user_email,
        sk_attr="completed_at",
        sk_start=sk_start,
        sk_end=sk_end,
    )

    dates = [
        datetime.fromisoformat(item["completed_at"]).date().isoformat() for item in completed_items
    ]

    return StatsResponse(
        total=total_lists,
        daily_counts=_build_daily_counts(dates),
    )
