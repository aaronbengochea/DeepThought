"""Pytest configuration and fixtures."""

from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from deepthought.api.app import create_app
from deepthought.models import (
    ExecutionResult,
    FormattedResponse,
    Plan,
    PlanStep,
    PlanStepType,
    ToolCallResult,
    VerificationCheck,
    VerificationResult,
    VerificationStatus,
)


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_plan() -> Plan:
    """Create a sample plan for testing."""
    from datetime import datetime, timezone

    return Plan(
        plan_id="test-plan-123",
        created_at=datetime.now(timezone.utc),
        task_description="Test calculation",
        steps=[
            PlanStep(
                step_number=1,
                step_type=PlanStepType.QUERY_DATABASE,
                description="Query database",
                parameters={"pk": "CALC#test", "sk": "ITEM#001"},
                depends_on=[],
            ),
            PlanStep(
                step_number=2,
                step_type=PlanStepType.EXECUTE_FUNCTION,
                description="Add values",
                parameters={"function": "add_values"},
                depends_on=[1],
            ),
        ],
        expected_outcome="Sum of val1 and val2",
    )


@pytest.fixture
def sample_execution_result() -> ExecutionResult:
    """Create a sample execution result for testing."""
    return ExecutionResult(
        plan_id="test-plan-123",
        executed_steps=[1, 2],
        tool_results=[
            ToolCallResult(
                tool_name="query_dynamodb",
                input_params={"pk": "CALC#test", "sk": "ITEM#001"},
                output={"pk": "CALC#test", "sk": "ITEM#001", "val1": 42, "val2": 58},
                success=True,
                execution_time_ms=10.5,
            ),
            ToolCallResult(
                tool_name="add_values",
                input_params={"val1": 42, "val2": 58},
                output=100,
                success=True,
                execution_time_ms=0.5,
            ),
        ],
        final_value=100,
        success=True,
    )


@pytest.fixture
def sample_verification_result() -> VerificationResult:
    """Create a sample verification result for testing."""
    return VerificationResult(
        plan_id="test-plan-123",
        checks=[
            VerificationCheck(
                check_name="addition_correctness",
                expected_value=100,
                actual_value=100,
                status=VerificationStatus.PASSED,
                message="Expected 100, got 100",
            ),
        ],
        overall_status=VerificationStatus.PASSED,
        confidence_score=1.0,
        reasoning="All checks passed",
    )


@pytest.fixture
def sample_formatted_response() -> FormattedResponse:
    """Create a sample formatted response for testing."""
    return FormattedResponse(
        success=True,
        data={"val1": 42, "val2": 58, "result": 100, "verification_status": "passed"},
        metadata={"request_id": "test-123", "plan_id": "test-plan-123"},
        message="Calculation completed successfully",
    )


@pytest.fixture
def mock_dynamodb_client() -> MagicMock:
    """Create a mock DynamoDB client."""
    mock = MagicMock()
    mock.get_item = AsyncMock(
        return_value={"pk": "CALC#test", "sk": "ITEM#001", "val1": 42, "val2": 58}
    )
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    return mock
