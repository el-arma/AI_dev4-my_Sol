*S04E02 - Wind Power Scheduler*

**Stack:**
Backend: Python, PydanticAI, asyncio  
Observability: Logfire  
Developer Tools: uv, Git, GitHub

**LLM Providers**
* Anthropic (claude-sonnet-4-6) — Agent Smith (heavy duty)
* OpenAI (gpt-5.4) — Agent Walker (quick scheduling)

**What's new:**
* Dual-agent design: heavy doc-reading agent (Claude) + lightweight scheduling agent (GPT)
* Parallel async data gathering: `asyncio.gather` for concurrent API requests + polling loop for async results
* Deterministic fallback solver: pure-async solution with zero LLM calls (just as a benchmark)

**Solution architecture:**
1. `main.py` — Orchestrator: 6-step workflow (start → parallel data fetch → poll results → compute schedule → unlock codes → submit config → done)
2. `deterministic_solve.py` — Alternative pure-async solver (no LLM): Greedy weather analysis, storm vs production slot logic
3. `suit.py` — Reusable tools: `task_result_verification` (write/verify), `wait_for_API` (rate-limit handler), fetch/save utilities
4. `prompts_lib.py` — Two-step prompts: doc extraction (Agent Smith) + turbine scheduling rules (Agent Walker)
5. `schemas.py` — Pydantic schemas: TurbineSlotConfig, TurbineConfigAction, TurbineScheduleAnswer
6. `session.py` — ContextSessionManager: shared execution context across tool calls
7. `token_tracker.py` — CostTracker: per-model token & USD accounting, auto-saves cost log

**Side Quests:**
* Deterministic solver as an LLM benchmark: same task solved without AI to measure cost/speed tradeoff [DONE]

**What I practiced / learned:**
* Multi-agent orchestration with heterogeneous LLM providers (Anthropic + OpenAI in one workflow)
* Async concurrent API calls with polling loop under a hard time constraint (40s window)
* Deterministic vs agentic tradeoff: the pure-async solver is faster and cheaper, but zero flexibility

**Task completion details:**
* gpt-5.4
* Input tokens (IT): 42,653
* Output tokens (OT): 776
* Requests: 10
* Full Task Completion Cost: $0.12
* Time: {"code":0,"message":"{FLG:...}","elapsedSeconds":"34.30"}

