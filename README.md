# DeepThought — Operate+

AI-powered multi-agent calculation service. A full-stack application where LLM agents collaborate through a LangGraph StateGraph to execute arithmetic operations on user-created number pairs, with real-time telemetry visualization.

## Architecture

```
Frontend (Next.js 16)          Backend (FastAPI + LangGraph)          Storage (DynamoDB)
┌──────────────────┐           ┌───────────────────────────┐          ┌──────────────┐
│  Auth Views      │  HTTP/JWT │  /api/v1/auth/*           │          │ Users Table  │
│  Dashboard       │ ────────► │  /api/v1/pairs/*          │ ───────► │ Pairs Table  │
│  Pair Operations │           │                           │          │ Logs Table   │
│  Agent Timeline  │           │  Agent Graph:             │          └──────────────┘
└──────────────────┘           │  orchestrator → execution │
                               │  → verification → response│
                               └───────────────────────────┘
```

### Agent Pipeline

Each operation runs through a 4-node LangGraph StateGraph:

1. **Orchestrator** — Plans the operation and determines execution strategy
2. **Execution** — Runs the math operation via tool calls (add, subtract, multiply, divide)
3. **Verification** — Validates the result matches expected output
4. **Response** — Formats the final result for display

Per-node timing is captured and stored as telemetry, viewable in the frontend timeline.

## Project Structure

```
DeepThought/
├── backend/
│   ├── src/deepthought/
│   │   ├── agents/          # LangGraph graph, nodes, edges, prompts
│   │   ├── api/             # FastAPI app factory, routes, auth, dependencies
│   │   ├── config/          # Pydantic Settings (.env support)
│   │   ├── db/              # Async DynamoDB client (aioboto3)
│   │   ├── llm/             # LLM provider factory (Google Gemini)
│   │   ├── models/          # Pydantic v2 models
│   │   └── tools/           # LangChain @tool functions (math, verification, formatting)
│   ├── tests/
│   │   ├── unit/            # Unit tests (209 tests)
│   │   └── integration/     # API flow tests (25 tests)
│   ├── scripts/             # DynamoDB seed script
│   ├── documentation/       # Design docs
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # UI, layout, auth, pairs, telemetry components
│   │   ├── contexts/        # Auth context (JWT + localStorage)
│   │   ├── hooks/           # useAuth, usePairs, useOperations (React Query)
│   │   └── lib/             # Axios API client, TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
└── CLAUDE.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Install Dependencies

```bash
make install              # Install both backend and frontend dependencies
make install-backend      # Backend only (pip install into .venv)
make install-frontend     # Frontend only (npm install)
```

### Configure Environment

```bash
cp backend/.env.example backend/.env       # Fill in required values
cp frontend/.env.example frontend/.env     # Set NEXT_PUBLIC_API_URL
```

### Run with Docker (Production-like)

```bash
make up       # Build and start all services (frontend, backend, DynamoDB, seed)
make down     # Stop all services
```

### Run for Local Development

```bash
make dev              # Start DynamoDB + seed + backend + frontend dev servers
make dev-backend      # Backend only (with DynamoDB + seed)
make dev-frontend     # Frontend only
```

### Infrastructure Only

```bash
make database     # Start DynamoDB Local (port 8000) + Admin GUI (port 8001)
make seed         # Seed test data (starts DynamoDB if needed)
```

## Service Endpoints

When running with `make up` or `make dev`, the following services are available:

| Service | URL | Description |
|---|---|---|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8080 | FastAPI server |
| API Docs (Swagger) | http://localhost:8080/docs | Interactive API documentation |
| DynamoDB Local | http://localhost:8000 | Local DynamoDB instance |
| DynamoDB Admin | http://localhost:8001 | DynamoDB table browser GUI |

## Testing

```bash
make test             # Run all tests (backend + frontend)
make test-backend     # Backend pytest (unit + integration)
make test-frontend    # Frontend build check
```

### Additional Backend Commands

```bash
cd backend
.venv/bin/pytest tests/unit/                     # Unit tests only
.venv/bin/pytest tests/integration/              # Integration tests only
.venv/bin/pytest --cov=src/deepthought           # With coverage
```

### Linting & Type Checking

```bash
make lint     # ruff check + ruff format + mypy
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `LLM_MODEL` | Google Gemini model name (e.g. `gemini-2.0-flash`) |
| `GOOGLE_API_KEY` | Google API key |
| `AWS_REGION` | AWS region |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `DYNAMODB_ENDPOINT_URL` | DynamoDB endpoint (e.g. `http://localhost:8000`) |
| `DYNAMODB_USERS_TABLE` | Users table name |
| `DYNAMODB_PAIRS_TABLE` | Pairs table name |
| `DYNAMODB_LOGS_TABLE` | Logs table name |
| `JWT_SECRET_KEY` | Secret key for JWT signing |
| `CORS_ORIGINS` | Comma-separated allowed origins |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (e.g. `http://localhost:8080/api/v1`) |

## Tech Stack

**Backend:** Python 3.11, FastAPI, LangGraph, LangChain, Google Gemini, DynamoDB (aioboto3), Pydantic v2, bcrypt + python-jose (JWT)

**Frontend:** Next.js 16, TypeScript, Tailwind CSS 4, React Query, Axios, Lucide Icons, next-themes

**Infrastructure:** Docker Compose, DynamoDB Local, Makefile
