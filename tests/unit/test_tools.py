"""Unit tests for all tools."""

import pytest

from deepthought.tools.math_ops import (
    AddValuesInput,
    MultiplyValuesInput,
    DivideValuesInput,
    add_values,
    multiply_values,
    divide_values,
)
from deepthought.tools.verification import (
    verify_addition,
    verify_subtraction,
    verify_multiplication,
    verify_division,
)
from deepthought.tools.formatting import format_json


class TestMultiplyValuesTool:
    """Tests for multiply_values tool."""

    def test_multiply_positive_integers(self):
        """Test multiplying two positive integers."""
        result = multiply_values.invoke({"val1": 6, "val2": 7})
        assert result == 42

    def test_multiply_positive_floats(self):
        """Test multiplying two positive floats."""
        result = multiply_values.invoke({"val1": 2.5, "val2": 4.0})
        assert result == 10.0

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = multiply_values.invoke({"val1": 100, "val2": 0})
        assert result == 0

    def test_multiply_negative_values(self):
        """Test multiplying negative values."""
        result = multiply_values.invoke({"val1": -5, "val2": 3})
        assert result == -15

    def test_multiply_two_negatives(self):
        """Test multiplying two negative values."""
        result = multiply_values.invoke({"val1": -4, "val2": -5})
        assert result == 20

    def test_tool_name(self):
        """Test tool has correct name."""
        assert multiply_values.name == "multiply_values"


class TestDivideValuesTool:
    """Tests for divide_values tool."""

    def test_divide_positive_integers(self):
        """Test dividing two positive integers."""
        result = divide_values.invoke({"val1": 100, "val2": 4})
        assert result == 25.0

    def test_divide_with_remainder(self):
        """Test dividing with remainder."""
        result = divide_values.invoke({"val1": 10, "val2": 3})
        assert result == pytest.approx(3.333333, rel=1e-4)

    def test_divide_by_zero(self):
        """Test dividing by zero returns error."""
        result = divide_values.invoke({"val1": 10, "val2": 0})
        assert isinstance(result, str)
        assert "Error" in result
        assert "zero" in result.lower()

    def test_divide_negative_by_positive(self):
        """Test dividing negative by positive."""
        result = divide_values.invoke({"val1": -10, "val2": 2})
        assert result == -5.0

    def test_divide_floats(self):
        """Test dividing floats."""
        result = divide_values.invoke({"val1": 7.5, "val2": 2.5})
        assert result == 3.0

    def test_tool_name(self):
        """Test tool has correct name."""
        assert divide_values.name == "divide_values"


class TestSubtractValuesTool:
    """Tests for subtract_values tool."""

    def test_subtract_positive_integers(self):
        """Test subtracting two positive integers."""
        from deepthought.tools.math_ops import subtract_values
        result = subtract_values.invoke({"val1": 100, "val2": 42})
        assert result == 58

    def test_subtract_resulting_in_negative(self):
        """Test subtraction resulting in negative."""
        from deepthought.tools.math_ops import subtract_values
        result = subtract_values.invoke({"val1": 10, "val2": 20})
        assert result == -10

    def test_subtract_with_zero(self):
        """Test subtracting zero."""
        from deepthought.tools.math_ops import subtract_values
        result = subtract_values.invoke({"val1": 42, "val2": 0})
        assert result == 42

    def test_subtract_negative_values(self):
        """Test subtracting negative from negative."""
        from deepthought.tools.math_ops import subtract_values
        result = subtract_values.invoke({"val1": -5, "val2": -3})
        assert result == -2

    def test_tool_name(self):
        """Test tool has correct name."""
        from deepthought.tools.math_ops import subtract_values
        assert subtract_values.name == "subtract_values"


class TestVerifyAdditionTool:
    """Tests for verify_addition tool."""

    def test_correct_addition(self):
        """Test verification passes for correct addition."""
        result = verify_addition.invoke({"val1": 42, "val2": 58, "result": 100})
        assert result["is_valid"] is True
        assert result["expected"] == 100
        assert result["actual"] == 100

    def test_incorrect_addition(self):
        """Test verification fails for incorrect addition."""
        result = verify_addition.invoke({"val1": 42, "val2": 58, "result": 99})
        assert result["is_valid"] is False
        assert result["expected"] == 100
        assert result["actual"] == 99

    def test_message_on_success(self):
        """Test success message."""
        result = verify_addition.invoke({"val1": 1, "val2": 1, "result": 2})
        assert "passed" in result["message"].lower()

    def test_message_on_failure(self):
        """Test failure message."""
        result = verify_addition.invoke({"val1": 1, "val2": 1, "result": 3})
        assert "failed" in result["message"].lower()


class TestVerifySubtractionTool:
    """Tests for verify_subtraction tool."""

    def test_correct_subtraction(self):
        """Test verification passes for correct subtraction."""
        result = verify_subtraction.invoke({"val1": 100, "val2": 42, "result": 58})
        assert result["is_valid"] is True
        assert result["expected"] == 58
        assert result["actual"] == 58

    def test_incorrect_subtraction(self):
        """Test verification fails for incorrect subtraction."""
        result = verify_subtraction.invoke({"val1": 100, "val2": 42, "result": 50})
        assert result["is_valid"] is False
        assert result["expected"] == 58
        assert result["actual"] == 50

    def test_message_on_success(self):
        """Test success message."""
        result = verify_subtraction.invoke({"val1": 10, "val2": 3, "result": 7})
        assert "passed" in result["message"].lower()

    def test_message_on_failure(self):
        """Test failure message."""
        result = verify_subtraction.invoke({"val1": 10, "val2": 3, "result": 5})
        assert "failed" in result["message"].lower()

    def test_negative_result(self):
        """Test verification with negative result."""
        result = verify_subtraction.invoke({"val1": 5, "val2": 10, "result": -5})
        assert result["is_valid"] is True


class TestVerifyMultiplicationTool:
    """Tests for verify_multiplication tool."""

    def test_correct_multiplication(self):
        """Test verification passes for correct multiplication."""
        result = verify_multiplication.invoke({"val1": 6, "val2": 7, "result": 42})
        assert result["is_valid"] is True
        assert result["expected"] == 42
        assert result["actual"] == 42

    def test_incorrect_multiplication(self):
        """Test verification fails for incorrect multiplication."""
        result = verify_multiplication.invoke({"val1": 6, "val2": 7, "result": 40})
        assert result["is_valid"] is False
        assert result["expected"] == 42
        assert result["actual"] == 40

    def test_multiply_with_zero(self):
        """Test verification with zero."""
        result = verify_multiplication.invoke({"val1": 100, "val2": 0, "result": 0})
        assert result["is_valid"] is True


class TestVerifyDivisionTool:
    """Tests for verify_division tool."""

    def test_correct_division(self):
        """Test verification passes for correct division."""
        result = verify_division.invoke({"val1": 100, "val2": 4, "result": 25.0})
        assert result["is_valid"] is True
        assert result["expected"] == 25.0
        assert result["actual"] == 25.0

    def test_incorrect_division(self):
        """Test verification fails for incorrect division."""
        result = verify_division.invoke({"val1": 100, "val2": 4, "result": 24.0})
        assert result["is_valid"] is False
        assert result["expected"] == 25.0
        assert result["actual"] == 24.0

    def test_division_by_zero(self):
        """Test verification fails for division by zero."""
        result = verify_division.invoke({"val1": 100, "val2": 0, "result": 0})
        assert result["is_valid"] is False
        assert "zero" in result["message"].lower()

    def test_division_with_tolerance(self):
        """Test verification passes within tolerance."""
        # 1/3 = 0.333333...
        result = verify_division.invoke({
            "val1": 1,
            "val2": 3,
            "result": 0.3333333333,
            "tolerance": 1e-9,
        })
        assert result["is_valid"] is True


class TestFormatJsonTool:
    """Tests for format_json tool."""

    def test_format_addition(self):
        """Test formatting addition result."""
        result = format_json.invoke({
            "val1": 42,
            "val2": 58,
            "result": 100,
            "operation": "add",
            "verification_passed": True,
            "verification_message": "Verification passed",
        })

        assert result["success"] is True
        assert result["calculation"]["val1"] == 42
        assert result["calculation"]["val2"] == 58
        assert result["calculation"]["result"] == 100
        assert result["calculation"]["operation"] == "add"
        assert "+" in result["calculation"]["expression"]
        assert result["verification"]["passed"] is True

    def test_format_multiplication(self):
        """Test formatting multiplication result."""
        result = format_json.invoke({
            "val1": 6,
            "val2": 7,
            "result": 42,
            "operation": "multiply",
            "verification_passed": True,
            "verification_message": "OK",
        })

        assert result["calculation"]["operation"] == "multiply"
        assert "*" in result["calculation"]["expression"]

    def test_format_division(self):
        """Test formatting division result."""
        result = format_json.invoke({
            "val1": 100,
            "val2": 4,
            "result": 25.0,
            "operation": "divide",
            "verification_passed": True,
            "verification_message": "OK",
        })

        assert result["calculation"]["operation"] == "divide"
        assert "/" in result["calculation"]["expression"]

    def test_format_subtraction(self):
        """Test formatting subtraction result."""
        result = format_json.invoke({
            "val1": 100,
            "val2": 42,
            "result": 58,
            "operation": "subtract",
            "verification_passed": True,
            "verification_message": "OK",
        })

        assert result["calculation"]["operation"] == "subtract"
        assert "-" in result["calculation"]["expression"]
        assert result["calculation"]["result"] == 58

    def test_format_failed_verification(self):
        """Test formatting with failed verification."""
        result = format_json.invoke({
            "val1": 1,
            "val2": 1,
            "result": 3,
            "operation": "add",
            "verification_passed": False,
            "verification_message": "Expected 2, got 3",
        })

        assert result["success"] is False
        assert result["verification"]["passed"] is False
        assert result["verification"]["status"] == "failed"
