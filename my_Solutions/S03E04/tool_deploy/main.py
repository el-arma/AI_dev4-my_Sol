import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai import Agent
import logfire
import os
import sqlite3
from token_tracker import CostTracker

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

DB_PATH = Path(os.getenv("DB_PATH", "main.db"))

# ======================================================================
# LOGFIRE SETUP & Tracking
# ======================================================================

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

app = FastAPI()
logfire.instrument_fastapi(app)

tt = CostTracker()
_tt_lock = asyncio.Lock()

# ======================================================================


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# ======================================================================
# AGENT
# ======================================================================

DB_SCHEMA = (
    "Table: stock | Columns: item_name TEXT, item_code TEXT, city_name TEXT, city_code TEXT | "
    "PK: (item_code, city_code)"
)

SYSTEM_PROMPT = f"""You are a database assistant. Help the user find cities that sell specific items.

{DB_SCHEMA}

Use available tools to query the database and return a short, direct answer.
Final answer must be under 400 characters — only city names or item info, no explanations.
"""

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=SYSTEM_PROMPT,
    name="Agent Smith, specialty: Special Agent", 
    description="Heavy Duty Agent"
)

# ======================================================================
# TOOLS
# ======================================================================

@Agent_Smith.tool_plain
def find_cities_for_item(item_name_fragment: str) -> str:
    """Search cities that sell an item using a keyword or fragment of its name."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "SELECT DISTINCT city_name, item_name, item_code FROM stock "
            "WHERE lower(item_name) LIKE lower(?) ORDER BY city_name",
            (f"%{item_name_fragment}%",),
        )
        rows = cur.fetchall()
        if not rows:
            return "No results found."
        groups: dict[str, tuple[str, list[str]]] = {}
        for city, item, code in rows:
            if item not in groups:
                groups[item] = (code, [])
            groups[item][1].append(city)
        parts = [f"{item} [{code}]: {', '.join(cities)}" for item, (code, cities) in groups.items()]
        return "\n".join(parts)[:900]
    finally:
        conn.close()


@Agent_Smith.tool_plain
def find_cities_with_all_items(item_codes_csv: str) -> str:
    """Find cities that simultaneously stock ALL specified items. Pass item codes as comma-separated values."""
    codes = [c.strip() for c in item_codes_csv.split(",") if c.strip()]
    if not codes:
        return "No item codes provided."
    n = len(codes)
    placeholders = ", ".join("?" * n)
    conn = get_conn()
    try:
        cur = conn.execute(
            f"SELECT city_name FROM stock WHERE item_code IN ({placeholders}) "
            f"GROUP BY city_code HAVING COUNT(DISTINCT item_code) = ? ORDER BY city_name",
            (*codes, n),
        )
        rows = [r[0] for r in cur.fetchall()]
        if not rows:
            return "No city stocks all requested items."
        return f"Cities with all items: {', '.join(rows)}"
    finally:
        conn.close()


@Agent_Smith.tool_plain
def execute_sql(sql_query: str) -> str:
    """Execute a SELECT SQL query against the stock database and return raw results."""
    if not sql_query.strip().upper().startswith("SELECT"):
        return "Only SELECT queries are allowed."
    conn = get_conn()
    try:
        cur = conn.execute(sql_query)
        rows = cur.fetchmany(30)
        if not rows:
            return "Query returned no results."
        col_names = [d[0] for d in cur.description]
        lines = [", ".join(col_names)] + [", ".join(str(v) for v in row) for row in rows]
        return "\n".join(lines)[:900]
    except Exception as e:
        return f"SQL error: {e}"
    finally:
        conn.close()


# ======================================================================
# REQUEST / RESPONSE
# ======================================================================

class ToolRequest(BaseModel):
    params: str


def truncate(text: str, max_bytes: int = 490) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes - 3].decode("utf-8", errors="ignore") + "..."


@app.post("/api/v1/S03E04-tool")
async def handle_request(req: ToolRequest) -> dict:
    logfire.info(f"Request: {req.params}")

    result = await Agent_Smith.run(req.params)
    async with _tt_lock:
        tt.sum_tokens(Agent_Smith.model, result.usage())
        logfire.info("Token usage", token_stats=tt.as_dict())
        tt.summary()

    logfire.info("Agent run complete")

    return {"output": truncate(result.output)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
