*S03E05 - Save Them*

**Stack:**
Backend: Python, PydanticAI, asyncio  
Observability: Logfire  
Developer Tools: uv, Git, GitHub

**LLM Providers**
* Anthropic
* Gemini (via GCP Vertex AI)
* OpenAI

**Solution architecture:**
1. `main.py` — Agent Smith entry point: tool registration + 4-step workflow (discover → fetch → solve → submit)
2. `pathfinder.py` — Pure Python route solver (Greedy Best-First Search + Pareto pruning), zero LLM calls
3. `prompts_lib.py` — System prompt defining the 4-step agent pipeline
4. `suit.py` — Reusable tools
5. `token_tracker.py` — CostTracker: per-model token & USD accounting, auto-saves cost log

**Side Quests:**
* Deep dive into graph search algorithms: BFS/DFS, Greedy Best-First Search + Pareto pruning (?)

**What I practiced / learned:**
* Agentic tool discovery via a ToolSearch API (no hardcoded domain tools)
* Greedy Best-First Search pathfinding with multi-objective Pareto pruning on a 5D state space `(x, y, mode, fuel, food)`
* Multi-model token & cost accounting across Anthropic / GCP / OpenAI
* Cooperation with Claude Code as a coding assistant

**Task completion details:**
* claude-sonnet-4-6
* Input tokens (IT): 25,993
* Output tokens (OT): 1,816
* Requests: 7
* Full Task Completion Cost: $0.105
