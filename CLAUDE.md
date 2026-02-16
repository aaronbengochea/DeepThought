# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepThought (Operate+) is an AI-powered multi-agent calculation service with a Next.js frontend and FastAPI + LangGraph backend. LLM-powered agents collaborate through a LangGraph StateGraph to execute calculations: orchestrator plans, execution runs tools, verification validates, response formats output.

## Project Structure

```
DeepThought/
  backend/          — Python FastAPI + LangGraph backend
  frontend/         — Next.js TypeScript frontend
  docker-compose.yml
  Makefile
```

## Build & Run Commands

```bash
# Full stack (Docker)
make build                # Build all containers
make up                   # Start everything (DynamoDB + seed + backend + frontend)
make down                 # Stop all services

# Individual services
make database             # DynamoDB Local only (Docker, port 8000)
make seed                 # Seed test data via Docker

# Local development (backend + frontend outside Docker)
make dev                  # DynamoDB (Docker) + seed + backend :8080 + frontend :3000
make frontend-dev         # Frontend dev server only

# Backend commands (run from backend/)
cd backend
pip install -e ".[dev]"
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080
pytest                    # All tests
pytest tests/unit/        # Unit tests only
mypy src/                 # Type checking
ruff check src/           # Lint
ruff format src/          # Format

# Quality (from repo root)
make test                 # Run backend tests
make lint                 # Ruff + mypy
```

## Architecture

### Agent Graph (LangGraph StateGraph)

```
START → orchestrator → execution → verification → response → END
```

Each node is an async function in `backend/src/deepthought/agents/nodes/` that receives `AgentState` (TypedDict) and returns partial state updates. Conditional routing in `agents/edges/routing.py` handles retries (max 3 execution, max 2 verification) and error paths that skip to the response node.

### Key Modules (under `backend/src/deepthought/`)

- **`api/`** — FastAPI app factory (`create_app()`), routes, dependency injection via `Depends()`
- **`agents/`** — LangGraph graph definition, node implementations, routing edges, system prompts per agent
- **`tools/`** — LangChain `@tool`-decorated functions: `database.py` (DynamoDB query), `math_ops.py` (add/subtract/multiply/divide), `verification.py`, `formatting.py`. Tool groups exported as `EXECUTION_TOOLS`, `VERIFICATION_TOOLS`, `RESPONSE_TOOLS`
- **`models/`** — Pydantic v2 models for agents, database, users, pairs, logs, responses
- **`llm/provider.py`** — Factory pattern returning Google Gemini `BaseChatModel` via `LLM_MODEL` env var
- **`db/client.py`** — Async DynamoDB wrapper using aioboto3
- **`config/settings.py`** — Pydantic Settings with `.env` support, LRU-cached singleton

### Request Flow

1. `POST /api/v1/auth/signup` or `POST /api/v1/auth/signin` → `routes/auth.py` (JWT auth)
2. `POST /api/v1/pairs/{pair_id}/operate` → `routes/pairs.py`
3. Graph injected via `get_agent_graph()` (LRU-cached compiled graph)
4. `await graph.ainvoke(initial_state)` runs the agent pipeline
5. Telemetry captured from final state, stored in logs table
6. Response formatted and returned

### DynamoDB Schema

Three tables with composite keys (`pk` + `sk`):
- **Users** (`deepthought-users`): `pk` = email (no sort key)
- **Pairs** (`deepthought-pairs`): `pk` = user_email, `sk` = pair_id (UUID)
- **Logs** (`deepthought-logs`): `pk` = pair_id, `sk` = `OP#{timestamp}#{log_id}`
- Local DynamoDB via Docker on port 8000; seed with `backend/scripts/seed_data.py`

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

Backend: copy `backend/.env.example` to `backend/.env`. All variables are required (no hardcoded defaults):

- `LLM_MODEL`: Google Gemini model name (e.g., `gemini-2.0-flash`)
- `GOOGLE_API_KEY`: Google API key
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `DYNAMODB_ENDPOINT_URL`: DynamoDB endpoint (e.g., `http://localhost:8000`)
- `DYNAMODB_USERS_TABLE`, `DYNAMODB_PAIRS_TABLE`, `DYNAMODB_LOGS_TABLE`: DynamoDB table names
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `CORS_ORIGINS`: Allowed CORS origins

Frontend: copy `frontend/.env.example` to `frontend/.env`:

- `NEXT_PUBLIC_API_URL`: Backend API URL (e.g., `http://localhost:8080/api/v1`)

## Docker Services

`docker-compose.yml` orchestrates: DynamoDB Local (:8000), seed runner, backend (:8080), frontend (:3000) on the `deepthought` bridge network.
