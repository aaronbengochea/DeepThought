# DeepThought Backend Implementation Plan

## Overview
FastAPI backend with LangGraph-based multi-agent system for orchestrated task execution.

## Tech Stack
- **Framework**: FastAPI + LangGraph
- **Database**: DynamoDB
- **Typing**: Pydantic v2 + mypy strict mode
- **Project Structure**: pyproject.toml + src/deepthought/ layout

## Architecture

```
Client Request
      │
      ▼
┌─────────────────┐
│   FastAPI       │  POST /api/v1/tasks/calculate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ORCHESTRATOR   │  Creates step-by-step plan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   EXECUTION     │  Queries DB, calls add_values tool
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VERIFICATION   │  Validates val1 + val2 == result
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    RESPONSE     │  Formats JSON: {val1, val2, result}
└────────┬────────┘
         │
         ▼
    Client Response
```

## Project Structure

```
DeepThought/
├── pyproject.toml
├── src/deepthought/
│   ├── __init__.py
│   ├── py.typed
│   ├── api/
│   │   ├── app.py              # FastAPI factory
│   │   ├── dependencies.py     # DI for graph, DB client
│   │   └── routes/
│   │       ├── health.py
│   │       └── tasks.py        # POST /calculate endpoint
│   ├── agents/
│   │   ├── graph.py            # LangGraph StateGraph
│   │   ├── state.py            # AgentState TypedDict
│   │   ├── nodes/
│   │   │   ├── orchestrator.py
│   │   │   ├── execution.py
│   │   │   ├── verification.py
│   │   │   └── response.py
│   │   └── edges/
│   │       └── routing.py      # Conditional edge logic
│   ├── tools/
│   │   ├── dynamodb.py         # query_dynamodb_tool
│   │   └── math_ops.py         # add_values_tool
│   ├── models/
│   │   ├── agents.py           # Plan, ExecutionResult, VerificationResult
│   │   ├── database.py         # DynamoDB item models
│   │   ├── requests.py         # TaskRequest
│   │   └── responses.py        # TaskResponse
│   ├── db/
│   │   └── client.py           # DynamoDB client wrapper
│   ├── config/
│   │   └── settings.py         # Pydantic BaseSettings
│   └── core/
│       └── exceptions.py       # Custom exceptions
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── scripts/
│   └── seed_data.py            # Seed test data
├── docker-compose.yml          # Local DynamoDB
└── infrastructure/             # Future AWS CDK
```

## Implementation Status

### Completed Steps ✅

#### Step 1: Project scaffolding and pyproject.toml
- [x] Create pyproject.toml with all dependencies, mypy strict config, ruff
- [x] Create src/deepthought/__init__.py and py.typed marker
- [x] Create .gitignore for Python
- [x] Remove old backend/ placeholder
- **Commit**: `"Set up Python project structure with pyproject.toml"`

#### Step 2: Configuration and core utilities
- [x] Create src/deepthought/config/__init__.py
- [x] Create src/deepthought/config/settings.py (Pydantic BaseSettings)
- [x] Create src/deepthought/core/__init__.py
- [x] Create src/deepthought/core/exceptions.py
- [x] Create .env.example
- **Commit**: `"Add configuration and core exception handling"`

#### Step 3: Pydantic models for agents
- [x] Create src/deepthought/models/__init__.py
- [x] Create src/deepthought/models/agents.py (Plan, PlanStep, ExecutionResult, VerificationResult, FormattedResponse)
- **Commit**: `"Add Pydantic models for agent state and results"`

#### Step 4: Pydantic models for API and database
- [x] Create src/deepthought/models/database.py (CalculationItem)
- [x] Create src/deepthought/models/requests.py (TaskRequest)
- [x] Create src/deepthought/models/responses.py (TaskResponse, HealthResponse)
- **Commit**: `"Add Pydantic models for API requests/responses and database"`

#### Step 5: DynamoDB client
- [x] Create src/deepthought/db/__init__.py
- [x] Create src/deepthought/db/client.py (async DynamoDB wrapper)
- **Commit**: `"Add DynamoDB client wrapper"`

#### Step 6: Agent tools
- [x] Create src/deepthought/tools/__init__.py
- [x] Create src/deepthought/tools/math_ops.py (add_values_tool)
- [x] Create src/deepthought/tools/dynamodb.py (query_dynamodb_tool)
- **Commit**: `"Add LangChain tools for math operations and DynamoDB"`

#### Step 7: Agent state definition
- [x] Create src/deepthought/agents/__init__.py
- [x] Create src/deepthought/agents/state.py (AgentState TypedDict)
- **Commit**: `"Add LangGraph agent state definition"`

#### Step 8: Orchestrator agent node
- [x] Create src/deepthought/agents/nodes/__init__.py
- [x] Create src/deepthought/agents/nodes/orchestrator.py
- **Commit**: `"Add orchestrator agent node"`

#### Step 9: Execution agent node
- [x] Create src/deepthought/agents/nodes/execution.py
- **Commit**: `"Add execution agent node"`

#### Step 10: Verification agent node
- [x] Create src/deepthought/agents/nodes/verification.py
- **Commit**: `"Add verification agent node"`

#### Step 11: Response agent node
- [x] Create src/deepthought/agents/nodes/response.py
- **Commit**: `"Add response agent node"`

#### Step 12: Graph edges and routing
- [x] Create src/deepthought/agents/edges/__init__.py
- [x] Create src/deepthought/agents/edges/routing.py
- **Commit**: `"Add conditional edge routing for agent graph"`

#### Step 13: LangGraph assembly
- [x] Create src/deepthought/agents/graph.py (StateGraph with all nodes/edges)
- **Commit**: `"Assemble LangGraph multi-agent graph"`

#### Step 14: FastAPI application factory
- [x] Create src/deepthought/api/__init__.py
- [x] Create src/deepthought/api/app.py
- [x] Create src/deepthought/api/dependencies.py
- **Commit**: `"Add FastAPI application factory and dependencies"`

#### Step 15: API routes
- [x] Create src/deepthought/api/routes/__init__.py
- [x] Create src/deepthought/api/routes/health.py
- [x] Create src/deepthought/api/routes/tasks.py
- **Commit**: `"Add FastAPI routes for health and task execution"`

#### Step 16: Local development setup
- [x] Create scripts/seed_data.py (seed test data)
- [x] Create docker-compose.yml for local DynamoDB
- **Commit**: `"Add local development scripts and Docker setup"`

#### Step 17: Test infrastructure
- [x] Create tests/__init__.py and tests/conftest.py
- [x] Create tests/unit/__init__.py
- [x] Create tests/integration/__init__.py
- **Commit**: `"Add test infrastructure and fixtures"`

#### Step 18: Write unit tests
- [x] Create tests/unit/test_math_ops.py (test add_values tool)
- [x] Create tests/unit/test_models.py (test Pydantic models)
- [x] Create tests/unit/test_nodes.py (test agent nodes with mock state)
- **Commit**: `"Add unit tests for tools, models, and agent nodes"`

---

#### Step 19: Fix LangGraph import compatibility
- [x] Update langgraph import (`langgraph.graph.graph.CompiledGraph` → `langgraph.graph.state.CompiledStateGraph`)
- [x] Fix ExecutionResult.executed_steps to use step numbers instead of tool names
- [x] Verify imports work with installed langgraph version
- [x] Run unit tests to confirm fix (69 tests pass)
- **Commit**: `"Fix LangGraph import compatibility and execution node bug"`

---

### Remaining Steps 🔲

#### Step 19.b: Refactor to True Agent Architecture with Ollama Support

**Overview**: Current "agents" are deterministic workflow nodes without LLM reasoning. This step refactors to a proper agent architecture where each agent uses an LLM for reasoning and has access to specific tools for execution.

**Architecture Change**:
```
BEFORE: Nodes with hardcoded logic (no LLM)
AFTER:  Agents with LLM reasoning + Tools for execution
```

**Tool Definitions**:
| Tool | Purpose | Used By |
|------|---------|---------|
| `query_dynamodb` | Fetch item from DB by pk/sk | Execution Agent |
| `add_values` | Add two numbers | Execution Agent |
| `multiply_values` | Multiply two numbers | Execution Agent |
| `divide_values` | Divide two numbers | Execution Agent |
| `verify_addition` | Check val1 + val2 == result | Verification Agent |
| `verify_multiplication` | Check val1 * val2 == result | Verification Agent |
| `verify_division` | Check val1 / val2 == result | Verification Agent |
| `format_json` | Structure response data | Response Agent |

##### Phase 19.b.1: LLM Provider Abstraction ✅
- [x] Add `langchain-ollama` to pyproject.toml
- [x] Create `src/deepthought/llm/__init__.py`
- [x] Create `src/deepthought/llm/provider.py` (factory for Ollama/Anthropic)
- [x] Update `src/deepthought/config/settings.py` with LLM config
- [x] Update `.env.example` with new LLM settings
- **Commit**: `"Phase 19.b.1: Add LLM provider abstraction with Ollama support"`

##### Phase 19.b.2: Infrastructure Setup ✅
- [x] Add Ollama service to `docker-compose.yml`
- [x] Create `scripts/setup_ollama.py` (pull required models)
- **Commit**: `"Phase 19.b.2: Add Ollama to Docker infrastructure"`

##### Phase 19.b.3: Refactor Tools Layer ✅
- [x] Create `src/deepthought/tools/database.py` (rename from dynamodb.py)
- [x] Update `src/deepthought/tools/math_ops.py` (add multiply, divide)
- [x] Create `src/deepthought/tools/verification.py` (verify_addition, verify_multiplication, verify_division)
- [x] Create `src/deepthought/tools/formatting.py` (format_json)
- [x] Update `src/deepthought/tools/__init__.py` (export all tools)
- **Commit**: `"Phase 19.b.3: Refactor and expand tools layer"`

##### Phase 19.b.4: Create Agent Prompts ✅
- [x] Create `src/deepthought/agents/prompts/__init__.py`
- [x] Create `src/deepthought/agents/prompts/orchestrator.py`
- [x] Create `src/deepthought/agents/prompts/execution.py`
- [x] Create `src/deepthought/agents/prompts/verification.py`
- [x] Create `src/deepthought/agents/prompts/response.py`
- **Commit**: `"Phase 19.b.4: Add agent system prompts"`

##### Phase 19.b.5: Refactor Agent Nodes ✅
- [x] Refactor `orchestrator.py` - LLM generates plan dynamically (with fallback)
- [x] Refactor `execution.py` - Tools [query_dynamodb, add_values, multiply_values, divide_values]
- [x] Refactor `verification.py` - Tools [verify_addition, verify_multiplication, verify_division]
- [x] Refactor `response.py` - Tools [format_json]
- **Commit**: `"Phase 19.b.5: Refactor agent nodes for multi-operation support"`

##### Phase 19.b.6: Update Tests ✅
- [x] Create `tests/unit/test_llm_provider.py`
- [x] Create `tests/unit/test_tools.py` (test new tools)
- [x] Update `tests/unit/test_nodes.py` (mock LLM calls)
- **Commit**: `"Phase 19.b.6: Add tests for LLM provider and new tools"`

##### Phase 19.b.7: Update Documentation ✅
- [x] Update `manualTesting.md` with Ollama setup instructions
- [x] Update `.env.example` with complete settings
- **Commit**: `"Phase 19.b.7: Update documentation with Ollama and multi-operation support"`

##### Phase 19.b.8: Holistic Testing ✅
- [x] Run full test suite (105 tests pass)
- [x] Verify Docker Compose configuration
- [x] Verify all module imports work correctly
- [x] Verify agent graph compiles successfully
- **Note**: Manual end-to-end testing requires starting Ollama/DynamoDB services

##### Phase 19.b.9: Add support for paid cloud LLM APIs listed in .env.example
- [ ] OpenAI
- [ ] Google Gemini
- [ ] Cohere
- [ ] Groq
- [ ] TogetherAI
- [ ] FireworksAI

##### Phase 19.b.20: Look up documentation for all paid clould LLM APIs and document it for future users

#### Step 19.c: Perform testing on open source LLMs
- [ ] Test with Llama 3.2
- [ ] Test with Mistral
- [ ] Test with DeepSeek
- [ ] Document performance/quality differences

#### Step 20: Write integration tests
- [ ] Create tests/integration/test_graph.py (test full graph execution)
- [ ] Create tests/integration/test_api.py (test FastAPI endpoints)

#### Step 21: Manual end-to-end testing
- [ ] Run full manual test flow (see Manual Testing Guide below)
- [ ] Verify all components work together

---

## Manual Testing Guide

Follow these steps to manually test the DeepThought backend:

### Prerequisites

- Docker installed and running
- Python 3.11+
- Ollama (for open source models) OR Anthropic API key

### Step 1: Clone and Navigate to Project

```bash
cd /path/to/DeepThought
```

### Step 2: Create Virtual Environment and Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install the package with dev dependencies
pip install -e ".[dev]"
```

### Step 3: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Required: ANTHROPIC_API_KEY=sk-ant-...
```

Your `.env` file should look like:
```
APP_NAME=DeepThought
DEBUG=true
LOG_LEVEL=DEBUG

AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy

DYNAMODB_TABLE_NAME=deepthought-calculations
DYNAMODB_ENDPOINT_URL=http://localhost:8000

ANTHROPIC_API_KEY=sk-ant-your-key-here

CORS_ORIGINS=["http://localhost:3000"]
```

### Step 4: Start Local DynamoDB

```bash
# Start DynamoDB Local using Docker Compose
docker compose up -d

# Verify it's running
docker ps
# Should show: deepthought-dynamodb
```

### Step 5: Create Table and Seed Test Data

```bash
# Run the seed script to create table and add test data
python scripts/seed_data.py
```

Expected output:
```
Connecting to local DynamoDB at http://localhost:8000
Created table: deepthought-calculations
Seeded: CALC#test/ITEM#001
Seeded: CALC#test/ITEM#002
Seeded: CALC#user123/ITEM#calc001
Done!
```

### Step 6: Start the FastAPI Server

```bash
# Start the development server (runs on port 8080 to avoid conflict with DynamoDB)
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080
```

### Step 7: Test the Health Endpoint

```bash
# In a new terminal, test health check
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-17T12:00:00.000000+00:00"
}
```

### Step 8: Test the Calculate Endpoint

Test with seeded data (val1=42, val2=58, expected result=100):

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#001"
  }'
```

Expected response:
```json
{
  "success": true,
  "request_id": "uuid-here",
  "data": {
    "val1": 42,
    "val2": 58,
    "result": 100
  },
  "execution_summary": { ... },
  "errors": null
}
```

### Step 9: Test Additional Data

Test with different seeded values (val1=100, val2=200, expected result=300):

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#002"
  }'
```

Test user calculation (val1=15, val2=25, expected result=40):

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#user123",
    "sort_key": "ITEM#calc001"
  }'
```

### Step 10: Test Error Handling

Test with non-existent data:

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#nonexistent",
    "sort_key": "ITEM#999"
  }'
```

### Step 11: View API Documentation

Open your browser and navigate to:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Step 12: Cleanup

```bash
# Stop the FastAPI server (Ctrl+C in that terminal)

# Stop DynamoDB Local
docker compose down

# Optional: Remove DynamoDB data volume
docker compose down -v
```

---

## Seeded Test Data Reference

| Partition Key | Sort Key | val1 | val2 | Expected Result |
|--------------|----------|------|------|-----------------|
| CALC#test | ITEM#001 | 42 | 58 | 100 |
| CALC#test | ITEM#002 | 100 | 200 | 300 |
| CALC#user123 | ITEM#calc001 | 15 | 25 | 40 |

---

## Troubleshooting

### DynamoDB Connection Error
- Ensure Docker is running: `docker ps`
- Check DynamoDB is on port 8000: `curl http://localhost:8000`
- Verify `DYNAMODB_ENDPOINT_URL` in `.env` is set to `http://localhost:8000`

### Anthropic API Error
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check the key is valid and has available credits

### Import Errors
- Ensure you installed with `pip install -e ".[dev]"`
- Verify virtual environment is activated

### Port Conflicts
- DynamoDB uses port 8000
- FastAPI uses port 8080 (configurable via `--port` flag)
- If ports are in use, check with `lsof -i :8000` or `lsof -i :8080`
