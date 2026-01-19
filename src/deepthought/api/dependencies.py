"""Dependency injection for FastAPI routes."""

from functools import lru_cache
from typing import Generator

from langgraph.graph.state import CompiledStateGraph

from deepthought.agents import compile_graph
from deepthought.config import get_settings
from deepthought.db import DynamoDBClient


@lru_cache
def get_agent_graph() -> CompiledStateGraph:
    """Get the compiled LangGraph agent graph (singleton)."""
    return compile_graph()


def get_dynamodb_client() -> Generator[DynamoDBClient, None, None]:
    """Dependency to get DynamoDB client."""
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_table_name,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    yield client
