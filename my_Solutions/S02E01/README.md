**Stack:**
GCP Cloud Run · Logfire · Pydantic · PydanticAI · uv · Git · GitHub

**What I practiced / learned:**
* REAL prompt engineering focused on designing robust prompts designed for small-size LLMs with limited capabilities (prompting prompts ;)
* constructing prompts under strict constraints – including limited token budgets  
* preparing AI agents for potential system outages and how to handle unstable APIs

**Ideas:** 
* System prompt as context engineering:
  - can provide available tools
  - tell the AI Agent "where it is" (e.g. online/offline, system type, etc.)
  - can tell how it should behave in general ("Be polite, but don't agree with everything the customer says.")
* Verification loops (LLM - API - feedback - retry) - must be implemented sooner or later (preferably sooner)
* Context session manager class to automate passing context between AI Agents in a workflow