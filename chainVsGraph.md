# LangChain vs LangGraph in DeepThought

## LangChain — the toolkit layer

LangChain provides the building blocks each agent node uses:

- **LLM abstraction** (`BaseChatModel`, `ChatGoogleGenerativeAI`) — the interface to call Google Gemini. Used in the orchestrator node to generate plans via `llm.ainvoke(messages)`.
- **Tool definitions** (`@tool` decorator + Pydantic input schemas) — wraps our functions (`add_values`, `query_dynamodb`, `verify_addition`, `format_json`, etc.) into a standard interface that can be invoked with `.invoke()` / `.ainvoke()`.
- **Message types** (`HumanMessage`, `AIMessage`, `BaseMessage`) — the structured message objects passed to/from the LLM and stored in state.

## LangGraph — the orchestration layer

LangGraph defines *how* the agents flow together as a state machine:

- **`StateGraph`** — declares the graph with 4 nodes (orchestrator, execution, verification, response) and the edges between them.
- **`AgentState` (TypedDict)** — the shared state that flows through every node. Each node reads from it and returns partial updates.
- **`add_messages` reducer** — automatically merges new messages into the message history.
- **Conditional edges + routing functions** — control flow logic: retry execution up to 3 times, retry verification up to 2 times, route errors to response.
- **`CompiledStateGraph`** — the compiled, executable graph invoked with `await graph.ainvoke(initial_state)` in the API route.

## In short

**LangChain** = what each agent *uses* (LLM calls, tools, messages).
**LangGraph** = how agents *connect* (state machine, routing, retries).
