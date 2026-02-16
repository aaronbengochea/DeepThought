"""Pydantic models for operation logs and telemetry."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentStepOutput(BaseModel):
    """Output from a single agent step in the pipeline."""

    agent_name: str = Field(..., description="Name of the agent node")
    output: dict[str, Any] = Field(..., description="Agent step output data")
    duration_ms: float = Field(..., description="Step execution duration in milliseconds")


class OperationLog(BaseModel):
    """Full operation log as stored in DynamoDB."""

    log_id: str = Field(..., description="Unique log identifier")
    pair_id: str = Field(..., description="Associated pair identifier")
    operation: str = Field(..., description="Operation performed (add, subtract, multiply, divide)")
    agent_steps: list[AgentStepOutput] = Field(..., description="Ordered list of agent step outputs")
    result: float | int | None = Field(None, description="Operation result")
    success: bool = Field(..., description="Whether the operation completed successfully")
    created_at: datetime = Field(..., description="Log creation timestamp")


class OperateRequest(BaseModel):
    """Request model for executing an operation on a pair."""

    operation: str = Field(..., description="Operation to perform (add, subtract, multiply, divide)")


class OperationLogResponse(BaseModel):
    """Response model for operation log data."""

    log_id: str = Field(..., description="Unique log identifier")
    pair_id: str = Field(..., description="Associated pair identifier")
    operation: str = Field(..., description="Operation performed")
    agent_steps: list[AgentStepOutput] = Field(..., description="Ordered list of agent step outputs")
    result: float | int | None = Field(None, description="Operation result")
    success: bool = Field(..., description="Whether the operation completed successfully")
    created_at: datetime = Field(..., description="Log creation timestamp")
