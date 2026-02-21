# DeepThought v2 — Productivity Suite Feature Plan

> **Internal plan reference**: This plan is also stored at `.claude/plans/shiny-bouncing-scott.md` for use with Claude Code plan mode execution.

---

# DeepThought Productivity Suite — Implementation Plan

## Context

DeepThought is currently a calculation-only agent demo (pairs + math operations via a LangGraph pipeline). The goal is to expand it into a full AI-powered productivity suite with **Calendar**, **Todo Lists**, and a **Conversational AI Chat Sidebar** ("Chat with Plus+"), while keeping the existing pairs/calculation functionality intact.

Key architectural decisions:
- **Hybrid RAG** via Pinecone Inference — `llama-text-embed-v2` dense + `pinecone-sparse-english-v0` sparse embeddings with local FlashRank cross-encoder reranking
- **Separate LangGraph graphs per domain** — independent, testable, evolvable
- **Google Gemini** for all agents (current provider)
- **Recurring + one-off calendar events** using RRULE (RFC 5545)
- **ISO 8601 timestamps with offset**, displayed in user's local timezone
- **Left sidebar + top bar** navigation layout
- **Separate landing page** at `/` linking to `/auth`
- **Persisted chat conversations** in DynamoDB
- **Per-feature gamification stats** (no central dashboard)
- **User-first UI** — manual CRUD for calendar/todos before agent layer

---

## Phase 1: Data Layer & Infrastructure Foundation

**Objective**: New DynamoDB tables, Pydantic models, Pinecone config, DynamoDB client enhancements, seed updates. No endpoints or UI.

### 1.1: DynamoDB Table Schemas [X]

- [X] **`deepthought-calendar`** (dedicated table — no sk prefix needed)
  - `pk` = user_email, `sk` = `{ISO_start_time}#{event_id}` (time-based sk for efficient range queries + event_id suffix for uniqueness when events share a start time)
  - Attributes: `event_id`, `title`, `description`, `start_time` (ISO 8601 w/ offset), `end_time` (ISO 8601 w/ offset), `rrule` (RFC 5545 string or null), `created_at`, `updated_at`
  - Range queries use `sk BETWEEN '2026-02-10' AND '2026-02-17'` for date-range lookups at the DB level
- [X] **`deepthought-todos`** (single-table design — lists + items coexist, sk prefixes required to distinguish entity types)
  - `pk` = user_email for both entity types
  - **Todo lists**: `sk` = `LIST#{list_id}` — Attributes: `list_id`, `title`, `created_at`, `updated_at`
  - **Todo items**: `sk` = `ITEM#{list_id}#{item_id}` — Attributes: `item_id`, `list_id`, `text`, `completed` (bool), `completed_at` (ISO 8601 or null), `sort_order` (int), `created_at`, `updated_at`
  - **GSI**: `pk_completed_at_index` — GSI pk=`user_email`, sk=`completed_at`. Only items with `completed_at` set are projected. Used for 10-day rolling stats query (`completed_at BETWEEN ...`).
  - Benefits: co-located data for list+items reads, single DI client, efficient `begins_with(sk, 'ITEM#{list_id}')` queries
- [X] **`deepthought-conversations`** (dedicated table — no sk prefix needed)
  - `pk` = user_email, `sk` = `{created_at}#{conversation_id}` (chronological ordering by default + conversation_id suffix for uniqueness)
  - Attributes: `conversation_id`, `context_type` (`"pairs"` | `"calendar"` | `"todos"` | `"general"`), `title`, `created_at`, `updated_at`
  - Conversations sort by `created_at` in DynamoDB results; for "most recent activity" ordering, sort by `updated_at` in application code (conversation counts per user are small)
- [X] **`deepthought-messages`** (dedicated table — no sk prefix needed)
  - `pk` = conversation_id, `sk` = `{created_at}#{message_id}` (chronological ordering + message_id suffix for uniqueness when messages arrive at the same millisecond)
  - Attributes: `message_id`, `conversation_id`, `role` (`"user"` | `"assistant"`), `content`, `tool_calls` (list[dict] or null), `created_at`

### 1.2: Pydantic Models [X]

**Create files:**
- [X] `backend/src/deepthought/models/calendar.py` — `CalendarEvent`, `CalendarEventCreate`, `CalendarEventUpdate`, `CalendarEventResponse`
- [X] `backend/src/deepthought/models/todos.py` — `TodoList`, `TodoListCreate`, `TodoListResponse`, `TodoItem`, `TodoItemCreate`, `TodoItemUpdate`, `TodoItemResponse`
- [X] `backend/src/deepthought/models/chat.py` — `Conversation`, `ConversationCreate`, `ConversationResponse`, `ChatMessage`, `ChatMessageCreate`, `ChatMessageResponse`, `ChatRequest`, `ChatResponse`
- [X] `backend/src/deepthought/models/stats.py` — `DailyCount`, `StatsResponse`

Follow existing patterns from `models/pairs.py` and `models/logs.py`: `BaseModel` with `Field(...)` descriptors, `int | float` unions, `datetime` types.

### 1.3: Settings & Environment [X]

**Modify** `backend/src/deepthought/config/settings.py` — add fields:
```python
# New DynamoDB tables
dynamodb_calendar_table: str
dynamodb_todos_table: str  # single table for lists + items
dynamodb_conversations_table: str
dynamodb_messages_table: str

# Pinecone (required)
pinecone_api_key: str
pinecone_index_name: str = "deepthought-rag"
```

**Update** `backend/.env.example` with all new env vars:
```
DYNAMODB_CALENDAR_TABLE=deepthought-calendar
DYNAMODB_TODOS_TABLE=deepthought-todos
DYNAMODB_CONVERSATIONS_TABLE=deepthought-conversations
DYNAMODB_MESSAGES_TABLE=deepthought-messages
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=deepthought-hybrid-rag
```

### 1.4: DynamoDB Client Enhancements [X]

**Modify** `backend/src/deepthought/db/client.py` — add methods:
- [X] `update_item(pk, sk, updates, return_values)` — partial attribute update via `UpdateExpression` with `SET` clauses
- [X] `delete_item(pk, sk)` — delete by primary key (pk + sk)
- [X] `batch_delete(items: list[tuple[str, str]])` — batch delete via `BatchWriteItem` (for deleting a todo list + all its items; handles DynamoDB's 25-item batch limit internally)
- [X] `query_between(pk, sk_start, sk_end)` — range query with `sk BETWEEN :start AND :end` for calendar date-range lookups
- [X] `query_count(pk, sk_prefix)` — count query using `Select='COUNT'` for stats
- [X] `query_gsi_range(index_name, pk_attr, pk_value, sk_attr, sk_start, sk_end)` — GSI range query for completed_at on todos

### 1.5: Dependency Injection [X]

**Modify** `backend/src/deepthought/api/dependencies.py` — add DI functions:
- [X] `get_calendar_db_client()` — for `deepthought-calendar` table
- [X] `get_todos_db_client()` — for `deepthought-todos` table (single client for lists + items)
- [X] `get_conversations_db_client()` — for `deepthought-conversations` table
- [X] `get_messages_db_client()` — for `deepthought-messages` table

Following the exact `get_pairs_db_client()` pattern (4 new functions, not 5 — todos is one table).

### 1.6: Seed Script Update [X]

**Modify** `backend/scripts/setup_dynamodb.py`:
- [X] Add `create_table()` calls for all 4 new tables (composite key)
- [X] Add GSI creation for `deepthought-todos` table (`pk_completed_at_index`)
- [X] ~~Add `seed_calendar()` — 3 sample events for test user (one recurring with rrule `FREQ=WEEKLY;BYDAY=MO,WE,FR`)~~ (skipped — not seeding data)
- [X] ~~Add `seed_todos()` — 1 todo list with 3 items (1 completed with `completed_at` set)~~ (skipped — not seeding data)

### 1.7: Pinecone Setup Script

**Create** `backend/scripts/setup_pinecone.py`:
- Creates the Pinecone index if it doesn't exist
- Config: 1024 dimensions (`llama-text-embed-v2` default), **dotproduct** metric (required for hybrid search with sparse+dense)
- Logs success/already-exists status

**Add** `make setup-pinecone` target to Makefile (separate from `make seed`).

### 1.8: Python Dependencies

**Modify** `backend/pyproject.toml` — add to dependencies:
```
"pinecone-client>=3.0.0"
"python-dateutil>=2.8.0"
"flashrank>=0.2.0"
```

Add to mypy overrides (ignore_missing_imports):
```
"pinecone.*"
"flashrank.*"
```

Note: No `langchain-pinecone`, `langchain-google-genai`, or `pinecone-text` needed — Pinecone Inference handles both dense (`llama-text-embed-v2`) and sparse (`pinecone-sparse-english-v0`) embeddings natively via the `pinecone-client` SDK.

---

## Phase 2: Calendar & Todo REST APIs

**Objective**: CRUD endpoints for calendar events and todo lists/items, plus stats endpoints. No chat agent yet.

**Depends on**: Phase 1

### 2.1: Calendar Routes

**Create** `backend/src/deepthought/api/routes/calendar.py`

Endpoints:
- `POST /api/v1/calendar/` — create event → `CalendarEventResponse` (201)
- `GET /api/v1/calendar/?start=...&end=...` — list events in date range (expands RRULE instances within range using `python-dateutil`)
- `GET /api/v1/calendar/{event_id}` — get single event
- `PATCH /api/v1/calendar/{event_id}` — update event
- `DELETE /api/v1/calendar/{event_id}` — delete event (204)

All require JWT auth via `get_current_user`.

### 2.2: Todo Routes

**Create** `backend/src/deepthought/api/routes/todos.py`

Endpoints:
- `POST /api/v1/todos/lists` — create todo list → `TodoListResponse` (201)
- `GET /api/v1/todos/lists` — list all todo lists (with item/completed counts)
- `DELETE /api/v1/todos/lists/{list_id}` — delete list + all items (204)
- `POST /api/v1/todos/lists/{list_id}/items` — add item → `TodoItemResponse` (201)
- `GET /api/v1/todos/lists/{list_id}/items` — list items for a list
- `PATCH /api/v1/todos/lists/{list_id}/items/{item_id}` — update item (toggle complete, edit text)
- `DELETE /api/v1/todos/lists/{list_id}/items/{item_id}` — delete item (204)

### 2.3: Stats Routes

**Create** `backend/src/deepthought/api/routes/stats.py`

Endpoints:
- `GET /api/v1/stats/pairs` — total pairs + 10-day rolling daily insertion counts
- `GET /api/v1/stats/todos` — total lists + 10-day rolling daily completed task counts

### 2.4: Route Registration

**Modify** `backend/src/deepthought/api/app.py` — register new routers:
```python
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(todos.router, prefix="/api/v1/todos", tags=["todos"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
```

### 2.5: Tests

- `backend/tests/unit/test_calendar.py` — CRUD handlers with mocked DB
- `backend/tests/unit/test_todos.py` — CRUD handlers with mocked DB
- `backend/tests/unit/test_stats.py` — stats computation logic
- `backend/tests/integration/test_calendar_flow.py` — full HTTP CRUD flow
- `backend/tests/integration/test_todos_flow.py` — full HTTP CRUD flow

---

## Phase 3: Frontend — Navigation, Landing Page & Calendar/Todo UIs

**Objective**: Restructure frontend layout (sidebar + top bar), create landing page, build calendar and todo UI components, and wire them to Phase 2 backend APIs for user-initiated CRUD. Users can manually create events, manage todo lists, and complete items without any agent involvement.

**Depends on**: Phase 2 (backend APIs)

### 3.1: Route Restructure

New route structure:
```
/                              → Landing page (unauthenticated)
/auth                          → Sign in / Sign up (existing)
/(authenticated)/pairs         → Pairs dashboard (moved from /dashboard)
/(authenticated)/pairs/[pairId] → Pair detail
/(authenticated)/calendar      → Calendar view
/(authenticated)/todos         → Todo lists view
/dashboard                     → Redirect to /pairs (backward compat)
```

Using a `(authenticated)` route group to share sidebar layout.

### 3.2: Sidebar Component

**Create** `frontend/src/components/layout/sidebar.tsx`
- Fixed left sidebar, narrow icon-only rail
- 3 icon buttons (lucide-react), vertically stacked:
  - **Pairs**: `Layers` icon — stacked layers convey paired data
  - **Calendar**: `CalendarDays` icon — calendar grid with day numbers, immediately recognizable
  - **Todos**: `ListChecks` icon — checklist with checkmarks, clearly communicates task management
- Active state: accent-muted background + accent text
- Tooltip on hover showing label ("Pairs", "Calendar", "Todos")
- Matches glassmorphism aesthetic (backdrop-blur, subtle border)
- No logo — logo stays on navbar

### 3.3: Top Bar Update

**Modify** `frontend/src/components/layout/navbar.tsx`
- Logo remains as-is ("Operate+" gradient text, links to /pairs)
- Keep: user first name, "Chat with Plus+" button (right side), theme toggle, sign out
- "Chat with Plus+" button is visible but disabled until Phase 5 (chat sidebar)

### 3.4: Authenticated Layout

**Create** `frontend/src/app/(authenticated)/layout.tsx`
- Auth guard (redirect to /auth if unauthenticated)
- Renders: `<Sidebar />` + content area offset by sidebar width
- `<Navbar />` at top of content area

### 3.5: Landing Page

**Rewrite** `frontend/src/app/page.tsx`
- Hero section: "Operate+" title, tagline, "Get Started" CTA → `/auth`
- 3 feature cards: Pairs, Calendar, Todos (with icons and descriptions)
- If authenticated, redirect to `/pairs`
- Aurora aesthetic with grid overlay matching auth page style

### 3.6: Move Existing Pages

- Move `dashboard/page.tsx` content → `(authenticated)/pairs/page.tsx`
- Move `pairs/[pairId]/page.tsx` → `(authenticated)/pairs/[pairId]/page.tsx`
- Create `dashboard/page.tsx` as redirect stub → `/pairs`

### 3.7: TypeScript Types & Hooks

**Modify** `frontend/src/lib/types.ts` — add interfaces for CalendarEvent, TodoList, TodoItem, Stats, etc.

**Create hooks:**
- `frontend/src/hooks/use-calendar.ts` — `useCalendarEvents(start, end)`, `useCreateEvent()`, `useUpdateEvent()`, `useDeleteEvent()`
- `frontend/src/hooks/use-todos.ts` — `useTodoLists()`, `useCreateTodoList()`, `useTodoItems(listId)`, `useCreateTodoItem()`, `useUpdateTodoItem()`, `useDeleteTodoItem()`
- `frontend/src/hooks/use-stats.ts` — `usePairsStats()`, `useTodosStats()`

Note: Chat-related types and hooks (`use-chat.ts`, Conversation, ChatMessage interfaces) are deferred to Phase 5 when the chat API exists.

### 3.8: Calendar View

**Calendar approach**: Build a custom calendar grid matching the aurora aesthetic. Use `date-fns` for date math. Custom is preferred over a library to maintain full design control.

**Create** `frontend/src/components/calendar/` directory:
- `calendar-header.tsx` — prev/next navigation, view mode toggle (day/week/month), current date display
- `calendar-view.tsx` — main orchestrator component, renders appropriate grid based on view mode
- `week-view.tsx` — 7-column time grid with hourly rows, events positioned by time
- `day-view.tsx` — single-column time grid
- `month-view.tsx` — traditional month grid with event dots/pills
- `event-card.tsx` — individual event rendering in the grid (gradient accent styling)
- `event-form-modal.tsx` — modal for creating/editing events with title, description, date/time pickers, recurrence picker
- `recurrence-picker.tsx` — dropdown for common recurrence patterns (daily, weekly, monthly, custom)

**Implement** `frontend/src/app/(authenticated)/calendar/page.tsx` — fully wired to Phase 2 calendar API via `use-calendar` hooks.

### 3.9: Todo View

**Create** `frontend/src/components/todos/` directory:
- `todo-list-card.tsx` — clickable card showing list title + item count badge; expands on click
- `todo-item-row.tsx` — checkbox + text; CSS transitions for check animation (slide to bottom, opacity → 0.4)
- `create-list-form.tsx` — inline form for new list creation
- `add-item-form.tsx` — inline form at bottom of expanded list

**Implement** `frontend/src/app/(authenticated)/todos/page.tsx` — fully wired to Phase 2 todos API via `use-todos` hooks.

Completed item animation:
```css
.todo-item-completed {
  opacity: 0.4;
  transition: opacity 0.3s ease, transform 0.3s ease;
}
```
Sort completed items to end in render logic.

---

## Phase 4: Chat Agent with Hybrid RAG

**Objective**: Conversational chat agent with domain-specific tools and hybrid RAG retrieval via Pinecone Inference (dense + sparse) with local FlashRank cross-encoder reranking.

**Depends on**: Phase 2 (backend APIs for tools to call)

### 4.1: RAG Infrastructure

**Create** `backend/src/deepthought/rag/` package:

- `embeddings.py` — Dual encoding via Pinecone Inference API:
  - `get_pinecone_client()` — cached Pinecone client instance
  - `embed_dense(texts, input_type)` — calls Pinecone Inference with model `llama-text-embed-v2` (1024-dim dense vectors); `input_type` is `"query"` or `"passage"`
  - `embed_sparse(texts, input_type)` — calls Pinecone Inference with model `pinecone-sparse-english-v0` (DeepImpact-based whole-word tokenization, no corpus fitting); `input_type` is `"query"` or `"passage"`
  - `embed_hybrid(texts, input_type)` → returns list of `(dense_vector, sparse_vector)` tuples
  - All embedding runs through Pinecone's hosted infrastructure — no local model downloads, no GPU required

- `vectorstore.py` — Hybrid Pinecone operations:
  - `get_pinecone_index()` — returns Pinecone index client
  - `upsert_hybrid(id, dense_vector, sparse_vector, metadata, namespace)` — upserts a single vector with both dense and sparse representations
  - `upsert_hybrid_batch(items, namespace)` — batch upsert for indexing
  - `query_hybrid(dense_vector, sparse_vector, namespace, top_k, alpha, filter)` — Pinecone hybrid search combining sparse (`pinecone-sparse-english-v0`) and dense (`llama-text-embed-v2`) with alpha-weighted interpolation (`alpha=0.7` default: 70% semantic, 30% keyword)
  - `delete_vectors(ids, namespace)` — delete by vector IDs
  - Pinecone index: 1024 dimensions, **dotproduct** metric (required for hybrid)
  - Namespaces: `calendar`, `todos`, `chat`, `pairs`
  - Metadata: `user_email`, `content_type`, `entity_id`, `timestamp`, `text`

- `reranker.py` — Local cross-encoder reranking:
  - `get_reranker()` — returns cached `flashrank.Ranker(model_name="ms-marco-MiniLM-L-12-v2")` instance (ONNX-optimized BERT cross-encoder, ~50ms for 100 passages on CPU, free)
  - `rerank(query, candidates, top_k)` → re-scores candidate documents by jointly encoding (query, document) pairs, returns top_k reranked results
  - Input: raw Pinecone results (~20 candidates from hybrid search)
  - Output: final top_k most relevant documents (default top_k=5)
  - Note: can be swapped to Pinecone's `bge-reranker-v2-m3` in the future if server-side reranking is preferred

- `indexer.py` — Fire-and-forget indexing hooks called from route handlers:
  - `index_calendar_event()`, `remove_calendar_event()`
  - `index_todo_item()`, `remove_todo_item()`
  - `index_chat_message()`
  - Each generates both dense + sparse embeddings via Pinecone Inference before upserting
  - Called via `asyncio.create_task()` after DB writes (non-blocking)

**RAG Pipeline (3 stages)**:
```
Stage 1: Pinecone hybrid search
         pinecone-sparse-english-v0 sparse + llama-text-embed-v2 dense
         Alpha-weighted interpolation (0.7 semantic / 0.3 keyword)
         Returns ~20 candidate documents

Stage 2: FlashRank local cross-encoder reranking
         ms-marco-MiniLM-L-12-v2 (ONNX, CPU-friendly, free)
         Re-scores candidates with joint query+doc encoding
         Returns top 5 most relevant

Stage 3: Context injection into Gemini
         Reranked documents provided as context in system prompt
         LLM generates response with tool access
```

### 4.2: Chat Domain Tools

**Create** `backend/src/deepthought/tools/calendar_tools.py`:
- `create_calendar_event(title, start_time, end_time, description, rrule)` — @tool
- `list_upcoming_events(days_ahead)` — @tool
- `delete_calendar_event(event_id)` — @tool

**Create** `backend/src/deepthought/tools/todo_tools.py`:
- `create_todo_list(title)` — @tool
- `add_todo_item(list_id, text)` — @tool
- `complete_todo_item(list_id, item_id)` — @tool
- `list_todo_lists()` — @tool
- `list_todo_items(list_id)` — @tool

**Create** `backend/src/deepthought/tools/pair_tools.py`:
- `create_pair(val1, val2)` — @tool
- `list_pairs()` — @tool

**Create** `backend/src/deepthought/tools/chat_tool_factory.py`:
- `get_tools_for_context(context_type, user_email, db_clients)` — returns domain-appropriate tools with DB clients bound via factory/partial pattern

### 4.3: Chat Agent LangGraph

**Create** `backend/src/deepthought/agents/chat/` package:

**`state.py`** — `ChatAgentState(TypedDict)`:
- `user_email`, `conversation_id`, `context_type`, `user_message`
- `retrieved_context: list[dict]`
- `messages: Annotated[list[BaseMessage], add_messages]`
- `assistant_response: str | None`
- `tool_calls_made: list[dict]`
- `current_step`, `error`

**`graph.py`** — Simpler 2-node graph:
```
START → retrieval → reasoning → END
```
- `create_chat_graph()` → `StateGraph[ChatAgentState]`
- `compile_chat_graph()` → `CompiledStateGraph`

**`nodes/retrieval.py`** — Hybrid retrieval pipeline:
1. Embeds user message via Pinecone Inference (dense + sparse, `input_type="query"`)
2. Queries Pinecone with hybrid search across relevant namespaces (filtered by `user_email`, alpha=0.7)
3. Reranks top ~20 candidates via local FlashRank cross-encoder → top 5
4. Loads last 20 conversation messages for multi-turn context

**`nodes/reasoning.py`** — Builds system prompt with reranked context, binds domain tools based on `context_type`, runs LLM with tool-calling loop (max 5 iterations), extracts final text response.

**`prompts.py`** — System prompts for the "Plus+" chat assistant, with context-specific tool instructions.

### 4.4: Chat API Route

**Create** `backend/src/deepthought/api/routes/chat.py`

Endpoints:
- `POST /api/v1/chat/` — send message → `ChatResponse` (conversation_id + assistant reply)
  - Creates or retrieves conversation
  - Stores user message in DynamoDB
  - Loads conversation history
  - Invokes chat graph (hybrid retrieval → reranking → reasoning)
  - Stores assistant response
  - Indexes messages in Pinecone via Inference API (fire-and-forget)
- `GET /api/v1/chat/conversations` — list user's conversations
- `GET /api/v1/chat/conversations/{conversation_id}/messages` — get messages for a conversation

**Modify** `backend/src/deepthought/api/dependencies.py`:
- Add `get_chat_graph()` — LRU-cached compiled chat graph

**Register** in `app.py`:
```python
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
```

### 4.5: Tests

- `backend/tests/unit/test_chat_graph.py` — retrieval + reasoning nodes with mocked LLM/Pinecone
- `backend/tests/unit/test_chat_tools.py` — calendar, todo, pair tools with mocked DB
- `backend/tests/unit/test_rag.py` — Pinecone Inference embedding calls, hybrid vectorstore query, FlashRank reranking with mocked dependencies
- `backend/tests/integration/test_chat_flow.py` — full chat endpoint with mocked LLM

---

## Phase 5: Chat Sidebar & Gamification Stats

**Objective**: Sliding chat panel wired to Phase 4 chat API, and rolling bar charts for gamification stats. This is where the agent becomes accessible to the user — the "Chat with Plus+" button becomes functional.

**Depends on**: Phase 3 (frontend pages), Phase 4 (chat API)

### 5.1: Chat Types & Hooks

**Modify** `frontend/src/lib/types.ts` — add Conversation, ChatMessage interfaces.

**Create hooks:**
- `frontend/src/hooks/use-chat.ts` — `useConversations()`, `useChatMessages(convId)`, `useSendMessage()`

### 5.2: Chat Sidebar

**Create** `frontend/src/contexts/chat-context.tsx`:
- `ChatProvider` managing: `isOpen`, `contextType`, `conversationId`
- `open(contextType)`, `close()` methods
- Context type auto-detected from current route

**Create** `frontend/src/components/chat/` directory:
- `chat-panel.tsx` — fixed right-side panel (w-96), slides in/out with `translate-x` transition, glassmorphism styling, z-50
- `chat-message.tsx` — message bubble (user: right-aligned accent, assistant: left-aligned surface-elevated)
- `chat-input.tsx` — text input with send button at bottom of panel

**Modify** `frontend/src/app/providers.tsx` — wrap with `ChatProvider`

**Modify** `frontend/src/components/layout/navbar.tsx` — enable "Chat with Plus+" button (was disabled in Phase 3), wire to chat context `open()`.

**Integration**: Navbar "Chat with Plus+" button opens panel. Panel context-type determined by current route pathname.

### 5.3: Gamification Stats

**Install** `recharts` in frontend.

**Create** `frontend/src/components/stats/`:
- `rolling-bar-chart.tsx` — `ResponsiveContainer` + `BarChart` with 10 bars, accent-colored, rounded tops, minimal axis
- `stat-badge.tsx` — glassmorphism card with large gradient number + muted label

**Integrate**:
- Pairs page (`(authenticated)/pairs/page.tsx`): stat badge (total pairs) + bar chart (10-day insertions) at top
- Todos page (`(authenticated)/todos/page.tsx`): stat badge (total lists) + bar chart (10-day completions) at top

---

## Phase 6: Infrastructure, Docker & Final Testing

**Objective**: Update Docker config, environment files, and comprehensive test coverage.

**Depends on**: All previous phases

### 6.1: Docker & Environment

**Modify** `docker-compose.yml`:
- Add new env vars to backend service (calendar/todo/conversation/message table names, Pinecone config)
- No new services needed (Pinecone is managed cloud, FlashRank runs embedded on CPU)

**Update** `backend/.env.example` and `frontend/.env.example` with documentation.

### 6.2: Seed Script Finalization

Ensure `setup_dynamodb.py` creates all 7 tables (3 original + 4 new) with GSI on todos, and seeds sample data across all entity types.

### 6.3: Backend Test Suite

All new unit + integration tests from Phases 2.5 and 4.5. Target: maintain the pattern of comprehensive mocked tests.

### 6.4: Frontend Build Verification

Ensure `npm run build` passes with all new components. This is the existing `make test-frontend` strategy.

---

## Verification Plan

### End-to-End Testing Checklist

1. **`make build && make up`** — all containers start, all 7 DynamoDB tables created (with GSI on todos), seed data populated
2. **Auth flow** — sign up, sign in, JWT works across all new endpoints
3. **Calendar CRUD** — create event via UI, list events by date range, update, delete. Verify RRULE expansion.
4. **Todo CRUD** — create list via UI, add items, toggle completion, delete. Verify item counts.
5. **Chat flow** — send message in each context (pairs, calendar, todos), verify hybrid RAG retrieval (Pinecone Inference dense + sparse + FlashRank reranking), tool calls, persisted conversation
6. **Stats** — verify rolling 10-day counts for pairs insertions and todo completions
7. **Frontend navigation** — sidebar links work, top bar renders, pages load
8. **Chat sidebar** — opens from each page with correct context, sends messages, displays responses
9. **Gamification** — bar charts render with correct data on pairs and todos pages
10. **Landing page** — renders for unauthenticated users, "Get Started" → `/auth`
11. **`make test`** — all backend tests pass, frontend builds successfully
12. **`make lint`** — ruff + mypy pass on all new code

---

## File Inventory

### New Backend Files (~24)
```
backend/scripts/setup_pinecone.py
backend/src/deepthought/models/calendar.py
backend/src/deepthought/models/todos.py
backend/src/deepthought/models/chat.py
backend/src/deepthought/models/stats.py
backend/src/deepthought/api/routes/calendar.py
backend/src/deepthought/api/routes/todos.py
backend/src/deepthought/api/routes/stats.py
backend/src/deepthought/api/routes/chat.py
backend/src/deepthought/rag/__init__.py
backend/src/deepthought/rag/embeddings.py
backend/src/deepthought/rag/vectorstore.py
backend/src/deepthought/rag/reranker.py
backend/src/deepthought/rag/indexer.py
backend/src/deepthought/agents/chat/__init__.py
backend/src/deepthought/agents/chat/state.py
backend/src/deepthought/agents/chat/graph.py
backend/src/deepthought/agents/chat/nodes/__init__.py
backend/src/deepthought/agents/chat/nodes/retrieval.py
backend/src/deepthought/agents/chat/nodes/reasoning.py
backend/src/deepthought/agents/chat/prompts.py
backend/src/deepthought/tools/calendar_tools.py
backend/src/deepthought/tools/todo_tools.py
backend/src/deepthought/tools/pair_tools.py
backend/src/deepthought/tools/chat_tool_factory.py
```

### Modified Backend Files (~7)
```
backend/src/deepthought/config/settings.py
backend/src/deepthought/api/dependencies.py
backend/src/deepthought/api/app.py
backend/src/deepthought/db/client.py
backend/scripts/setup_dynamodb.py
backend/pyproject.toml
Makefile (add setup-pinecone target)
```

### New Frontend Files (~25)
```
frontend/src/app/(authenticated)/layout.tsx
frontend/src/app/(authenticated)/pairs/page.tsx
frontend/src/app/(authenticated)/pairs/[pairId]/page.tsx
frontend/src/app/(authenticated)/calendar/page.tsx
frontend/src/app/(authenticated)/todos/page.tsx
frontend/src/app/dashboard/page.tsx (redirect stub)
frontend/src/components/layout/sidebar.tsx
frontend/src/components/calendar/calendar-header.tsx
frontend/src/components/calendar/calendar-view.tsx
frontend/src/components/calendar/week-view.tsx
frontend/src/components/calendar/day-view.tsx
frontend/src/components/calendar/month-view.tsx
frontend/src/components/calendar/event-card.tsx
frontend/src/components/calendar/event-form-modal.tsx
frontend/src/components/calendar/recurrence-picker.tsx
frontend/src/components/todos/todo-list-card.tsx
frontend/src/components/todos/todo-item-row.tsx
frontend/src/components/todos/create-list-form.tsx
frontend/src/components/todos/add-item-form.tsx
frontend/src/components/chat/chat-panel.tsx
frontend/src/components/chat/chat-message.tsx
frontend/src/components/chat/chat-input.tsx
frontend/src/components/stats/rolling-bar-chart.tsx
frontend/src/components/stats/stat-badge.tsx
frontend/src/contexts/chat-context.tsx
frontend/src/hooks/use-calendar.ts
frontend/src/hooks/use-todos.ts
frontend/src/hooks/use-chat.ts
frontend/src/hooks/use-stats.ts
```

### Modified Frontend Files (~5)
```
frontend/src/app/page.tsx (rewrite as landing page)
frontend/src/app/providers.tsx
frontend/src/components/layout/navbar.tsx
frontend/src/lib/types.ts
frontend/package.json
```

### New Test Files (~10)
```
backend/tests/unit/test_calendar.py
backend/tests/unit/test_todos.py
backend/tests/unit/test_stats.py
backend/tests/unit/test_chat_graph.py
backend/tests/unit/test_chat_tools.py
backend/tests/unit/test_rag.py
backend/tests/integration/test_calendar_flow.py
backend/tests/integration/test_todos_flow.py
backend/tests/integration/test_chat_flow.py
```
