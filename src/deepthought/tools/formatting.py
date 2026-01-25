"""Formatting tools for structuring agent responses."""

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class FormatJsonInput(BaseModel):
    """Input schema for format_json tool."""

    val1: int | float = Field(..., description="First operand value")
    val2: int | float = Field(..., description="Second operand value")
    result: int | float = Field(..., description="The calculation result")
    operation: str = Field(..., description="The operation performed (add, multiply, divide)")
    verification_passed: bool = Field(..., description="Whether verification passed")
    verification_message: str = Field(
        default="", description="Optional verification message"
    )


@tool(args_schema=FormatJsonInput)
def format_json(
    val1: int | float,
    val2: int | float,
    result: int | float,
    operation: str,
    verification_passed: bool,
    verification_message: str = "",
) -> dict[str, Any]:
    """
    Format calculation results into a structured JSON response.

    Creates a user-friendly response object with all calculation details.

    Args:
        val1: First operand value
        val2: Second operand value
        result: The calculation result
        operation: The operation performed (add, multiply, divide)
        verification_passed: Whether verification passed
        verification_message: Optional verification message

    Returns:
        A structured dict with all calculation details.
    """
    # Map operation to symbol
    operation_symbols = {
        "add": "+",
        "multiply": "*",
        "divide": "/",
    }
    symbol = operation_symbols.get(operation, operation)

    return {
        "success": verification_passed,
        "calculation": {
            "val1": val1,
            "val2": val2,
            "operation": operation,
            "result": result,
            "expression": f"{val1} {symbol} {val2} = {result}",
        },
        "verification": {
            "passed": verification_passed,
            "status": "passed" if verification_passed else "failed",
            "message": verification_message,
        },
    }
