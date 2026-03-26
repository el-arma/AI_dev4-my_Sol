HOW TO RUN:
1) Deploy with git push
2) Sent signal that it's rdy (S01E03_send_to_verify.py)
3) Check endpoint "check-flag" for flag

**Stack:**
FastAPI · SQLAlchemy · Pydantic · pytest · GitHub Actions · GCP Cloud Run · Docker · PydanticAI · uv

**What’s inside:**
* AI agent with persistent conversation memory (DB-backed context window) 
* Logs
* Full test suite with DB isolation (test DB) + agent mocking 
* CI → build, test, Dockerize, deploy to Cloud Run 

**What I practiced / learned:**
* Designing stateful AI systems (not just prompts)
* Production-ready patterns: logging, testing, dependency injection, secrets masking
* Shipping infra: from local → CI → docker container → cloud (GCP)