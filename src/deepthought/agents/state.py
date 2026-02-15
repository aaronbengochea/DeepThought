"""LangGraph state definition for the multi-agent system."""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

from deepthought.models.agents import (
    ExecutionResult,
    FormattedResponse,
    Plan,
    VerificationResult,
)


class AgentState(TypedDict):
    """
    Shared state passed between all agents in the graph.

    This state flows through the entire agent pipeline:
    Orchestrator -> Execution -> Verification -> Response
    """

    # Request context
    request_id: str
    task_description: str
    input_params: dict[str, Any]

    # Agent outputs (populated as graph executes)
    plan: Plan | None
    execution_result: ExecutionResult | None
    verification_result: VerificationResult | None
    formatted_response: FormattedResponse | None

    # Message history for agent reasoning
    messages: Annotated[list[BaseMessage], add_messages]

    # Per-node timing (populated as each node completes)
    node_timings: dict[str, float]

    # Control flow
    current_step: str
    error: str | None
    should_retry: bool
    retry_count: int
