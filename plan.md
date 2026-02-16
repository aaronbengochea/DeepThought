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

### 1.10 Subtraction Tests
- [X] `tests/unit/test_tools.py` — add `TestSubtractValuesTool` (5 tests) and `TestVerifySubtractionTool` (5 tests) classes, plus subtract formatting test
- [X] `tests/unit/test_math_ops.py` — add `TestSubtractValuesInput` (5 tests) and `TestSubtractValuesTool` (10 tests)
- [X] `tests/unit/test_nodes.py` — add subtract execution, verification, and response node tests (3 tests)

### 1.11 Multiplication Tests
- [X] `tests/unit/test_math_ops.py` — add `TestMultiplyValuesInput` (5 tests) and `TestMultiplyValuesTool` (9 tests)
- [X] `tests/unit/test_tools.py` — add `TestVerifyMultiplicationTool` message success/failure tests (2 tests)
- [X] `tests/unit/test_nodes.py` — add multiply execution, verification, and response node tests (3 tests)

### 1.12 Division Tests
- [X] `tests/unit/test_math_ops.py` — add `TestDivideValuesInput` (5 tests) and `TestDivideValuesTool` (9 tests)
- [X] `tests/unit/test_tools.py` — add `TestVerifyDivisionTool` message success/failure tests (2 tests)
- [X] `tests/unit/test_nodes.py` — add divide execution, verification, and response node tests (3 tests)

---

## Phase 2: Simplify LLM to Google Only

**Goal:** Remove Ollama and Anthropic, keep only Google Gemini. Reduces complexity.

**Verify:** `pytest tests/unit/test_llm_provider.py` passes. `LLM_PROVIDER` env var no longer needed.

### 2.1 `src/deepthought/llm/provider.py`
- [X] Remove `LLMProvider` enum
- [X] Remove `_create_ollama_llm` and `_create_anthropic_llm` functions
- [X] Simplify `get_llm()` to always use `_create_google_llm` with `settings.google_api_key` and `settings.llm_model`
- [X] Remove `provider` parameter from `get_llm()`

### 2.2 `src/deepthought/llm/__init__.py`
- [X] Remove `LLMProvider` from exports

### 2.3 `src/deepthought/config/settings.py`
- [X] Remove: `llm_provider`, `ollama_base_url`, `anthropic_api_key`, `openai_api_key`, `cohere_api_key`, `groq_api_key`, `together_api_key`, `fireworks_api_key`
- [X] Keep `llm_model` as required env var (no default needed)
- [X] Keep `google_api_key`

### 2.4 `.env.example`
- [X] Remove all provider-specific vars except `GOOGLE_API_KEY` and `LLM_MODEL`
- [X] Remove `LLM_PROVIDER`

### 2.5 Delete `scripts/setup_ollama.py`
- [X] Already absent — never existed in this codebase

### 2.6 `docker-compose.yml`
- [X] Remove the `ollama:` service block and `ollama-models:` volume

### 2.7 `pyproject.toml`
- [X] Remove `langchain-anthropic` and `langchain-ollama` from dependencies
- [X] Remove their mypy overrides

### 2.8 `tests/unit/test_llm_provider.py`
- [X] Rewrite: test Google creation, test missing API key error, remove all Ollama/Anthropic tests

---

## Phase 3: New DynamoDB Tables + Models + Seed Script

**Goal:** Create three new tables (users, pairs, logs), Pydantic models, and updated seed data.

**Verify:** `make database && make seed` creates all tables. Model tests pass.

### 3.1 New file: `src/deepthought/models/users.py`
- [X] `User(BaseModel)` — email, name, password_hash, created_at
- [X] `UserCreate(BaseModel)` — email, name, password (min_length=8)
- [X] `UserSignIn(BaseModel)` — email, password
- [X] `UserResponse(BaseModel)` — email, name, created_at
- [X] `AuthResponse(BaseModel)` — token, user (UserResponse)

### 3.2 New file: `src/deepthought/models/pairs.py`
- [X] `Pair(BaseModel)` — pair_id, user_email, val1, val2, created_at
- [X] `PairCreate(BaseModel)` — val1, val2
- [X] `PairResponse(BaseModel)` — pair_id, val1, val2, created_at

### 3.3 New file: `src/deepthought/models/logs.py`
- [X] `AgentStepOutput(BaseModel)` — agent_name, output (dict), duration_ms
- [X] `OperationLog(BaseModel)` — log_id, pair_id, operation, agent_steps (list[AgentStepOutput]), result, success, created_at
- [X] `OperateRequest(BaseModel)` — operation (str)
- [X] `OperationLogResponse(BaseModel)` — all OperationLog fields

### 3.4 `src/deepthought/models/__init__.py`
- [X] Export all new models

### 3.5 `src/deepthought/config/settings.py` + `.env.example` + `.env`
- [X] Add: `dynamodb_users_table: str` (required env var, no default)
- [X] Add: `dynamodb_pairs_table: str` (required env var, no default)
- [X] Add: `dynamodb_logs_table: str` (required env var, no default)
- [X] Add: `jwt_secret_key: str` (required env var, no default)
- [X] Add: `jwt_algorithm: str = "HS256"`
- [X] Add: `jwt_expiration_minutes: int = 1440`
- [X] Add table names and JWT_SECRET_KEY to `.env.example` and `.env`

### 3.6 `src/deepthought/api/dependencies.py`
- [X] Add `get_users_db_client()`, `get_pairs_db_client()`, `get_logs_db_client()` — each returns a `DynamoDBClient` with the appropriate table name from settings

### 3.7 `scripts/seed_data.py`
- [X] Add `create_table` calls for `deepthought-users` (pk=S, sk=S), `deepthought-pairs` (pk=S, sk=S), `deepthought-logs` (pk=S, sk=S)
- [X] Seed a test user: email=`test@example.com`, name=`Test User`, bcrypt hash of `password123`
- [X] Seed two test pairs for the test user
- [X] Keep existing `deepthought-calculations` table and seed data (will be deprecated in Phase 4)

### 3.8 `pyproject.toml`
- [X] Add: `"bcrypt>=4.0.0"`, `"python-jose[cryptography]>=3.3.0"`, `"email-validator>=2.0.0"`, `"python-dotenv>=1.0.0"`
- [X] Add mypy overrides for `jose`, `bcrypt`, `dotenv`

### 3.9 Tests
- [X] `tests/unit/test_models.py` — add tests for all new models (27 new tests, 54 total)

---

## Phase 4: New Backend API Endpoints

**Goal:** Auth (signup/signin/me), pairs (create/list), operations (operate/logs), JWT middleware.

**Verify:** `pytest tests/` passes. Manual test via `/docs` Swagger UI.

### 4.1 New file: `src/deepthought/api/auth.py`
- [X] `hash_password(password) -> str` using bcrypt
- [X] `verify_password(password, hash) -> bool` using bcrypt
- [X] `create_access_token(data: dict) -> str` using python-jose (HS256, settings.jwt_secret_key)
- [X] `decode_access_token(token) -> dict` using python-jose
- [X] `get_current_user(token = Depends(OAuth2PasswordBearer))` — FastAPI dependency that decodes JWT, queries users table, returns user dict

### 4.2 New file: `src/deepthought/api/routes/auth.py`
- [X] `POST /signup` — check if user exists, hash password, store in users table, return JWT + user
- [X] `POST /signin` — verify credentials, return SignInResponse (token + email)
- [X] `GET /profile` — return current user (requires JWT via `get_current_user`)

### 4.3 New file: `src/deepthought/api/routes/pairs.py`
- [X] `POST /` — create pair (val1, val2 from body, user_email from JWT, uuid for pair_id, store in pairs table)
- [X] `GET /` — list all pairs for current user (query pairs table with pk=user_email)
- [X] `POST /{pair_id}/operate` — execute operation on pair:
  1. Fetch pair, verify ownership
  2. Invoke agent graph with `input_params: {val1, val2, operation}` (direct values, no DB query needed)
  3. Capture telemetry from `final_state` (plan, execution_result, verification_result, formatted_response as `AgentStepOutput` list)
  4. Store log in logs table (pk=pair_id, sk=`OP#{timestamp}#{uuid}`)
  5. Return `OperationLogResponse` with all agent steps
- [X] `GET /{pair_id}/logs` — get all operation logs for a pair (verify pair ownership, query logs table)

### 4.4 Modify agent graph for direct value passing

**Key change in `src/deepthought/agents/nodes/execution.py`:**
- [X] At the start of `execution_node`, check if `input_params` contains `val1` and `val2`
- [X] If present, set `db_item = {"val1": input_params["val1"], "val2": input_params["val2"]}` and skip the QUERY_DATABASE step
- [X] This is backward compatible — the old `/calculate` endpoint still passes pk/sk

### 4.4.1 Per-node timing instrumentation

- [X] Add `node_timings: dict[str, float]` to `AgentState` in `agents/state.py`
- [X] Wrap each node (orchestrator, execution, verification, response) with `time.perf_counter()` start/end
- [X] Each node returns `node_timings: {"<node_name>": duration_ms}` in its state update
- [X] Operate endpoint reads `node_timings` from `final_state` to populate `duration_ms` on each `AgentStepOutput`
- [X] Add `node_timings: {}` to initial state in both `/operate` and `/calculate` endpoints

### 4.5 Telemetry capture in `/operate` endpoint
The `final_state` from `graph.ainvoke()` already contains:
- [X] `final_state["plan"]` → Plan model (`.model_dump()` for serialization)
- [X] `final_state["execution_result"]` → ExecutionResult model
- [X] `final_state["verification_result"]` → VerificationResult model
- [X] `final_state["formatted_response"]` → FormattedResponse model
- [X] `final_state["node_timings"]` → per-node durations

[X] Build `agent_steps` list from these, store in logs table.

### 4.6 `src/deepthought/api/app.py`
- [X] Register new routers: `auth.router` at `/api/v1/auth`, `pairs.router` at `/api/v1/pairs`

### 4.6.1 Deprecation cleanup (after 4.6)
- [X] Remove `DYNAMODB_TABLE_NAME` env var from settings, `.env`, `.env.example`
- [X] Remove the old `/api/v1/tasks/calculate` endpoint and `routes/tasks.py`
- [X] Remove `get_dynamodb_client()` from `dependencies.py` (replaced by table-specific clients)
- [X] Remove `deepthought-calculations` table creation and seed data from `scripts/seed_data.py`
- [X] Remove `TaskRequest`, `TaskResponse`, `CalculationItem` models and their tests
- [X] Update `models/__init__.py`, `models/responses.py`, `models/database.py`
- [X] Update `routes/__init__.py` and `app.py` to remove tasks router
- [X] Update `query_dynamodb` tool to use pairs table
- [X] Update `CLAUDE.md` with new request flow, DynamoDB schema, and env vars
- [X] Add `node_timings` to test helper base state

### 4.7 `src/deepthought/core/exceptions.py`
- [X] Add `AuthenticationError`, `AuthorizationError`, `NotFoundError`

### 4.8 Tests
- [X] New file: `tests/unit/test_auth.py` — password hashing, JWT creation/decoding, get_current_user (18 tests)
- [X] New file: `tests/unit/test_pairs.py` — pair CRUD, operate endpoint, logs retrieval (11 tests)

---

## Phase 5: Frontend Scaffolding + Auth Views

**Goal:** Initialize Next.js app, configure theme system, implement sign in/up.

**Verify:** `cd frontend && npm run dev` — auth page renders, can toggle dark/light mode.

### 5.1 Initialize Next.js
- [X] Next.js 16 with TypeScript, Tailwind CSS 4, App Router, src directory, ESLint
- [X] React Compiler enabled via `babel-plugin-react-compiler` + `reactCompiler: true`
- [X] Standalone output configured for Docker deployment

### 5.2 Install dependencies
- [X] `@tanstack/react-query`, `axios`, `lucide-react`, `next-themes`

### 5.3 Project structure
```
frontend/
  .env                  — environment variables (gitignored)
  .env.example          — environment template (committed)
  .gitignore            — frontend-specific ignores
  Dockerfile            — multi-stage build for production
  eslint.config.mjs     — ESLint with Next.js + TypeScript rules
  next.config.ts        — React Compiler + standalone output
  package.json          — dependencies and scripts
  postcss.config.mjs    — Tailwind CSS PostCSS plugin
  tsconfig.json         — TypeScript configuration
  src/
    app/
      layout.tsx        — root layout with Syne/DM Sans/JetBrains Mono fonts + Providers
      page.tsx          — auth-aware redirect to /auth or /dashboard
      providers.tsx     — ThemeProvider, QueryClientProvider, AuthProvider
      globals.css       — dark cosmic/aurora theme, gradient utilities, noise texture
      favicon.ico       — app icon
      auth/
        page.tsx        — sign in / sign up with aurora background
      dashboard/
        layout.tsx      — auth-guarded shell with navbar
        page.tsx        — placeholder (Phase 6)
      pairs/[pairId]/
        page.tsx        — operations view with telemetry timeline (Phase 7)
    components/
      ui/
        button.tsx      — 3 variants (primary/secondary/ghost), 3 sizes, loading state
        input.tsx       — labeled input with error display
        card.tsx        — with optional gradient border effect
      auth/
        sign-in-form.tsx  — email + password, error handling, redirect on success
        sign-up-form.tsx  — name + email + password, validation, redirect on success
      pairs/              — pair-card, pair-form, operation-button (Phase 6)
      telemetry/          — agent-timeline, step-detail (Phase 7)
      layout/
        navbar.tsx      — Operate+ logo, user name, theme toggle, sign out
        theme-toggle.tsx — sun/moon icon toggle via next-themes
    contexts/
      auth-context.tsx  — React Context: user, token, signUp, signIn, signOut, isLoading
    lib/
      api.ts            — Axios instance with JWT interceptor, baseURL from NEXT_PUBLIC_API_URL
      types.ts          — TypeScript interfaces matching backend models
    hooks/
      use-auth.ts       — hook wrapping auth context
      use-pairs.ts      — React Query hooks for pairs CRUD (Phase 6)
      use-operations.ts — React Query hooks for operate + logs (Phase 7)
```

### 5.4 Auth page design ("Operate+" branding)
- [X] Centered glass-morphic card with gradient border and backdrop blur
- [X] "Operate+" logo with gradient text and accent "+"
- [X] Tab toggle between Sign In and Sign Up forms
- [X] Sign In: email + password inputs, submit button, error handling
- [X] Sign Up: name + email + password inputs, min 8 char validation, error handling
- [X] On success: store JWT in localStorage, redirect to `/dashboard`
- [X] Theme toggle in top-right corner
- [X] Aurora background with animated gradient blobs, grid overlay, noise texture

### 5.5 Theme configuration
- [X] `next-themes` with `attribute="class"`, `defaultTheme="dark"`
- [X] ThemeToggle component with Sun/Moon icons from lucide-react
- [X] Dark cosmic theme: deep navy (#06080f), cyan/violet/fuchsia aurora accents
- [X] Light theme: warm neutrals (#fafbfc), blue/violet/pink accents
- [X] CSS custom properties for surfaces, text, borders, accents, gradients
- [X] Utility classes: gradient-text, gradient-border, glow-surface, noise, shimmer, aurora-blob

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

**Verify:** `docker compose up` — all services start, frontend at :3000, backend at :8080, DynamoDB at :8000, DynamoDB Admin at :8001.

### 8.1 `backend/Dockerfile`
- [X] Python 3.11-slim, pip install from pyproject.toml, copy src/ and scripts/, uvicorn CMD

### 8.2 `frontend/Dockerfile`
- [X] Multi-stage build: node:20-alpine builder (npm ci + build with NEXT_PUBLIC_API_URL arg) → runner (standalone output)
- [X] `output: 'standalone'` configured in `next.config.ts`

### 8.3 `docker-compose.yml`
- [X] `dynamodb-local` — DynamoDB Local on :8000 with healthcheck
- [X] `dynamodb-admin` — DynamoDB Admin GUI on :8001 with AWS creds from backend/.env
- [X] `seed` — runs seed_data.py after DynamoDB is healthy
- [X] `backend` — FastAPI on :8080, depends on seed completion
- [X] `frontend` — Next.js on :3000, NEXT_PUBLIC_API_URL from frontend/.env
- [X] All services on `deepthought` bridge network
- [X] All env vars sourced from backend/.env and frontend/.env (no hardcoded values)

### 8.4 Monorepo restructuring
- [X] Backend moved into `backend/` directory (src/, tests/, scripts/, pyproject.toml, .env)
- [X] Per-directory `.gitignore` files for independent deployability
- [X] `backend/documentation/` directory for design docs

---

## Phase 9: Makefile Updates

**Goal:** New commands for full-stack build/run/dev workflow.

### 9.1 `Makefile`
- [X] `COMPOSE` variable with `--env-file ./backend/.env --env-file ./frontend/.env`
- [X] `make build` — `docker compose build`
- [X] `make up` — build + up -d + print service URLs (frontend, backend, API docs, DynamoDB, DynamoDB GUI)
- [X] `make down` — `docker compose down`
- [X] `make database` — DynamoDB Local only
- [X] `make seed` — database + seed via Docker
- [X] `make dev` — DynamoDB + seed + backend (uvicorn --reload) + frontend (npm run dev)
- [X] `make frontend-dev` — `cd frontend && npm run dev`
- [X] `make test` — `cd backend && pytest`
- [X] `make lint` — `cd backend && ruff check + format --check + mypy`

---

## Phase 10: Integration Testing + Polish

**Goal:** End-to-end tests, documentation, edge case handling.

### 10.1 New file: `backend/tests/integration/test_api_flow.py`
- Full flow: signup → signin → create pair → operate (all 4 ops) → get logs
- Auth edge cases: duplicate signup (409), wrong password (401), expired JWT
- Ownership: user A cannot access user B's pairs

### 10.2 Update `CLAUDE.md` and `README.md`
- [X] CLAUDE.md updated with monorepo structure, new paths, Docker services
- New architecture diagram, API endpoints, frontend info

### 10.3 Update `.env.example`
- [X] Backend `.env.example` has all table names, JWT settings
- [X] Frontend `.env.example` has NEXT_PUBLIC_API_URL

### 10.4 Update `.gitignore`
- [X] Per-directory .gitignore files for backend/ and frontend/
- [X] Root .gitignore covers only IDE and OS files

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

**Monorepo structure:**
```
DeepThought/
  .gitignore              — IDE + OS ignores only
  CLAUDE.md               — project instructions
  Makefile                — full-stack build/run/dev commands
  docker-compose.yml      — all services orchestration
  plan.md                 — this file
  README.md
  backend/
    .gitignore            — Python-specific ignores
    .env / .env.example   — backend environment config
    Dockerfile            — backend container
    pyproject.toml        — Python deps + tool config
    documentation/        — design docs
    scripts/              — seed_data.py
    src/deepthought/      — FastAPI + LangGraph source
    tests/                — pytest unit + integration tests
  frontend/
    .gitignore            — Node/Next.js-specific ignores
    .env / .env.example   — frontend environment config
    Dockerfile            — frontend container (multi-stage)
    package.json          — Node deps + scripts
    next.config.ts        — React Compiler + standalone output
    src/                  — Next.js App Router source
```

**Deleted files:** `scripts/setup_ollama.py`, old root-level config files (moved to backend/)
