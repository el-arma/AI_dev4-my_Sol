*S03E04 - Negotiations*

**Stack:**
Backend: Python, FastAPI, Pydantic, PydanticAI  
Database: SQLite  
Infra: Docker, Docker Compose, NGINX, Hetzner VPS  
Testing: pytest  
Observability: Logfire  
Developer Tools: uv, Makefile, Git, GitHub

**LLM Providers**
* Anthropic
* Gemini (via GCP Vertex AI)
* OpenAI

**Solution architecture:**
1. `get_data.py` — downloads CSV files from AI_devs4 API
2. `db_setup.py` — merges multiple CSV files into a single `stock` table (item_name, item_code, city_name, city_code) in SQLite
3. `db_health_check.py` — validates the database (schema, row count, duplicates)
4. FastAPI tool endpoint — handles agent queries by executing SQL against the database
5. `test_local_deploy.py` — smoke tests + tests with real products and expected city mappings
6. `task_verification.py` — submits the tool to the verification system
7. Makefile orchestrates almost the full pipeline (download → build DB → validate → deploy locally → test)
8. NGINX routes traffic to two containers (ports: 8000 → task_S01E05, 8001 → task_S03E04)

**Side Quests:**
* Deploy solution with Cloud Run

**What I practiced / learned:**
* Building REST API tools for AI agents x2
* Data pipeline: raw CSV → local DB → deployed app on VPS
* Deployment to a Hetzner VPS using Docker containers
* Makefile as a multi-step pipeline orchestrator
* Writing smoke tests

**Task completion details:**
* claude-sonnet-4-6
* Input tokens (IT): 3.7k
* Output tokens (OT): 0.3k
* Requests: 6
* Task Completion: 6.5s
* Full Task Completion Cost: $0.0155

**Thoughts:**
* The database should have been initialized on the VPS, but I did a small workaround.
* MAKE doesn't like Windows - total migration to Linux is inevitable