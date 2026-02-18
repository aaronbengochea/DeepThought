"""Pydantic models and enums for DynamoDB."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ReturnValues(StrEnum):
    """DynamoDB ReturnValues options for write operations."""

    NONE = "NONE"
    ALL_OLD = "ALL_OLD"
    ALL_NEW = "ALL_NEW"
    UPDATED_OLD = "UPDATED_OLD"
    UPDATED_NEW = "UPDATED_NEW"


class DynamoDBItem(BaseModel):
    """Base model for DynamoDB items."""

    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")

    model_config = {"extra": "allow"}
