# Operate+ Implementation Plan

## Context

DeepThought is currently a backend-only FastAPI + LangGraph multi-agent calculation service. The agent pipeline (orchestrator → execution → verification → response) queries DynamoDB for number pairs and performs add/multiply/divide operations. There is no frontend, no user auth, no subtract operation, and no operation logging/telemetry.

This plan transforms DeepThought into a full-stack application called **Operate+** with:
- A Next.js frontend with auth, pair management, and agent telemetry visualization
- Subtract as a fourth operation
- User authentication (email + password, JWT)
- Three new DynamoDB tables (users, pairs, logs) for user data, number pairs, and operation telemetry
- Simplified LLM provider (Google Gemini only)
- Docker deployment for the full stack
- Dark/light theme toggle with modern gradient UI

---

## Phase 1: Add Subtract Tool + Verification

**Goal:** Add the fourth math operation across all layers. Purely additive, zero breaking changes.

**Verify:** `pytest tests/unit/` — all existing tests pass, new subtract tests pass.

### 1.1 `src/deepthought/tools/math_ops.py`
- [X] Add `SubtractValuesInput(BaseModel)` with `val1`, `val2` fields (same pattern as `AddValuesInput`)
- [X] Add `@tool(args_schema=SubtractValuesInput) def subtract_values(val1, val2) -> int | float` returning `val1 - val2`

### 1.2 `src/deepthought/tools/verification.py`
- [X] Add `VerifySubtractionInput(BaseModel)` with `val1`, `val2`, `result` fields
- [X] Add `@tool(args_schema=VerifySubtractionInput) def verify_subtraction(val1, val2, result) -> dict` checking `val1 - val2 == result`

### 1.3 `src/deepthought/tools/__init__.py`
- [X] Import `subtract_values` and `verify_subtraction`
- [X] Add `subtract_values` to `EXECUTION_TOOLS`
- [X] Add `verify_subtraction` to `VERIFICATION_TOOLS`

### 1.4 `src/deepthought/agents/nodes/orchestrator.py`
- [X] Add `"subtract": "subtract_values"` to `OPERATION_TO_FUNCTION` dict (line 26)

### 1.5 `src/deepthought/agents/nodes/execution.py`
- [X] Import `subtract_values`
- [X] Add `"subtract": subtract_values` and `"subtract_values": subtract_values` to `OPERATION_TO_TOOL` dict (line 25)

### 1.6 `src/deepthought/agents/nodes/verification.py`
- [X] Import `verify_subtraction`
- [X] Add `"subtract": verify_subtraction` and `"subtract_values": verify_subtraction` to `OPERATION_TO_VERIFY_TOOL` (line 23)
- [X] Add `"subtract_values"` to the tool_name check on line 68: `tr.tool_name in ("add_values", "subtract_values", "multiply_values", "divide_values")`
- [X] Add `elif tr.tool_name == "subtract_values": operation = "subtract"` after line 76

### 1.7 `src/deepthought/agents/nodes/response.py`
- [X] Add `"subtract_values"` to the tool_name check on line 72
- [X] Add `elif tr.tool_name == "subtract_values": operation = "subtract"` after line 80

### 1.8 `src/deepthought/tools/formatting.py`
- [X] Add `"subtract": "-"` to `operation_symbols` dict (line 48)
- Update `operation` field description to include "subtract"

### 1.9 Agent prompts — add subtract mentions
- [X] `agents/prompts/orchestrator.py` — add `- **subtract**: Subtract two numbers (val1 - val2)` to Available Operations, update operation enum in JSON format
- [X] `agents/prompts/execution.py` — add `- **subtract_values(val1, val2)**: Subtract val2 from val1. Returns the difference.`
- [X] `agents/prompts/verification.py` — add `- **verify_subtraction(val1, val2, result)**: Verify that val1 - val2 == result`
- [X] `agents/prompts/response.py` — update operation field description to include "subtract"

### 1.10 Tests
- `tests/unit/test_tools.py` — add `TestSubtractValuesTool` and `TestVerifySubtractionTool` classes
- `tests/unit/test_math_ops.py` — add `TestSubtractValuesInput` and `TestSubtractValuesTool`
- `tests/unit/test_nodes.py` — add subtract-related tests for execution and verification nodes

---

## Phase 2: Simplify LLM to Google Only

**Goal:** Remove Ollama and Anthropic, keep only Google Gemini. Reduces complexity.

**Verify:** `pytest tests/unit/test_llm_provider.py` passes. `LLM_PROVIDER` env var no longer needed.

### 2.1 `src/deepthought/llm/provider.py`
- Remove `LLMProvider` enum
- Remove `_create_ollama_llm` and `_create_anthropic_llm` functions
- Simplify `get_llm()` to always use `_create_google_llm` with `settings.google_api_key` and `settings.llm_model`
- Remove `provider` parameter from `get_llm()`

### 2.2 `src/deepthought/llm/__init__.py`
- Remove `LLMProvider` from exports

### 2.3 `src/deepthought/config/settings.py`
- Remove: `llm_provider`, `ollama_base_url`, `anthropic_api_key`, `openai_api_key`, `cohere_api_key`, `groq_api_key`, `together_api_key`, `fireworks_api_key`
- Change `llm_model` default to `"gemini-2.0-flash"`
- Keep `google_api_key`

### 2.4 `.env.example`
- Remove all provider-specific vars except `GOOGLE_API_KEY` and `LLM_MODEL`
- Remove `LLM_PROVIDER`

### 2.5 Delete `scripts/setup_ollama.py`

### 2.6 `docker-compose.yml`
- Remove the `ollama:` service block and `ollama-models:` volume

### 2.7 `pyproject.toml`
- Remove `langchain-anthropic` and `langchain-ollama` from dependencies
- Remove their mypy overrides

### 2.8 `tests/unit/test_llm_provider.py`
- Rewrite: test Google creation, test missing API key error, remove all Ollama/Anthropic tests

---

## Phase 3: New DynamoDB Tables + Models + Seed Script

**Goal:** Create three new tables (users, pairs, logs), Pydantic models, and updated seed data.

**Verify:** `make database && make seed` creates all tables. Model tests pass.

### 3.1 New file: `src/deepthought/models/users.py`
- `User(BaseModel)` — email, name, password_hash, created_at
- `UserCreate(BaseModel)` — email, name, password (min_length=8)
- `UserSignIn(BaseModel)` — email, password
- `UserResponse(BaseModel)` — email, name, created_at
- `AuthResponse(BaseModel)` — token, user (UserResponse)

### 3.2 New file: `src/deepthought/models/pairs.py`
- `Pair(BaseModel)` — pair_id, user_email, val1, val2, created_at
- `PairCreate(BaseModel)` — val1, val2
- `PairResponse(BaseModel)` — pair_id, val1, val2, created_at

### 3.3 New file: `src/deepthought/models/logs.py`
- `AgentStepOutput(BaseModel)` — agent_name, output (dict), duration_ms
- `OperationLog(BaseModel)` — log_id, pair_id, operation, agent_steps (list[AgentStepOutput]), result, success, created_at
- `OperateRequest(BaseModel)` — operation (str)
- `OperationLogResponse(BaseModel)` — all OperationLog fields

### 3.4 `src/deepthought/models/__init__.py`
- Export all new models

### 3.5 `src/deepthought/config/settings.py`
- Add: `dynamodb_users_table: str = "deepthought-users"`
- Add: `dynamodb_pairs_table: str = "deepthought-pairs"`
- Add: `dynamodb_logs_table: str = "deepthought-logs"`
- Add: `jwt_secret_key: str = "change-this-secret-key-in-production"`
- Add: `jwt_algorithm: str = "HS256"`
- Add: `jwt_expiration_minutes: int = 1440`

### 3.6 `src/deepthought/api/dependencies.py`
- Add `get_users_db_client()`, `get_pairs_db_client()`, `get_logs_db_client()` — each returns a `DynamoDBClient` with the appropriate table name from settings

### 3.7 `scripts/seed_data.py`
- Add `create_table` calls for `deepthought-users` (pk=S, sk=S), `deepthought-pairs` (pk=S, sk=S), `deepthought-logs` (pk=S, sk=S)
- Seed a test user: email=`test@example.com`, name=`Test User`, bcrypt hash of `password123`
- Seed two test pairs for the test user
- Keep existing `deepthought-calculations` table and seed data

### 3.8 `pyproject.toml`
- Add: `"bcrypt>=4.0.0"`, `"python-jose[cryptography]>=3.3.0"`

### 3.9 Tests
- `tests/unit/test_models.py` — add tests for all new models

---

## Phase 4: New Backend API Endpoints

**Goal:** Auth (signup/signin/me), pairs (create/list), operations (operate/logs), JWT middleware.

**Verify:** `pytest tests/` passes. Manual test via `/docs` Swagger UI.

### 4.1 New file: `src/deepthought/api/auth.py`
- `hash_password(password) -> str` using bcrypt
- `verify_password(password, hash) -> bool` using bcrypt
- `create_access_token(data: dict) -> str` using python-jose (HS256, settings.jwt_secret_key)
- `decode_access_token(token) -> dict` using python-jose
- `get_current_user(token = Depends(OAuth2PasswordBearer))` — FastAPI dependency that decodes JWT, queries users table, returns user dict

### 4.2 New file: `src/deepthought/api/routes/auth.py`
- `POST /signup` — check if user exists, hash password, store in users table, return JWT + user
- `POST /signin` — verify credentials, return JWT + user
- `GET /me` — return current user (requires JWT via `get_current_user`)

### 4.3 New file: `src/deepthought/api/routes/pairs.py`
- `POST /` — create pair (val1, val2 from body, user_email from JWT, uuid for pair_id, store in pairs table)
- `GET /` — list all pairs for current user (query pairs table with pk=user_email)
- `POST /{pair_id}/operate` — execute operation on pair:
  1. Fetch pair, verify ownership
  2. Invoke agent graph with `input_params: {val1, val2, operation}` (direct values, no DB query needed)
  3. Capture telemetry from `final_state` (plan, execution_result, verification_result, formatted_response as `AgentStepOutput` list)
  4. Store log in logs table (pk=pair_id, sk=`OP#{timestamp}#{uuid}`)
  5. Return `OperationLogResponse` with all agent steps
- `GET /{pair_id}/logs` — get all operation logs for a pair (verify pair ownership, query logs table)

### 4.4 Modify agent graph for direct value passing

**Key change in `src/deepthought/agents/nodes/execution.py`:**
- At the start of `execution_node`, check if `input_params` contains `val1` and `val2`
- If present, set `db_item = {"val1": input_params["val1"], "val2": input_params["val2"]}` and skip the QUERY_DATABASE step
- This is backward compatible — the old `/calculate` endpoint still passes pk/sk

**Key change in `src/deepthought/agents/state.py`:**
- Add `node_timings: dict[str, float]` to AgentState for per-node timing

**Timing instrumentation in each node:**
- Record `time.perf_counter()` at node start/end
- Return `node_timings` with the node's duration in the state update

### 4.5 Telemetry capture in `/operate` endpoint
The `final_state` from `graph.ainvoke()` already contains:
- `final_state["plan"]` → Plan model (`.model_dump()` for serialization)
- `final_state["execution_result"]` → ExecutionResult model
- `final_state["verification_result"]` → VerificationResult model
- `final_state["formatted_response"]` → FormattedResponse model
- `final_state["node_timings"]` → per-node durations

Build `agent_steps` list from these, store in logs table.

### 4.6 `src/deepthought/api/app.py`
- Register new routers: `auth.router` at `/api/v1/auth`, `pairs.router` at `/api/v1/pairs`

### 4.7 `src/deepthought/core/exceptions.py`
- Add `AuthenticationError`, `AuthorizationError`, `NotFoundError`

### 4.8 Tests
- New file: `tests/unit/test_auth.py` — password hashing, JWT creation/decoding, signup/signin endpoints
- New file: `tests/unit/test_pairs.py` — pair CRUD, operate endpoint, logs retrieval

---

## Phase 5: Frontend Scaffolding + Auth Views

**Goal:** Initialize Next.js app, configure theme system, implement sign in/up.

**Verify:** `cd frontend && npm run dev` — auth page renders, can toggle dark/light mode.

### 5.1 Initialize Next.js
```bash
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
```

### 5.2 Install dependencies
```bash
npm install @tanstack/react-query axios lucide-react next-themes
```

### 5.3 Project structure
```
frontend/src/
  app/
    layout.tsx          — root layout with AuthProvider, QueryClientProvider, ThemeProvider
    page.tsx            — redirect to /auth or /dashboard based on auth state
    globals.css         — Tailwind config + custom gradient/dark-mode styles
    auth/page.tsx       — sign in / sign up view
    dashboard/
      page.tsx          — pair input + pair list
      layout.tsx        — dashboard shell with navbar
    pairs/[pairId]/
      page.tsx          — operations view with telemetry timeline
  components/
    ui/                 — button, input, card, toggle (reusable primitives)
    auth/               — sign-in-form, sign-up-form
    pairs/              — pair-card, pair-form, operation-button
    telemetry/          — agent-timeline, step-detail
    layout/             — navbar, theme-toggle
  contexts/
    auth-context.tsx    — React Context: user, token, login, signup, logout
  lib/
    api.ts              — Axios instance with JWT interceptor, baseURL from env
    types.ts            — TypeScript interfaces matching backend models
  hooks/
    use-auth.ts         — hook wrapping auth context
    use-pairs.ts        — React Query hooks for pairs CRUD
    use-operations.ts   — React Query hooks for operate + logs
```

### 5.4 Auth page design ("Operate+" branding)
- Centered card with logo/title "Operate+"
- Toggle between Sign In and Sign Up forms
- Sign In: email + password inputs, submit button
- Sign Up: email + name + password inputs, submit button
- On success: store JWT in localStorage, redirect to `/dashboard`
- Theme toggle in top-right corner
- Design: rounded-2xl cards, gradient accent borders, backdrop blur, dark bg (`slate-900`) / light bg (`slate-50`)

### 5.5 Theme configuration
- `next-themes` with `darkMode: 'class'` in Tailwind config
- Theme toggle component with sun/moon icons from lucide-react
- CSS custom properties for gradient accents (purple-blue in dark, blue-teal in light)

---

## Phase 6: Frontend Input View + Pairs Display

**Goal:** Dashboard where users create number pairs and see all their pairs as cards.

**Verify:** Can create pairs, see them listed with date/time, navigate to operations view.

### 6.1 Dashboard page (`app/dashboard/page.tsx`)
- **Create Pair** section: form with two number inputs + "Create Pair" button
- **Your Pairs** section: grid of pair cards, sorted by newest first
- Dashboard layout: navbar with "Operate+" logo, user name, theme toggle, logout

### 6.2 React Query hooks (`hooks/use-pairs.ts`)
- `usePairs()` — `GET /pairs`, returns `Pair[]`
- `useCreatePair()` — `POST /pairs`, invalidates pairs query on success

### 6.3 Pair card component (`components/pairs/pair-card.tsx`)
- Displays val1 and val2 prominently (large numbers)
- Created date/time in human-readable format (e.g., "Feb 10, 2026 at 3:45 PM")
- Rounded-xl card with gradient border, hover scale effect
- Clickable — navigates to `/pairs/[pairId]`

### 6.4 Pair form component (`components/pairs/pair-form.tsx`)
- Two number inputs with labels
- Submit button with loading spinner
- Success toast/animation on creation

---

## Phase 7: Frontend Operations + Telemetry Timeline

**Goal:** Operations view with 4 operation buttons and step-by-step agent timeline.

**Verify:** Click operation → loading → timeline appears showing all 4 agent steps with expandable details.

### 7.1 Operations page (`app/pairs/[pairId]/page.tsx`)
- Back button to dashboard
- Pair info header: val1, val2
- **4 operation buttons** in a row: Add (+), Subtract (-), Multiply (x), Divide (/)
  - Color-coded: blue/green/purple/orange
  - Rounded-xl with gradient backgrounds
  - Loading spinner when operation in progress
- **Operation history** below: list of past operations for this pair
  - Each entry: operation icon, result, timestamp, success badge
  - Expandable to show full telemetry timeline

### 7.2 React Query hooks (`hooks/use-operations.ts`)
- `useOperate(pairId)` — `POST /pairs/{pairId}/operate`, returns `OperationLog`
- `useLogs(pairId)` — `GET /pairs/{pairId}/logs`, returns `OperationLog[]`

### 7.3 Agent timeline component (`components/telemetry/agent-timeline.tsx`)
- **Vertical timeline** with 4 nodes connected by a line:
  1. **Orchestrator** — shows plan summary (operation, expected outcome)
  2. **Execution** — shows tool calls, inputs, outputs, timing
  3. **Verification** — shows checks, pass/fail status, confidence score
  4. **Response** — shows final formatted result, expression
- Each node: circle indicator (green=success, red=fail), agent name, duration badge
- Click to expand/collapse detail panel

### 7.4 Step detail component (`components/telemetry/step-detail.tsx`)
- Expandable card under each timeline node
- Shows full JSON output from the agent step
- Formatted and syntax-highlighted
- Copy-to-clipboard button

### 7.5 Operation button component (`components/pairs/operation-button.tsx`)
- Icon + label (e.g., + Add)
- Gradient background per operation
- Disabled + spinner while any operation is in progress
- Hover/active states

---

## Phase 8: Dockerfiles + Compose Updates

**Goal:** Containerize backend and frontend, unified docker-compose with shared network.

**Verify:** `docker compose up` — all 3 services start, frontend at :3000, backend at :8080, DynamoDB at :8000.

### 8.1 New file: `Dockerfile` (backend)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."
COPY src/ src/
COPY scripts/ scripts/
EXPOSE 8080
CMD ["uvicorn", "src.deepthought.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
```

### 8.2 New file: `frontend/Dockerfile`
Multi-stage build:
- Stage 1 (builder): `node:20-alpine`, `npm ci`, `npm run build` (with `NEXT_PUBLIC_API_URL` build arg)
- Stage 2 (runner): `node:20-alpine`, copy standalone output, `EXPOSE 3000`, `CMD ["node", "server.js"]`
- Requires `output: 'standalone'` in `next.config.ts`

### 8.3 `docker-compose.yml` — full rewrite
```yaml
services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    ports: ["8000:8000"]
    healthcheck: ...
    networks: [deepthought-network]

  backend:
    build: { context: ., dockerfile: Dockerfile }
    ports: ["8080:8080"]
    env_file: [.env]
    environment:
      DYNAMODB_ENDPOINT_URL: http://dynamodb-local:8000
    depends_on:
      dynamodb-local: { condition: service_healthy }
    networks: [deepthought-network]

  frontend:
    build:
      context: ./frontend
      args: { NEXT_PUBLIC_API_URL: http://localhost:8080/api/v1 }
    ports: ["3000:3000"]
    depends_on: [backend]
    networks: [deepthought-network]

networks:
  deepthought-network:
    driver: bridge
```

### 8.4 New files: `.dockerignore` and `frontend/.dockerignore`

---

## Phase 9: Makefile Updates

**Goal:** New commands for full-stack build/run/dev workflow.

### 9.1 `Makefile`
- `make build` — `docker compose build`
- `make up` — `docker compose up -d` + sleep + `make seed` + print service URLs
- `make down` — `docker compose down`
- `make dev` — start DynamoDB + seed + backend (uvicorn --reload) + frontend (npm run dev)
- `make frontend-dev` — `cd frontend && npm run dev`
- `make lint` — `ruff check src/ && ruff format --check src/ && mypy src/`
- `make test` — `pytest tests/`
- Keep existing `allLocal`, `database`, `seed`, `downAllLocal` commands working

---

## Phase 10: Integration Testing + Polish

**Goal:** End-to-end tests, documentation, edge case handling.

### 10.1 New file: `tests/integration/test_api_flow.py`
- Full flow: signup → signin → create pair → operate (all 4 ops) → get logs
- Auth edge cases: duplicate signup (409), wrong password (401), expired JWT
- Ownership: user A cannot access user B's pairs

### 10.2 Update `CLAUDE.md` and `README.md`
- New architecture diagram, API endpoints, frontend info, Docker deployment, Google-only LLM

### 10.3 Update `.env.example`
- Add new table names, JWT settings

### 10.4 Update `.gitignore`
- Add `frontend/node_modules/`, `frontend/.next/`

---

## Phase Dependency Graph

```
Phase 1 (Subtract) ──┐
                      ├──→ Phase 3 (DB Tables) ──→ Phase 4 (API) ──┐
Phase 2 (Google LLM) ─┘                                             │
                                                                     ├──→ Phase 8 (Docker) ──→ Phase 9 (Makefile) ──→ Phase 10 (Polish)
Phase 5 (Frontend Scaffold) ──→ Phase 6 (Pairs UI) ──→ Phase 7 (Ops UI) ─┘
```

- Phases 1 & 2 are independent (can be done in parallel)
- Phase 3 depends on 1 & 2
- Phase 4 depends on 3
- Phases 5-7 can start after Phase 4 (or in parallel with mock data)
- Phase 8 depends on all functional work
- Phase 9 depends on 8
- Phase 10 is final polish

---

## Files Summary

**New files (~20+ backend, ~30+ frontend):**
- `src/deepthought/models/users.py`, `pairs.py`, `logs.py`
- `src/deepthought/api/auth.py`
- `src/deepthought/api/routes/auth.py`, `pairs.py`
- `tests/unit/test_auth.py`, `test_pairs.py`
- `tests/integration/test_api_flow.py`
- `Dockerfile`, `.dockerignore`
- `frontend/` (entire Next.js app)
- `frontend/Dockerfile`, `frontend/.dockerignore`

**Modified files (~20):**
- `src/deepthought/tools/math_ops.py`, `verification.py`, `__init__.py`, `formatting.py`
- `src/deepthought/agents/nodes/orchestrator.py`, `execution.py`, `verification.py`, `response.py`
- `src/deepthought/agents/prompts/orchestrator.py`, `execution.py`, `verification.py`, `response.py`
- `src/deepthought/agents/state.py`
- `src/deepthought/llm/provider.py`, `__init__.py`
- `src/deepthought/config/settings.py`
- `src/deepthought/api/app.py`, `dependencies.py`
- `src/deepthought/core/exceptions.py`
- `pyproject.toml`, `docker-compose.yml`, `Makefile`, `.env.example`, `scripts/seed_data.py`

**Deleted files:** `scripts/setup_ollama.py`
