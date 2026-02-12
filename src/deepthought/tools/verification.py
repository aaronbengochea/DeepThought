"""Verification tools for validating calculation results."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class VerifyAdditionInput(BaseModel):
    """Input schema for verify_addition tool."""

    val1: int | float = Field(..., description="First value that was added")
    val2: int | float = Field(..., description="Second value that was added")
    result: int | float = Field(..., description="The result to verify")


class VerifyMultiplicationInput(BaseModel):
    """Input schema for verify_multiplication tool."""

    val1: int | float = Field(..., description="First value that was multiplied")
    val2: int | float = Field(..., description="Second value that was multiplied")
    result: int | float = Field(..., description="The result to verify")


class VerifyDivisionInput(BaseModel):
    """Input schema for verify_division tool."""

    val1: int | float = Field(..., description="Numerator that was divided")
    val2: int | float = Field(..., description="Denominator that was used")
    result: float = Field(..., description="The result to verify")
    tolerance: float = Field(
        default=1e-9, description="Tolerance for floating point comparison"
    )


class VerifySubtractionInput(BaseModel):
    """Input schema for verify_subtraction tool."""

    val1: int | float = Field(..., description="Value that was subtracted from")
    val2: int | float = Field(..., description="Value that was subtracted")
    result: int | float = Field(..., description="The result to verify")


class VerificationResult(BaseModel):
    """Result of a verification check."""

    is_valid: bool = Field(..., description="Whether the calculation is correct")
    expected: int | float = Field(..., description="The expected result")
    actual: int | float = Field(..., description="The actual result provided")
    message: str = Field(..., description="Human-readable verification message")


@tool(args_schema=VerifyAdditionInput)
def verify_addition(
    val1: int | float, val2: int | float, result: int | float
) -> dict:
    """
    Verify that an addition result is correct.

    Checks if val1 + val2 == result.

    Args:
        val1: First value that was added
        val2: Second value that was added
        result: The result to verify

    Returns:
        A dict with is_valid, expected, actual, and message fields.
    """
    expected = val1 + val2
    is_valid = expected == result

    return {
        "is_valid": is_valid,
        "expected": expected,
        "actual": result,
        "message": (
            f"Verification passed: {val1} + {val2} = {result}"
            if is_valid
            else f"Verification failed: {val1} + {val2} = {expected}, but got {result}"
        ),
    }


@tool(args_schema=VerifySubtractionInput)
def verify_subtraction(
    val1: int | float, val2: int | float, result: int | float
) -> dict:
    """
    Verify that a subtraction result is correct.

    Checks if val1 - val2 == result.

    Args:
        val1: Value that was subtracted from
        val2: Value that was subtracted
        result: The result to verify

    Returns:
        A dict with is_valid, expected, actual, and message fields.
    """
    expected = val1 - val2
    is_valid = expected == result

    return {
        "is_valid": is_valid,
        "expected": expected,
        "actual": result,
        "message": (
            f"Verification passed: {val1} - {val2} = {result}"
            if is_valid
            else f"Verification failed: {val1} - {val2} = {expected}, but got {result}"
        ),
    }


@tool(args_schema=VerifyMultiplicationInput)
def verify_multiplication(
    val1: int | float, val2: int | float, result: int | float
) -> dict:
    """
    Verify that a multiplication result is correct.

    Checks if val1 * val2 == result.

    Args:
        val1: First value that was multiplied
        val2: Second value that was multiplied
        result: The result to verify

    Returns:
        A dict with is_valid, expected, actual, and message fields.
    """
    expected = val1 * val2
    is_valid = expected == result

    return {
        "is_valid": is_valid,
        "expected": expected,
        "actual": result,
        "message": (
            f"Verification passed: {val1} * {val2} = {result}"
            if is_valid
            else f"Verification failed: {val1} * {val2} = {expected}, but got {result}"
        ),
    }


@tool(args_schema=VerifyDivisionInput)
def verify_division(
    val1: int | float, val2: int | float, result: float, tolerance: float = 1e-9
) -> dict:
    """
    Verify that a division result is correct.

    Checks if val1 / val2 ≈ result (within tolerance for floating point).

    Args:
        val1: Numerator that was divided
        val2: Denominator that was used
        result: The result to verify
        tolerance: Tolerance for floating point comparison

    Returns:
        A dict with is_valid, expected, actual, and message fields.
    """
    if val2 == 0:
        return {
            "is_valid": False,
            "expected": None,
            "actual": result,
            "message": "Verification failed: Division by zero is undefined",
        }

    expected = val1 / val2
    is_valid = abs(expected - result) <= tolerance

    return {
        "is_valid": is_valid,
        "expected": expected,
        "actual": result,
        "message": (
            f"Verification passed: {val1} / {val2} = {result}"
            if is_valid
            else f"Verification failed: {val1} / {val2} = {expected}, but got {result}"
        ),
    }
