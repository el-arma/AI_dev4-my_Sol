*S04E03 - Domatowo*

**Stack:**
Backend: Python, PydanticAI, asyncio  
Observability: Logfire  
Developer Tools: uv, Git, GitHub

**LLM Providers**
* Anthropic (claude-sonnet-4-6)

**What's new:**
* HIL (Human-in-the-Loop) decorator: wraps tool calls with a human approval gate — agent must get permission before any action executes
* AP budget planning: system prompt includes a cost-per-action table and a budget template; agent is forced to plan before spending
* Tactical unit coordination: transporters carry scouts cheaply along streets, scouts inspect on foot only at the destination

**Solution architecture:**
1. `main.py` — Agent Smith entry point: single-run agentic workflow with Logfire observability
2. `suit.py` — Tools: `task_result_verification` (write/verify) + `HIL` decorator (human approval gate) + `wait_for_API` (rate-limit handler)
3. `prompts_lib.py` — System prompt: tactical search-and-rescue workflow with AP budget template and decision rules
4. `schemas.py` — Pydantic schemas: TaskResultRequest
5. `session.py` — ContextSessionManager: shared execution context across tool calls
6. `token_tracker.py` — CostTracker: per-model token & USD accounting, auto-saves cost log

**What I practiced / learned:**
* Human-in-the-Loop (HIL): wrapping agent tools with a human approval gate — agent proposes, human approves or redirects
* Resource-constrained agentic planning: 300 AP budget forces the agent to reason about cost before acting, not after
* Game-like API interaction: agent coordinates units (transporters + scouts) via structured JSON actions against a stateful server

**Task completion details:**
* Claude-Sonnet-4-6
* Input tokens (IT): 182k
* Output tokens (OT): 8.45k
* Requests: 18
* Full Task Completion Cost: $0.674


# IDEA:
Sub-AGENT PER QUANDRANT