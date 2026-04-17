**Stack:**
asyncio · GCP Cloud Run · Pydantic Logfire · Pydantic · PydanticAI · uv · Git · GitHub · OpenRouter
Ollama · PostgreSQL 17 + (vector extension)

**What’s new inside:**
* Real `ContextSessionManager` (based on native PydanticAI `RunContext`)
* New tools (e.g. safe ZIP downloading/unpacking)
* Hashed flags — you can verify correctness *only if you already know the flag*
* New gateway provider: OpenRouter
* Local model support added

**LLM providers**
* Anthropic
* Gemini (via GCP Vertex AI)
* OpenAI
* Microsoft: Phi-3.5

**What I practiced / learned:**
* More advanced context handling (passing context via special ContextSessionManager object)
* Vector embeddings
* Setting up a vector DB (PostgreSQL + extension)
* Pandas DataFrames

**Side Quests:**
* FORCED migration: PydanticAI Gateway → Pydantic Logfire [TODO]
* "Simple" prompt caching [PROTOTYPE READY]
* Evaluations: PydanticAI / Langfuse

**Ideas:**
* Deterministic plan executor/orchestrator
  (user prepare a specific plan → break it into steps in YAML → run deterministically, what steps AI Agents should do, handling selected tasks; some run once, some every run, some async)[PROTOTYPE READY]
* Automatic task summary
  (tokens usage: input/output, models used, time)
* Automatic reasoning summary (how the task was completed)
* Automatic flag hashing (SHA256) when task completed

**Task completion details:**
*A: My deterministic WorkFlow + small LLM (GPT-4.1) running in parallel (with use of async)
   → at least **50% lower cost**, potentially **up to 10x lower** with prompt caching
*B: Full solution proposed by Claude → works, but suboptimal in multiple areas

**Thoughts:**
* A lot...  will write a separate post