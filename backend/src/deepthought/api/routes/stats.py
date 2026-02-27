"""Gamification stats endpoints for pairs and todos."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from deepthought.api.auth import get_current_user
from deepthought.api.dependencies import get_pairs_db_client
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
