"""LangChain tools for agent operations."""

# Database tools
from deepthought.tools.database import query_dynamodb

# Math operation tools
from deepthought.tools.math_ops import add_values, divide_values, multiply_values, subtract_values

# Verification tools
from deepthought.tools.verification import (
    verify_addition,
    verify_division,
    verify_multiplication,
    verify_subtraction,
)

# Formatting tools
from deepthought.tools.formatting import format_json

__all__ = [
    # Database
    "query_dynamodb",
    # Math operations
    "add_values",
    "subtract_values",
    "multiply_values",
    "divide_values",
    # Verification
    "verify_addition",
    "verify_subtraction",
    "verify_multiplication",
    "verify_division",
    # Formatting
    "format_json",
]

# Tool groups for agent binding
EXECUTION_TOOLS = [query_dynamodb, add_values, subtract_values, multiply_values, divide_values]
VERIFICATION_TOOLS = [verify_addition, verify_subtraction, verify_multiplication, verify_division]
RESPONSE_TOOLS = [format_json]
