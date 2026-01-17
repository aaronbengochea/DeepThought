"""Pydantic models for API responses."""

from typing import Any

from pydantic import BaseModel


class TaskResponse(BaseModel):
    """Standard API response for task execution."""

    success: bool
    request_id: str
    data: dict[str, Any]
    execution_summary: dict[str, Any]
    errors: list[str] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str
