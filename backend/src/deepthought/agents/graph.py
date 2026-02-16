"""LangGraph StateGraph definition for the multi-agent system."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from deepthought.agents.edges.routing import (
    route_after_execution,
    route_after_orchestrator,
    route_after_verification,
)
from deepthought.agents.nodes import (
    execution_node,
    orchestrator_node,
    response_node,
    verification_node,
)
from deepthought.agents.state import AgentState


def create_agent_graph() -> StateGraph[AgentState]:
    """
    Create the LangGraph StateGraph for the multi-agent system.

    Graph structure:

    START
      │
      ▼
    ┌─────────────────┐
    │  ORCHESTRATOR   │  Creates comprehensive plan
    └────────┬────────┘
             │
             ▼ (route_after_orchestrator)
    ┌─────────────────┐
    │   EXECUTION     │  Executes plan (DB query, add_values)
    └────────┬────────┘
             │
             ▼ (route_after_execution)
    ┌─────────────────┐
    │  VERIFICATION   │  Verifies results
    └────────┬────────┘
             │
             ▼ (route_after_verification)
    ┌─────────────────┐
    │    RESPONSE     │  Formats JSON response
    └────────┬────────┘
             │
             ▼
           END

    Returns:
        The StateGraph builder (not yet compiled).
    """
    # Create the graph builder
    builder: StateGraph[AgentState] = StateGraph(AgentState)

    # Add nodes (each node is an agent)
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("execution", execution_node)
    builder.add_node("verification", verification_node)
    builder.add_node("response", response_node)

    # Define edges
    builder.add_edge(START, "orchestrator")

    # Conditional routing after orchestrator
    builder.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "execution": "execution",
            "error": "response",
        },
    )

    # Conditional routing after execution
    builder.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "verification": "verification",
            "retry": "execution",
            "error": "response",
        },
    )

    # Conditional routing after verification
    builder.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "response": "response",
            "retry_execution": "execution",
            "error": "response",
        },
    )

    # Response always goes to END
    builder.add_edge("response", END)

    return builder


def compile_graph() -> CompiledStateGraph:
    """
    Compile the graph for execution.

    Returns:
        The compiled graph ready for invocation.
    """
    builder = create_agent_graph()
    return builder.compile()
