"""Pydantic models for DynamoDB items."""

from pydantic import BaseModel, Field


class DynamoDBItem(BaseModel):
    """Base model for DynamoDB items."""

    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")

    model_config = {"extra": "allow"}
