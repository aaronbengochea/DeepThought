"""Unit tests for agent nodes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from deepthought.agents.nodes.orchestrator import orchestrator_node
from deepthought.agents.nodes.execution import execution_node
from deepthought.agents.nodes.verification import verification_node
from deepthought.agents.nodes.response import response_node
from deepthought.agents.state import AgentState
from deepthought.models.agents import (
    ExecutionResult,
    Plan,
    PlanStep,
    PlanStepType,
    ToolCallResult,
    VerificationCheck,
    VerificationResult,
    VerificationStatus,
)


def create_base_state(**overrides) -> AgentState:
    """Create a base state for testing with optional overrides."""
    state: AgentState = {
        "request_id": "test-request-123",
        "task_description": "Calculate sum of values",
        "input_params": {"partition_key": "CALC#test", "sort_key": "ITEM#001"},
        "plan": None,
        "execution_result": None,
        "verification_result": None,
        "formatted_response": None,
        "messages": [],
        "current_step": "init",
        "error": None,
        "should_retry": False,
        "retry_count": 0,
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


class TestOrchestratorNode:
    """Tests for orchestrator_node."""

    @pytest.mark.asyncio
    async def test_creates_plan(self):
        """Test orchestrator creates a plan."""
        state = create_base_state()

        result = await orchestrator_node(state)

        assert "plan" in result
        assert result["plan"] is not None
        assert isinstance(result["plan"], Plan)

    @pytest.mark.asyncio
    async def test_plan_has_correct_steps(self):
        """Test plan contains expected step types."""
        state = create_base_state()

        result = await orchestrator_node(state)
        plan = result["plan"]

        step_types = [step.step_type for step in plan.steps]
        assert PlanStepType.QUERY_DATABASE in step_types
        assert PlanStepType.EXECUTE_FUNCTION in step_types
        assert PlanStepType.VERIFY_RESULT in step_types
        assert PlanStepType.FORMAT_RESPONSE in step_types

    @pytest.mark.asyncio
    async def test_plan_uses_input_params(self):
        """Test plan uses partition and sort keys from input."""
        state = create_base_state(
            input_params={"partition_key": "CALC#custom", "sort_key": "ITEM#999"}
        )

        result = await orchestrator_node(state)
        plan = result["plan"]

        # Find the query step
        query_step = next(
            s for s in plan.steps if s.step_type == PlanStepType.QUERY_DATABASE
        )
        assert query_step.parameters["pk"] == "CALC#custom"
        assert query_step.parameters["sk"] == "ITEM#999"

    @pytest.mark.asyncio
    async def test_sets_current_step(self):
        """Test orchestrator sets current_step correctly."""
        state = create_base_state()

        result = await orchestrator_node(state)

        assert result["current_step"] == "orchestrator_complete"

    @pytest.mark.asyncio
    async def test_adds_message(self):
        """Test orchestrator adds a message."""
        state = create_base_state()

        result = await orchestrator_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_plan_id_matches_request_id(self):
        """Test plan_id is set to request_id."""
        state = create_base_state(request_id="unique-request-456")

        result = await orchestrator_node(state)

        assert result["plan"].plan_id == "unique-request-456"


class TestExecutionNode:
    """Tests for execution_node."""

    @pytest.mark.asyncio
    async def test_returns_error_when_no_plan(self):
        """Test execution returns error when plan is missing."""
        state = create_base_state(plan=None)

        result = await execution_node(state)

        assert result["error"] == "No plan available for execution"
        assert result["current_step"] == "execution_failed"

    @pytest.mark.asyncio
    @patch("deepthought.agents.nodes.execution.query_dynamodb")
    @patch("deepthought.agents.nodes.execution.add_values")
    async def test_successful_execution(self, mock_add, mock_query):
        """Test successful execution with mocked tools."""
        # Setup mocks
        mock_query.ainvoke = AsyncMock(
            return_value={"pk": "CALC#test", "sk": "ITEM#001", "val1": 42, "val2": 58}
        )
        mock_add.invoke.return_value = 100

        # Create state with plan
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[
                PlanStep(
                    step_number=1,
                    step_type=PlanStepType.QUERY_DATABASE,
                    description="Query",
                    parameters={"pk": "CALC#test", "sk": "ITEM#001"},
                ),
                PlanStep(
                    step_number=2,
                    step_type=PlanStepType.EXECUTE_FUNCTION,
                    description="Add",
                    parameters={"function": "add_values"},
                    depends_on=[1],
                ),
            ],
            expected_outcome="Sum",
        )
        state = create_base_state(plan=plan)

        result = await execution_node(state)

        assert result["execution_result"] is not None
        assert result["execution_result"].success is True
        assert result["execution_result"].final_value == 100
        assert result["current_step"] == "execution_complete"

    @pytest.mark.asyncio
    @patch("deepthought.agents.nodes.execution.query_dynamodb")
    async def test_handles_query_failure(self, mock_query):
        """Test execution handles database query failure."""
        mock_query.ainvoke = AsyncMock(side_effect=Exception("Database error"))

        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[
                PlanStep(
                    step_number=1,
                    step_type=PlanStepType.QUERY_DATABASE,
                    description="Query",
                    parameters={"pk": "CALC#test", "sk": "ITEM#001"},
                ),
            ],
            expected_outcome="Sum",
        )
        state = create_base_state(plan=plan)

        result = await execution_node(state)

        assert result["execution_result"] is not None
        assert result["execution_result"].success is False


class TestVerificationNode:
    """Tests for verification_node."""

    @pytest.mark.asyncio
    async def test_returns_error_when_missing_data(self):
        """Test verification returns error when data is missing."""
        state = create_base_state(plan=None, execution_result=None)

        result = await verification_node(state)

        assert result["error"] == "Missing execution result or plan for verification"
        assert result["current_step"] == "verification_failed"

    @pytest.mark.asyncio
    async def test_successful_verification(self):
        """Test successful verification when calculation is correct."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="query_dynamodb",
                    input_params={"pk": "CALC#test"},
                    output={"pk": "CALC#test", "val1": 42, "val2": 58},
                    success=True,
                    execution_time_ms=10.0,
                ),
                ToolCallResult(
                    tool_name="add_values",
                    input_params={"val1": 42, "val2": 58},
                    output=100,
                    success=True,
                    execution_time_ms=1.0,
                ),
            ],
            final_value=100,
            success=True,
        )
        state = create_base_state(plan=plan, execution_result=execution_result)

        result = await verification_node(state)

        assert result["verification_result"] is not None
        assert result["verification_result"].overall_status == VerificationStatus.PASSED
        assert result["verification_result"].confidence_score == 1.0
        assert result["current_step"] == "verification_complete"

    @pytest.mark.asyncio
    async def test_failed_verification_wrong_result(self):
        """Test verification fails when calculation is incorrect."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="query_dynamodb",
                    input_params={"pk": "CALC#test"},
                    output={"pk": "CALC#test", "val1": 42, "val2": 58},
                    success=True,
                    execution_time_ms=10.0,
                ),
                ToolCallResult(
                    tool_name="add_values",
                    input_params={"val1": 42, "val2": 58},
                    output=99,  # Wrong result!
                    success=True,
                    execution_time_ms=1.0,
                ),
            ],
            final_value=99,
            success=True,
        )
        state = create_base_state(plan=plan, execution_result=execution_result)

        result = await verification_node(state)

        assert result["verification_result"].overall_status == VerificationStatus.FAILED
        assert result["verification_result"].confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_verification_with_missing_tool_results(self):
        """Test verification fails when tool results are missing."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[],
            tool_results=[],  # No results
            final_value=None,
            success=False,
        )
        state = create_base_state(plan=plan, execution_result=execution_result)

        result = await verification_node(state)

        assert result["verification_result"].overall_status == VerificationStatus.FAILED


class TestResponseNode:
    """Tests for response_node."""

    @pytest.mark.asyncio
    async def test_formats_error_response(self):
        """Test response node formats error correctly."""
        state = create_base_state(error="Something went wrong")

        result = await response_node(state)

        assert result["formatted_response"] is not None
        assert result["formatted_response"].success is False
        assert "Something went wrong" in result["formatted_response"].message
        assert result["current_step"] == "complete"

    @pytest.mark.asyncio
    async def test_handles_missing_data(self):
        """Test response node handles missing execution data."""
        state = create_base_state(
            plan=None, execution_result=None, verification_result=None
        )

        result = await response_node(state)

        assert result["formatted_response"].success is False
        assert "missing" in result["formatted_response"].message.lower()

    @pytest.mark.asyncio
    async def test_successful_response(self):
        """Test response node formats successful result."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="query_dynamodb",
                    input_params={"pk": "CALC#test"},
                    output={"pk": "CALC#test", "val1": 42, "val2": 58},
                    success=True,
                    execution_time_ms=10.0,
                ),
                ToolCallResult(
                    tool_name="add_values",
                    input_params={"val1": 42, "val2": 58},
                    output=100,
                    success=True,
                    execution_time_ms=1.0,
                ),
            ],
            final_value=100,
            success=True,
        )
        verification_result = VerificationResult(
            plan_id="test-123",
            checks=[
                VerificationCheck(
                    check_name="addition_correctness",
                    expected_value=100,
                    actual_value=100,
                    status=VerificationStatus.PASSED,
                    message="OK",
                )
            ],
            overall_status=VerificationStatus.PASSED,
            confidence_score=1.0,
            reasoning="All passed",
        )
        state = create_base_state(
            plan=plan,
            execution_result=execution_result,
            verification_result=verification_result,
        )

        result = await response_node(state)

        assert result["formatted_response"].success is True
        assert result["formatted_response"].data["val1"] == 42
        assert result["formatted_response"].data["val2"] == 58
        assert result["formatted_response"].data["result"] == 100
        assert result["formatted_response"].data["verification_status"] == "passed"
        assert result["current_step"] == "complete"

    @pytest.mark.asyncio
    async def test_response_includes_metadata(self):
        """Test response includes metadata."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="query_dynamodb",
                    input_params={},
                    output={"val1": 1, "val2": 2},
                    success=True,
                    execution_time_ms=10.0,
                ),
                ToolCallResult(
                    tool_name="add_values",
                    input_params={},
                    output=3,
                    success=True,
                    execution_time_ms=1.0,
                ),
            ],
            final_value=3,
            success=True,
        )
        verification_result = VerificationResult(
            plan_id="test-123",
            checks=[],
            overall_status=VerificationStatus.PASSED,
            confidence_score=1.0,
            reasoning="OK",
        )
        state = create_base_state(
            request_id="my-request-id",
            plan=plan,
            execution_result=execution_result,
            verification_result=verification_result,
        )

        result = await response_node(state)

        metadata = result["formatted_response"].metadata
        assert metadata["request_id"] == "my-request-id"
        assert metadata["plan_id"] == "test-123"
        assert metadata["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_failed_verification_response(self):
        """Test response with failed verification."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test",
            steps=[],
            expected_outcome="Sum",
        )
        execution_result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="query_dynamodb",
                    input_params={},
                    output={"val1": 1, "val2": 2},
                    success=True,
                    execution_time_ms=10.0,
                ),
                ToolCallResult(
                    tool_name="add_values",
                    input_params={},
                    output=99,  # Wrong
                    success=True,
                    execution_time_ms=1.0,
                ),
            ],
            final_value=99,
            success=True,
        )
        verification_result = VerificationResult(
            plan_id="test-123",
            checks=[],
            overall_status=VerificationStatus.FAILED,
            confidence_score=0.0,
            reasoning="Mismatch",
        )
        state = create_base_state(
            plan=plan,
            execution_result=execution_result,
            verification_result=verification_result,
        )

        result = await response_node(state)

        assert result["formatted_response"].success is False
        assert "verification failures" in result["formatted_response"].message.lower()
