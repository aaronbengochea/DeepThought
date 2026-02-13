"""Pydantic models for number pairs."""

from datetime import datetime

from pydantic import BaseModel, Field


class Pair(BaseModel):
    """Full pair model as stored in DynamoDB."""

    pair_id: str = Field(..., description="Unique pair identifier")
    user_email: str = Field(..., description="Owner's email address")
    val1: int | float = Field(..., description="First value")
    val2: int | float = Field(..., description="Second value")
    created_at: datetime = Field(..., description="Pair creation timestamp")


class PairCreate(BaseModel):
    """Request model for creating a number pair."""

    val1: int | float = Field(..., description="First value")
    val2: int | float = Field(..., description="Second value")


class PairResponse(BaseModel):
    """Response model for pair data."""

    pair_id: str = Field(..., description="Unique pair identifier")
    val1: int | float = Field(..., description="First value")
    val2: int | float = Field(..., description="Second value")
    created_at: datetime = Field(..., description="Pair creation timestamp")
