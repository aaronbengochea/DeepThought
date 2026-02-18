"""Pydantic models for gamification stats."""

from pydantic import BaseModel, Field


class DailyCount(BaseModel):
    """A single day's count for rolling stats."""

    date: str = Field(..., description="Date string (YYYY-MM-DD)")
    count: int = Field(..., description="Count for that day")


class StatsResponse(BaseModel):
    """Response model for feature stats with rolling daily counts."""

    total: int = Field(..., description="Total count across all time")
    daily_counts: list[DailyCount] = Field(
        ..., description="Rolling 10-day daily counts"
    )
