"""Pydantic models for API requests."""

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Request to execute a calculation task."""

    partition_key: str = Field(..., description="Primary key to query DynamoDB")
    sort_key: str = Field(..., description="Sort key for the item")
    operation: str = Field(default="add", description="Operation to perform")
