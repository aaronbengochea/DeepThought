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


def get_users_db_client() -> Generator[DynamoDBClient, None, None]:
    """Dependency to get DynamoDB client for the users table."""
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_users_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    yield client


def get_pairs_db_client() -> Generator[DynamoDBClient, None, None]:
    """Dependency to get DynamoDB client for the pairs table."""
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_pairs_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    yield client


def get_logs_db_client() -> Generator[DynamoDBClient, None, None]:
    """Dependency to get DynamoDB client for the logs table."""
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_logs_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    yield client


def get_calendar_db_client() -> Generator[DynamoDBClient, None, None]:
    """Dependency to get DynamoDB client for the calendar table."""
    settings = get_settings()
    client = DynamoDBClient(
        table_name=settings.dynamodb_calendar_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    yield client
