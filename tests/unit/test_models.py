"""Unit tests for Pydantic models."""

from datetime import datetime, timezone

import pytest

from deepthought.models.agents import (
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
from deepthought.models.database import CalculationItem, DynamoDBItem
from deepthought.models.logs import (
    AgentStepOutput,
    OperateRequest,
    OperationLog,
    OperationLogResponse,
)
from deepthought.models.pairs import Pair, PairCreate, PairResponse
from deepthought.models.requests import TaskRequest
from deepthought.models.responses import HealthResponse, TaskResponse
from deepthought.models.users import AuthResponse, User, UserCreate, UserResponse, UserSignIn


class TestPlanStepType:
    """Tests for PlanStepType enum."""

    def test_query_database_value(self):
        """Test QUERY_DATABASE enum value."""
        assert PlanStepType.QUERY_DATABASE.value == "query_database"

    def test_execute_function_value(self):
        """Test EXECUTE_FUNCTION enum value."""
        assert PlanStepType.EXECUTE_FUNCTION.value == "execute_function"

    def test_verify_result_value(self):
        """Test VERIFY_RESULT enum value."""
        assert PlanStepType.VERIFY_RESULT.value == "verify_result"

    def test_format_response_value(self):
        """Test FORMAT_RESPONSE enum value."""
        assert PlanStepType.FORMAT_RESPONSE.value == "format_response"


class TestPlanStep:
    """Tests for PlanStep model."""

    def test_valid_plan_step(self):
        """Test creating a valid PlanStep."""
        step = PlanStep(
            step_number=1,
            step_type=PlanStepType.QUERY_DATABASE,
            description="Query the database",
            parameters={"pk": "CALC#test", "sk": "ITEM#001"},
        )
        assert step.step_number == 1
        assert step.step_type == PlanStepType.QUERY_DATABASE
        assert step.description == "Query the database"
        assert step.parameters == {"pk": "CALC#test", "sk": "ITEM#001"}
        assert step.depends_on == []

    def test_plan_step_with_dependencies(self):
        """Test PlanStep with dependencies."""
        step = PlanStep(
            step_number=2,
            step_type=PlanStepType.EXECUTE_FUNCTION,
            description="Execute function",
            parameters={},
            depends_on=[1],
        )
        assert step.depends_on == [1]

    def test_step_number_must_be_positive(self):
        """Test step_number must be >= 1."""
        with pytest.raises(ValueError):
            PlanStep(
                step_number=0,
                step_type=PlanStepType.QUERY_DATABASE,
                description="Query",
                parameters={},
            )


class TestPlan:
    """Tests for Plan model."""

    def test_valid_plan(self):
        """Test creating a valid Plan."""
        now = datetime.now(timezone.utc)
        plan = Plan(
            plan_id="test-123",
            created_at=now,
            task_description="Test task",
            steps=[
                PlanStep(
                    step_number=1,
                    step_type=PlanStepType.QUERY_DATABASE,
                    description="Query",
                    parameters={},
                )
            ],
            expected_outcome="Expected result",
        )
        assert plan.plan_id == "test-123"
        assert plan.created_at == now
        assert plan.task_description == "Test task"
        assert len(plan.steps) == 1
        assert plan.expected_outcome == "Expected result"

    def test_plan_with_empty_steps(self):
        """Test Plan can have empty steps list."""
        plan = Plan(
            plan_id="test-123",
            created_at=datetime.now(timezone.utc),
            task_description="Test task",
            steps=[],
            expected_outcome="Expected result",
        )
        assert plan.steps == []


class TestToolCallResult:
    """Tests for ToolCallResult model."""

    def test_successful_tool_call(self):
        """Test successful tool call result."""
        result = ToolCallResult(
            tool_name="add_values",
            input_params={"val1": 10, "val2": 20},
            output=30,
            success=True,
            execution_time_ms=1.5,
        )
        assert result.tool_name == "add_values"
        assert result.input_params == {"val1": 10, "val2": 20}
        assert result.output == 30
        assert result.success is True
        assert result.error_message is None
        assert result.execution_time_ms == 1.5

    def test_failed_tool_call(self):
        """Test failed tool call result."""
        result = ToolCallResult(
            tool_name="query_dynamodb",
            input_params={"pk": "CALC#test"},
            output=None,
            success=False,
            error_message="Item not found",
            execution_time_ms=10.0,
        )
        assert result.success is False
        assert result.error_message == "Item not found"


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_successful_execution(self):
        """Test successful execution result."""
        result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1, 2],
            tool_results=[
                ToolCallResult(
                    tool_name="add_values",
                    input_params={"val1": 10, "val2": 20},
                    output=30,
                    success=True,
                    execution_time_ms=1.0,
                )
            ],
            final_value=30,
            success=True,
        )
        assert result.plan_id == "test-123"
        assert result.success is True
        assert result.final_value == 30
        assert result.error_details is None

    def test_failed_execution(self):
        """Test failed execution result."""
        result = ExecutionResult(
            plan_id="test-123",
            executed_steps=[1],
            tool_results=[],
            final_value=None,
            success=False,
            error_details="Database error",
        )
        assert result.success is False
        assert result.error_details == "Database error"


class TestVerificationStatus:
    """Tests for VerificationStatus enum."""

    def test_passed_value(self):
        """Test PASSED enum value."""
        assert VerificationStatus.PASSED.value == "passed"

    def test_failed_value(self):
        """Test FAILED enum value."""
        assert VerificationStatus.FAILED.value == "failed"

    def test_skipped_value(self):
        """Test SKIPPED enum value."""
        assert VerificationStatus.SKIPPED.value == "skipped"


class TestVerificationCheck:
    """Tests for VerificationCheck model."""

    def test_passed_check(self):
        """Test passed verification check."""
        check = VerificationCheck(
            check_name="addition_correctness",
            expected_value=100,
            actual_value=100,
            status=VerificationStatus.PASSED,
            message="Expected 100, got 100",
        )
        assert check.check_name == "addition_correctness"
        assert check.expected_value == 100
        assert check.actual_value == 100
        assert check.status == VerificationStatus.PASSED

    def test_failed_check(self):
        """Test failed verification check."""
        check = VerificationCheck(
            check_name="addition_correctness",
            expected_value=100,
            actual_value=99,
            status=VerificationStatus.FAILED,
            message="Expected 100, got 99",
        )
        assert check.status == VerificationStatus.FAILED


class TestVerificationResult:
    """Tests for VerificationResult model."""

    def test_valid_verification_result(self):
        """Test valid verification result."""
        result = VerificationResult(
            plan_id="test-123",
            checks=[
                VerificationCheck(
                    check_name="test",
                    expected_value=1,
                    actual_value=1,
                    status=VerificationStatus.PASSED,
                    message="OK",
                )
            ],
            overall_status=VerificationStatus.PASSED,
            confidence_score=1.0,
            reasoning="All checks passed",
        )
        assert result.plan_id == "test-123"
        assert result.overall_status == VerificationStatus.PASSED
        assert result.confidence_score == 1.0

    def test_confidence_score_bounds(self):
        """Test confidence_score must be between 0 and 1."""
        with pytest.raises(ValueError):
            VerificationResult(
                plan_id="test-123",
                checks=[],
                overall_status=VerificationStatus.PASSED,
                confidence_score=1.5,  # Invalid - exceeds 1.0
                reasoning="Test",
            )

        with pytest.raises(ValueError):
            VerificationResult(
                plan_id="test-123",
                checks=[],
                overall_status=VerificationStatus.PASSED,
                confidence_score=-0.1,  # Invalid - below 0.0
                reasoning="Test",
            )


class TestFormattedResponse:
    """Tests for FormattedResponse model."""

    def test_success_response(self):
        """Test successful formatted response."""
        response = FormattedResponse(
            success=True,
            data={"val1": 42, "val2": 58, "result": 100},
            metadata={"request_id": "test-123"},
            message="Calculation completed successfully",
        )
        assert response.success is True
        assert response.data["result"] == 100
        assert response.message == "Calculation completed successfully"

    def test_error_response(self):
        """Test error formatted response."""
        response = FormattedResponse(
            success=False,
            data={},
            metadata={"request_id": "test-123"},
            message="Error occurred",
        )
        assert response.success is False
        assert response.data == {}


class TestDynamoDBItem:
    """Tests for DynamoDBItem model."""

    def test_valid_item(self):
        """Test valid DynamoDB item."""
        item = DynamoDBItem(pk="TEST#123", sk="ITEM#001")
        assert item.pk == "TEST#123"
        assert item.sk == "ITEM#001"

    def test_extra_fields_allowed(self):
        """Test extra fields are allowed."""
        item = DynamoDBItem(pk="TEST#123", sk="ITEM#001", extra_field="value")
        assert item.model_extra.get("extra_field") == "value"


class TestCalculationItem:
    """Tests for CalculationItem model."""

    def test_valid_calculation_item(self):
        """Test valid calculation item."""
        item = CalculationItem(
            pk="CALC#user123",
            sk="ITEM#calc001",
            val1=42,
            val2=58,
            created_at="2024-01-01T00:00:00Z",
        )
        assert item.pk == "CALC#user123"
        assert item.sk == "ITEM#calc001"
        assert item.val1 == 42
        assert item.val2 == 58

    def test_pk_pattern_validation(self):
        """Test pk must match CALC# pattern."""
        with pytest.raises(ValueError):
            CalculationItem(
                pk="INVALID#user123",  # Should start with CALC#
                sk="ITEM#calc001",
                val1=42,
                val2=58,
                created_at="2024-01-01T00:00:00Z",
            )

    def test_sk_pattern_validation(self):
        """Test sk must match ITEM# pattern."""
        with pytest.raises(ValueError):
            CalculationItem(
                pk="CALC#user123",
                sk="INVALID#calc001",  # Should start with ITEM#
                val1=42,
                val2=58,
                created_at="2024-01-01T00:00:00Z",
            )

    def test_optional_description(self):
        """Test description is optional."""
        item = CalculationItem(
            pk="CALC#user123",
            sk="ITEM#calc001",
            val1=42,
            val2=58,
            description="Test calculation",
            created_at="2024-01-01T00:00:00Z",
        )
        assert item.description == "Test calculation"


class TestTaskRequest:
    """Tests for TaskRequest model."""

    def test_valid_task_request(self):
        """Test valid task request."""
        request = TaskRequest(
            partition_key="CALC#test",
            sort_key="ITEM#001",
        )
        assert request.partition_key == "CALC#test"
        assert request.sort_key == "ITEM#001"
        assert request.operation == "add"  # Default value

    def test_custom_operation(self):
        """Test task request with custom operation."""
        request = TaskRequest(
            partition_key="CALC#test",
            sort_key="ITEM#001",
            operation="multiply",
        )
        assert request.operation == "multiply"


class TestTaskResponse:
    """Tests for TaskResponse model."""

    def test_success_response(self):
        """Test successful task response."""
        response = TaskResponse(
            success=True,
            request_id="test-123",
            data={"val1": 42, "val2": 58, "result": 100},
            execution_summary={"steps_executed": 2},
        )
        assert response.success is True
        assert response.request_id == "test-123"
        assert response.errors is None

    def test_error_response(self):
        """Test error task response."""
        response = TaskResponse(
            success=False,
            request_id="test-123",
            data={},
            execution_summary={},
            errors=["Database connection failed"],
        )
        assert response.success is False
        assert response.errors == ["Database connection failed"]


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_valid_health_response(self):
        """Test valid health response."""
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.timestamp == "2024-01-01T00:00:00Z"


# --- User Models ---


class TestUser:
    """Tests for User model."""

    def test_valid_user(self):
        """Test creating a valid user."""
        now = datetime.now(timezone.utc)
        user = User(
            first_name="Test",
            last_name="User",
            password_hash="$2b$12$hashedpassword",
            created_at=now,
        )
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.password_hash == "$2b$12$hashedpassword"
        assert user.created_at == now


class TestUserCreate:
    """Tests for UserCreate model."""

    def test_valid_user_create(self):
        """Test valid user creation request."""
        user = UserCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
        )
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.password == "password123"

    def test_password_min_length(self):
        """Test password must be at least 8 characters."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password="short",
            )

    def test_first_name_min_length(self):
        """Test first_name must be at least 1 character."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                first_name="",
                last_name="User",
                password="password123",
            )

    def test_last_name_min_length(self):
        """Test last_name must be at least 1 character."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                first_name="Test",
                last_name="",
                password="password123",
            )

    def test_invalid_email(self):
        """Test invalid email is rejected."""
        with pytest.raises(ValueError):
            UserCreate(
                email="bad-email",
                first_name="Test",
                last_name="User",
                password="password123",
            )


class TestUserSignIn:
    """Tests for UserSignIn model."""

    def test_valid_sign_in(self):
        """Test valid sign-in request."""
        sign_in = UserSignIn(
            email="test@example.com",
            password="password123",
        )
        assert sign_in.email == "test@example.com"
        assert sign_in.password == "password123"

    def test_invalid_email(self):
        """Test invalid email is rejected."""
        with pytest.raises(ValueError):
            UserSignIn(email="bad-email", password="password123")


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_valid_user_response(self):
        """Test valid user response."""
        now = datetime.now(timezone.utc)
        response = UserResponse(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            created_at=now,
        )
        assert response.email == "test@example.com"
        assert response.first_name == "Test"
        assert response.last_name == "User"
        assert response.created_at == now


class TestAuthResponse:
    """Tests for AuthResponse model."""

    def test_valid_auth_response(self):
        """Test valid auth response."""
        now = datetime.now(timezone.utc)
        response = AuthResponse(
            token="jwt-token-here",
            user=UserResponse(
                email="test@example.com",
                first_name="Test",
                last_name="User",
                created_at=now,
            ),
        )
        assert response.token == "jwt-token-here"
        assert response.user.email == "test@example.com"
        assert response.user.first_name == "Test"


# --- Pair Models ---


class TestPair:
    """Tests for Pair model."""

    def test_valid_pair(self):
        """Test creating a valid pair."""
        now = datetime.now(timezone.utc)
        pair = Pair(
            pair_id="pair-123",
            user_email="test@example.com",
            val1=42,
            val2=58,
            created_at=now,
        )
        assert pair.pair_id == "pair-123"
        assert pair.user_email == "test@example.com"
        assert pair.val1 == 42
        assert pair.val2 == 58
        assert pair.created_at == now

    def test_float_values(self):
        """Test pair with float values."""
        pair = Pair(
            pair_id="pair-123",
            user_email="test@example.com",
            val1=3.14,
            val2=2.71,
            created_at=datetime.now(timezone.utc),
        )
        assert pair.val1 == 3.14
        assert pair.val2 == 2.71


class TestPairCreate:
    """Tests for PairCreate model."""

    def test_valid_pair_create(self):
        """Test valid pair creation request."""
        pair = PairCreate(val1=42, val2=58)
        assert pair.val1 == 42
        assert pair.val2 == 58

    def test_float_values(self):
        """Test pair creation with float values."""
        pair = PairCreate(val1=3.14, val2=2.71)
        assert pair.val1 == 3.14
        assert pair.val2 == 2.71


class TestPairResponse:
    """Tests for PairResponse model."""

    def test_valid_pair_response(self):
        """Test valid pair response."""
        now = datetime.now(timezone.utc)
        response = PairResponse(
            pair_id="pair-123",
            val1=42,
            val2=58,
            created_at=now,
        )
        assert response.pair_id == "pair-123"
        assert response.val1 == 42
        assert response.val2 == 58
        assert response.created_at == now


# --- Log Models ---


class TestAgentStepOutput:
    """Tests for AgentStepOutput model."""

    def test_valid_agent_step(self):
        """Test creating a valid agent step output."""
        step = AgentStepOutput(
            agent_name="orchestrator",
            output={"plan": "test plan"},
            duration_ms=150.5,
        )
        assert step.agent_name == "orchestrator"
        assert step.output == {"plan": "test plan"}
        assert step.duration_ms == 150.5


class TestOperationLog:
    """Tests for OperationLog model."""

    def test_valid_operation_log(self):
        """Test creating a valid operation log."""
        now = datetime.now(timezone.utc)
        log = OperationLog(
            log_id="log-123",
            pair_id="pair-123",
            operation="add",
            agent_steps=[
                AgentStepOutput(
                    agent_name="orchestrator",
                    output={"plan": "test"},
                    duration_ms=100.0,
                ),
                AgentStepOutput(
                    agent_name="execution",
                    output={"result": 100},
                    duration_ms=50.0,
                ),
            ],
            result=100,
            success=True,
            created_at=now,
        )
        assert log.log_id == "log-123"
        assert log.pair_id == "pair-123"
        assert log.operation == "add"
        assert len(log.agent_steps) == 2
        assert log.result == 100
        assert log.success is True

    def test_failed_operation_log(self):
        """Test operation log for a failed operation."""
        log = OperationLog(
            log_id="log-456",
            pair_id="pair-123",
            operation="divide",
            agent_steps=[],
            result=None,
            success=False,
            created_at=datetime.now(timezone.utc),
        )
        assert log.success is False
        assert log.result is None


class TestOperateRequest:
    """Tests for OperateRequest model."""

    def test_valid_operate_request(self):
        """Test valid operate request."""
        request = OperateRequest(operation="add")
        assert request.operation == "add"

    def test_subtract_operation(self):
        """Test subtract operation request."""
        request = OperateRequest(operation="subtract")
        assert request.operation == "subtract"


class TestOperationLogResponse:
    """Tests for OperationLogResponse model."""

    def test_valid_operation_log_response(self):
        """Test valid operation log response."""
        now = datetime.now(timezone.utc)
        response = OperationLogResponse(
            log_id="log-123",
            pair_id="pair-123",
            operation="multiply",
            agent_steps=[
                AgentStepOutput(
                    agent_name="orchestrator",
                    output={"plan": "test"},
                    duration_ms=100.0,
                ),
            ],
            result=2436,
            success=True,
            created_at=now,
        )
        assert response.log_id == "log-123"
        assert response.operation == "multiply"
        assert response.result == 2436
        assert response.success is True
