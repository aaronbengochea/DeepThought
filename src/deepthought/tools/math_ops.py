"""Math operation tools for agents."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class AddValuesInput(BaseModel):
    """Input schema for add_values tool."""

    val1: int | float = Field(..., description="First value to add")
    val2: int | float = Field(..., description="Second value to add")


class MultiplyValuesInput(BaseModel):
    """Input schema for multiply_values tool."""

    val1: int | float = Field(..., description="First value to multiply")
    val2: int | float = Field(..., description="Second value to multiply")


class DivideValuesInput(BaseModel):
    """Input schema for divide_values tool."""

    val1: int | float = Field(..., description="Numerator (value to divide)")
    val2: int | float = Field(..., description="Denominator (value to divide by)")


@tool(args_schema=AddValuesInput)
def add_values(val1: int | float, val2: int | float) -> int | float:
    """
    Add two values together.

    Args:
        val1: First value
        val2: Second value

    Returns:
        The sum of val1 and val2.
    """
    return val1 + val2


@tool(args_schema=MultiplyValuesInput)
def multiply_values(val1: int | float, val2: int | float) -> int | float:
    """
    Multiply two values together.

    Args:
        val1: First value
        val2: Second value

    Returns:
        The product of val1 and val2.
    """
    return val1 * val2


@tool(args_schema=DivideValuesInput)
def divide_values(val1: int | float, val2: int | float) -> float | str:
    """
    Divide val1 by val2.

    Args:
        val1: Numerator (value to divide)
        val2: Denominator (value to divide by)

    Returns:
        The result of val1 / val2, or an error message if division by zero.
    """
    if val2 == 0:
        return "Error: Division by zero is not allowed"
    return val1 / val2
