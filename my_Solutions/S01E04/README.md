**Stack:**
Docker · FastMCP · GCP Cloud Run · Logfire · Pydantic · PydanticAI · uv

**What’s new inside:**
* Observability layers – I can finally precisely see what LLM agent is doing and what tools with what args it is calling
* Simple custom-made MCP server with tools
* Independent logger (just in case)
* Pydantic AI gateway – (3 provider one via GCP) – better cost tracking

So it’s starting to look like a somewhat nice, cohesive ecosystem:
* Pydantic for LLM I/O validation
* Pydantic Logfire
* Pydantic AI
* Pydantic AI Gateway
* [Pydantic is all you need ;)](https://www.youtube.com/watch?v=yj-wSRJwrrc)

**What I practiced / learned:**
* Basics of MCP and why it’s so damn useful when used properly
* Cleaning GitHub repos from secrets/paths/URLs/endpoints (nothing was leaked, just as a precaution)
* Implementing observability layers for agent actions and their tools (Logfire + custom logger)
* Adding vision capabilities to the agent (image recognition)
* Implementing gateway – routing

**Ideas:**
* Tired of LLMs hallucinating Pydantic AI components → small RAG over PydanticAI docs
* My own MCP gateway (yes, Docker is cool, but eventually this should live in the cloud)
* LLM gateway patterns:
  * horizontal → multiple agents as fallback if one fails
  * vertical → automatically chaining agents when one is not strong enough
