"""Database tools for agents."""

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from deepthought.config import get_settings
from deepthought.db import DynamoDBClient


class QueryDynamoDBInput(BaseModel):
    """Input schema for DynamoDB query tool."""

    pk: str = Field(..., description="Partition key value")
    sk: str = Field(..., description="Sort key value")


@tool(args_schema=QueryDynamoDBInput)
async def query_dynamodb(pk: str, sk: str) -> dict[str, Any] | None:
    """
    Query DynamoDB for an item by primary key.

    Args:
        pk: Partition key (e.g., "CALC#user123")
        sk: Sort key (e.g., "ITEM#calc001")

    Returns:
        The item if found, None otherwise.
    """
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_table_name,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )

    item = await client.get_item(pk=pk, sk=sk)
    return item
