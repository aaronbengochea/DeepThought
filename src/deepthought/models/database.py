"""Pydantic models for DynamoDB items."""

from pydantic import BaseModel, Field


class DynamoDBItem(BaseModel):
    """Base model for DynamoDB items."""

    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")

    model_config = {"extra": "allow"}


class CalculationItem(DynamoDBItem):
    """Item storing calculation data."""

    pk: str = Field(..., pattern=r"^CALC#.+$")  # e.g., CALC#user123
    sk: str = Field(..., pattern=r"^ITEM#.+$")  # e.g., ITEM#calc001
    val1: int | float
    val2: int | float
    description: str | None = None
    created_at: str
