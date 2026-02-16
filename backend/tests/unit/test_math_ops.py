"""Unit tests for math operation tools."""

import pytest

from deepthought.tools.math_ops import (
    AddValuesInput,
    DivideValuesInput,
    MultiplyValuesInput,
    SubtractValuesInput,
    add_values,
    divide_values,
    multiply_values,
    subtract_values,
)


class TestAddValuesInput:
    """Tests for AddValuesInput schema."""

    def test_valid_integers(self):
        """Test schema accepts valid integers."""
        input_data = AddValuesInput(val1=10, val2=20)
        assert input_data.val1 == 10
        assert input_data.val2 == 20

    def test_valid_floats(self):
        """Test schema accepts valid floats."""
        input_data = AddValuesInput(val1=10.5, val2=20.5)
        assert input_data.val1 == 10.5
        assert input_data.val2 == 20.5

    def test_mixed_int_float(self):
        """Test schema accepts mixed int and float."""
        input_data = AddValuesInput(val1=10, val2=20.5)
        assert input_data.val1 == 10
        assert input_data.val2 == 20.5

    def test_negative_values(self):
        """Test schema accepts negative values."""
        input_data = AddValuesInput(val1=-10, val2=-20)
        assert input_data.val1 == -10
        assert input_data.val2 == -20

    def test_zero_values(self):
        """Test schema accepts zero values."""
        input_data = AddValuesInput(val1=0, val2=0)
        assert input_data.val1 == 0
        assert input_data.val2 == 0

    def test_missing_val1_raises_error(self):
        """Test schema requires val1."""
        with pytest.raises(ValueError):
            AddValuesInput(val2=20)  # type: ignore[call-arg]

    def test_missing_val2_raises_error(self):
        """Test schema requires val2."""
        with pytest.raises(ValueError):
            AddValuesInput(val1=10)  # type: ignore[call-arg]


class TestAddValuesTool:
    """Tests for add_values tool."""

    def test_add_positive_integers(self):
        """Test adding two positive integers."""
        result = add_values.invoke({"val1": 42, "val2": 58})
        assert result == 100

    def test_add_positive_floats(self):
        """Test adding two positive floats."""
        result = add_values.invoke({"val1": 1.5, "val2": 2.5})
        assert result == 4.0

    def test_add_mixed_int_float(self):
        """Test adding int and float."""
        result = add_values.invoke({"val1": 10, "val2": 0.5})
        assert result == 10.5

    def test_add_negative_values(self):
        """Test adding negative values."""
        result = add_values.invoke({"val1": -10, "val2": -20})
        assert result == -30

    def test_add_mixed_positive_negative(self):
        """Test adding positive and negative values."""
        result = add_values.invoke({"val1": 100, "val2": -50})
        assert result == 50

    def test_add_zeros(self):
        """Test adding zeros."""
        result = add_values.invoke({"val1": 0, "val2": 0})
        assert result == 0

    def test_add_zero_and_value(self):
        """Test adding zero and a value."""
        result = add_values.invoke({"val1": 0, "val2": 42})
        assert result == 42

    def test_add_large_numbers(self):
        """Test adding large numbers."""
        result = add_values.invoke({"val1": 1_000_000, "val2": 2_000_000})
        assert result == 3_000_000

    def test_add_small_floats(self):
        """Test adding small floats."""
        result = add_values.invoke({"val1": 0.001, "val2": 0.002})
        assert result == pytest.approx(0.003)

    def test_tool_name(self):
        """Test tool has correct name."""
        assert add_values.name == "add_values"

    def test_tool_description(self):
        """Test tool has description."""
        assert add_values.description is not None
        assert "add" in add_values.description.lower()


class TestSubtractValuesInput:
    """Tests for SubtractValuesInput schema."""

    def test_valid_integers(self):
        """Test schema accepts valid integers."""
        input_data = SubtractValuesInput(val1=20, val2=10)
        assert input_data.val1 == 20
        assert input_data.val2 == 10

    def test_valid_floats(self):
        """Test schema accepts valid floats."""
        input_data = SubtractValuesInput(val1=20.5, val2=10.5)
        assert input_data.val1 == 20.5
        assert input_data.val2 == 10.5

    def test_negative_values(self):
        """Test schema accepts negative values."""
        input_data = SubtractValuesInput(val1=-10, val2=-20)
        assert input_data.val1 == -10
        assert input_data.val2 == -20

    def test_missing_val1_raises_error(self):
        """Test schema requires val1."""
        with pytest.raises(ValueError):
            SubtractValuesInput(val2=20)  # type: ignore[call-arg]

    def test_missing_val2_raises_error(self):
        """Test schema requires val2."""
        with pytest.raises(ValueError):
            SubtractValuesInput(val1=10)  # type: ignore[call-arg]


class TestSubtractValuesTool:
    """Tests for subtract_values tool."""

    def test_subtract_positive_integers(self):
        """Test subtracting two positive integers."""
        result = subtract_values.invoke({"val1": 100, "val2": 42})
        assert result == 58

    def test_subtract_positive_floats(self):
        """Test subtracting two positive floats."""
        result = subtract_values.invoke({"val1": 10.5, "val2": 3.5})
        assert result == 7.0

    def test_subtract_negative_values(self):
        """Test subtracting negative values."""
        result = subtract_values.invoke({"val1": -10, "val2": -20})
        assert result == 10

    def test_subtract_mixed_positive_negative(self):
        """Test subtracting negative from positive."""
        result = subtract_values.invoke({"val1": 50, "val2": -50})
        assert result == 100

    def test_subtract_resulting_in_negative(self):
        """Test subtraction resulting in a negative number."""
        result = subtract_values.invoke({"val1": 10, "val2": 20})
        assert result == -10

    def test_subtract_zeros(self):
        """Test subtracting zeros."""
        result = subtract_values.invoke({"val1": 0, "val2": 0})
        assert result == 0

    def test_subtract_from_zero(self):
        """Test subtracting from zero."""
        result = subtract_values.invoke({"val1": 0, "val2": 42})
        assert result == -42

    def test_subtract_large_numbers(self):
        """Test subtracting large numbers."""
        result = subtract_values.invoke({"val1": 3_000_000, "val2": 1_000_000})
        assert result == 2_000_000

    def test_tool_name(self):
        """Test tool has correct name."""
        assert subtract_values.name == "subtract_values"

    def test_tool_description(self):
        """Test tool has description."""
        assert subtract_values.description is not None
        assert "subtract" in subtract_values.description.lower()


class TestMultiplyValuesInput:
    """Tests for MultiplyValuesInput schema."""

    def test_valid_integers(self):
        """Test schema accepts valid integers."""
        input_data = MultiplyValuesInput(val1=6, val2=7)
        assert input_data.val1 == 6
        assert input_data.val2 == 7

    def test_valid_floats(self):
        """Test schema accepts valid floats."""
        input_data = MultiplyValuesInput(val1=2.5, val2=4.0)
        assert input_data.val1 == 2.5
        assert input_data.val2 == 4.0

    def test_negative_values(self):
        """Test schema accepts negative values."""
        input_data = MultiplyValuesInput(val1=-5, val2=3)
        assert input_data.val1 == -5
        assert input_data.val2 == 3

    def test_missing_val1_raises_error(self):
        """Test schema requires val1."""
        with pytest.raises(ValueError):
            MultiplyValuesInput(val2=7)  # type: ignore[call-arg]

    def test_missing_val2_raises_error(self):
        """Test schema requires val2."""
        with pytest.raises(ValueError):
            MultiplyValuesInput(val1=6)  # type: ignore[call-arg]


class TestMultiplyValuesTool:
    """Tests for multiply_values tool (test_math_ops)."""

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

    def test_multiply_negative_by_positive(self):
        """Test multiplying negative by positive."""
        result = multiply_values.invoke({"val1": -5, "val2": 3})
        assert result == -15

    def test_multiply_two_negatives(self):
        """Test multiplying two negatives."""
        result = multiply_values.invoke({"val1": -4, "val2": -5})
        assert result == 20

    def test_multiply_by_one(self):
        """Test multiplying by one (identity)."""
        result = multiply_values.invoke({"val1": 42, "val2": 1})
        assert result == 42

    def test_multiply_large_numbers(self):
        """Test multiplying large numbers."""
        result = multiply_values.invoke({"val1": 1_000, "val2": 1_000})
        assert result == 1_000_000

    def test_tool_name(self):
        """Test tool has correct name."""
        assert multiply_values.name == "multiply_values"

    def test_tool_description(self):
        """Test tool has description."""
        assert multiply_values.description is not None
        assert "multiply" in multiply_values.description.lower()


class TestDivideValuesInput:
    """Tests for DivideValuesInput schema."""

    def test_valid_integers(self):
        """Test schema accepts valid integers."""
        input_data = DivideValuesInput(val1=100, val2=4)
        assert input_data.val1 == 100
        assert input_data.val2 == 4

    def test_valid_floats(self):
        """Test schema accepts valid floats."""
        input_data = DivideValuesInput(val1=7.5, val2=2.5)
        assert input_data.val1 == 7.5
        assert input_data.val2 == 2.5

    def test_negative_values(self):
        """Test schema accepts negative values."""
        input_data = DivideValuesInput(val1=-10, val2=2)
        assert input_data.val1 == -10
        assert input_data.val2 == 2

    def test_missing_val1_raises_error(self):
        """Test schema requires val1."""
        with pytest.raises(ValueError):
            DivideValuesInput(val2=4)  # type: ignore[call-arg]

    def test_missing_val2_raises_error(self):
        """Test schema requires val2."""
        with pytest.raises(ValueError):
            DivideValuesInput(val1=100)  # type: ignore[call-arg]


class TestDivideValuesTool:
    """Tests for divide_values tool (test_math_ops)."""

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

    def test_divide_by_one(self):
        """Test dividing by one (identity)."""
        result = divide_values.invoke({"val1": 42, "val2": 1})
        assert result == 42.0

    def test_divide_same_values(self):
        """Test dividing a number by itself."""
        result = divide_values.invoke({"val1": 99, "val2": 99})
        assert result == 1.0

    def test_tool_name(self):
        """Test tool has correct name."""
        assert divide_values.name == "divide_values"

    def test_tool_description(self):
        """Test tool has description."""
        assert divide_values.description is not None
        assert "divide" in divide_values.description.lower()
