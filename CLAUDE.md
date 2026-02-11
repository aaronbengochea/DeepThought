# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepThought is an AI-powered multi-agent calculation service built with FastAPI and LangGraph. LLM-powered agents collaborate through a LangGraph StateGraph to execute calculations fetched from DynamoDB: orchestrator plans, execution runs tools, verification validates, response formats output.

## Build & Run Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Start everything locally (DynamoDB + seed + server on :8080)
make allLocal

# Individual services
make database              # DynamoDB Local only (Docker, port 8000)
make seed                  # Seed test data
make downAllLocal          # Stop all services

# Run server manually
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080

# Tests
pytest                                    # All tests
pytest tests/unit/                        # Unit tests only
pytest tests/unit/test_nodes.py           # Single test file
pytest tests/unit/test_nodes.py::test_orchestrator_node  # Single test
pytest --cov=src/deepthought             # With coverage

# Type checking & linting
mypy src/                  # Strict mode with pydantic plugin
ruff check src/            # Lint
ruff format src/           # Format
```

## Architecture

### Agent Graph (LangGraph StateGraph)

```
START → orchestrator → execution → verification → response → END
```

Each node is an async function in `src/deepthought/agents/nodes/` that receives `AgentState` (TypedDict) and returns partial state updates. Conditional routing in `agents/edges/routing.py` handles retries (max 3 execution, max 2 verification) and error paths that skip to the response node.

### Key Modules

- **`api/`** — FastAPI app factory (`create_app()`), routes, dependency injection via `Depends()`
- **`agents/`** — LangGraph graph definition, node implementations, routing edges, system prompts per agent
- **`tools/`** — LangChain `@tool`-decorated functions: `database.py` (DynamoDB query), `math_ops.py` (add/multiply/divide), `verification.py`, `formatting.py`. Tool groups exported as `EXECUTION_TOOLS`, `VERIFICATION_TOOLS`, `RESPONSE_TOOLS`
- **`models/`** — Pydantic v2 models for agents, database, requests, responses
- **`llm/provider.py`** — Factory pattern returning Google Gemini `BaseChatModel` via `LLM_MODEL` env var
- **`db/client.py`** — Async DynamoDB wrapper using aioboto3
- **`config/settings.py`** — Pydantic Settings with `.env` support, LRU-cached singleton

### Request Flow

1. `POST /api/v1/tasks/calculate` → `routes/tasks.py`
2. Graph injected via `get_agent_graph()` (LRU-cached compiled graph)
3. `await graph.ainvoke(initial_state)` runs the agent pipeline
4. Response formatted and returned

### DynamoDB Schema

- Composite key: `pk` (partition) + `sk` (sort)
- Example: `pk="CALC#test"`, `sk="ITEM#001"` with attributes `val1`, `val2`
- Local DynamoDB via Docker on port 8000; seed with `scripts/seed_data.py`

## Code Conventions

- Python 3.11+, async-first
- mypy strict mode — full type hints required (`dict[str, Any]` not `dict`)
- Ruff: line-length 100, rules E/F/I/N/W/B/Q
- pytest-asyncio with `asyncio_mode = "auto"`
- Pydantic v2 for all data validation
- Agent nodes are stateless; state flows through `AgentState` TypedDict
- Tools are pure functions with Pydantic input schemas
- Resource lifecycle via generator pattern (DB client in `dependencies.py`)

## Environment Configuration

Copy `.env.example` to `.env`. All variables are required (no hardcoded defaults):

- `LLM_MODEL`: Google Gemini model name (e.g., `gemini-2.0-flash`)
- `GOOGLE_API_KEY`: Google API key
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `DYNAMODB_ENDPOINT_URL`: DynamoDB endpoint (e.g., `http://localhost:8000`)
- `DC_DYNAMO_ENDPOINT`: Docker-internal DynamoDB endpoint (e.g., `http://deepthought-dynamodb:8000`)
- `CORS_ORIGINS`: Allowed CORS origins

## Docker Services

`docker-compose.yml` provides DynamoDB Local (port 8000) and DynamoDB Admin GUI (port 8001) on the `sn-deepthought` bridge network.
