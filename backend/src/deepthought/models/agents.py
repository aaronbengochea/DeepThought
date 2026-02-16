"""Pydantic models for agent state and communication."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlanStepType(str, Enum):
    """Types of steps the orchestrator can create."""

    QUERY_DATABASE = "query_database"
    EXECUTE_FUNCTION = "execute_function"
    VERIFY_RESULT = "verify_result"
    FORMAT_RESPONSE = "format_response"


class PlanStep(BaseModel):
    """A single step in the orchestrator's plan."""

    step_number: int = Field(..., ge=1)
    step_type: PlanStepType
    description: str
    parameters: dict[str, Any]
    depends_on: list[int] = Field(default_factory=list)


class Plan(BaseModel):
    """The orchestrator agent's comprehensive plan."""

    plan_id: str
    created_at: datetime
    task_description: str
    steps: list[PlanStep]
    expected_outcome: str


class ToolCallResult(BaseModel):
    """Result of a single tool call."""

    tool_name: str
    input_params: dict[str, Any]
    output: Any
    success: bool
    error_message: str | None = None
    execution_time_ms: float


class ExecutionResult(BaseModel):
    """Result from the execution agent."""

    plan_id: str
    executed_steps: list[int]
    tool_results: list[ToolCallResult]
    final_value: Any
    success: bool
    error_details: str | None = None


class VerificationStatus(str, Enum):
    """Status of verification."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VerificationCheck(BaseModel):
    """A single verification check."""

    check_name: str
    expected_value: Any
    actual_value: Any
    status: VerificationStatus
    message: str


class VerificationResult(BaseModel):
    """Result from the verification agent."""

    plan_id: str
    checks: list[VerificationCheck]
    overall_status: VerificationStatus
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class FormattedResponse(BaseModel):
    """The response agent's formatted output."""

    success: bool
    data: dict[str, Any]
    metadata: dict[str, Any]
    message: str
