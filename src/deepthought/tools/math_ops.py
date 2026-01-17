"""Math operation tools for agents."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class AddValuesInput(BaseModel):
    """Input schema for add_values tool."""

    val1: int | float = Field(..., description="First value to add")
    val2: int | float = Field(..., description="Second value to add")


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
