"""Unit tests for math operation tools."""

import pytest

from deepthought.tools.math_ops import AddValuesInput, add_values


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
