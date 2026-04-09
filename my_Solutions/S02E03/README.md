S02E03

**Stack:**
asyncio · GCP Cloud Run · Logfire · Pydantic · PydanticAI · uv · git · GitHub

**What’s new inside:**
* Tools for reading and processing logs/txt files:
    * Designed to handle large-scale inputs (1.5k, 150k, 1M - doesn't matter) will chop it into chunks and process each piece
    * Default chunk size: 1000 lines (customizable)
    * Filtering + condensation before sending to LLM - avoids context overflow & reduces token usage
    * Fully configurable: chunk size, event-level filters, processing strategy

**LLM providers**
* Anthropic
* Gemini (via GCP Vertex AI)
* OpenAI

**What I practiced / learned:**
* Generators (yield instead of return) for memory-efficient streaming

**Ideas:**
* Jinja + Pydantic as a nice structured prompt constructor:
    * Jinja = rendering (templates to final prompt)
    * Pydantic = validation (schema, constraints, safety)

This combo should make prompt construction more predictable, testable, and less error-prone — especially in larger systems.

**Side Quests:**
* Exploring LGTM stack (e.g. replicate the log flow from this task)
* Logfire with an alternative OTel backend - looking for something more production-oriented (better for production VPS purposes)
