import asyncio
from dataclasses import dataclass
from dotenv import load_dotenv
from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
import logfire
import os
import requests
import sqlite3
from token_tracker import CostTracker

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# paths:
DB_PATH: Path = Path(os.getenv("DB_PATH", "main.db"))

# Webhooks:
DISCORD_WEB_HOOK: str = os.environ["DISCORD_WEB_HOOK"]

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
# for DB Dep injection
# ======================================================================
@dataclass
class DependDB:
    conn: sqlite3.Connection


# ======================================================================
# AGENT
# ======================================================================

def _introspect_schema() -> str:
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        lines = []
        for (t,) in tables:
            cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
            col_defs = ", ".join(f"{c[1]} {c[2]}" for c in cols)
            pks = ", ".join(c[1] for c in cols if c[5] > 0)
            lines.append(f"Table: {t} | Columns: {col_defs}" + (f" | PK: ({pks})" if pks else ""))
        return "\n".join(lines)
    finally:
        conn.close()

DB_SCHEMA = _introspect_schema()

SYSTEM_PROMPT = f"""You are a database assistant. Help the user find cities that sell specific items.

{DB_SCHEMA}

IMPORTANT: All item names in the database are in Polish. If the user asks in English (e.g. "wind turbine", "battery", "inverter"), translate the key terms to Polish before calling search tools. For example: "wind turbine" → "turbina wiatrowa", "battery" → "akumulator", "inverter" → "inwerter", "solar panel" → "panel solarny".

Use available tools to query the database and return a short, direct answer.
Final answer must be under 400 characters — only city names or item info, no explanations.
"""

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    deps_type=DependDB,
    system_prompt=SYSTEM_PROMPT,
    name="Agent Smith, specialty: Special Agent",
    description="Heavy Duty Agent"
)

# ======================================================================
# TOOLS
# ======================================================================

@Agent_Smith.tool
def find_cities_for_item(ctx: RunContext[DependDB], item_name_fragment: str) -> str:
    """Search cities that sell an item using a keyword or fragment of its name.

    Args:
        item_name_fragment (str): Keyword or partial name of the item to search for.
    """
    cur = ctx.deps.conn.execute(
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
    return "\n".join(parts)


@Agent_Smith.tool
def find_cities_with_all_items(ctx: RunContext[DependDB], item_codes_csv: str) -> str:
    """Find cities that simultaneously stock ALL specified items.

    Args:
        item_codes_csv (str): Comma-separated item codes to match (e.g. "A1, B2, C3").
    """
    codes = [c.strip() for c in item_codes_csv.split(",") if c.strip()]
    if not codes:
        return "No item codes provided."
    n = len(codes)
    placeholders = ", ".join("?" * n)
    cur = ctx.deps.conn.execute(
        f"SELECT city_name FROM stock WHERE item_code IN ({placeholders}) "
        f"GROUP BY city_code HAVING COUNT(DISTINCT item_code) = ? ORDER BY city_name",
        (*codes, n),
    )
    rows = [r[0] for r in cur.fetchall()]
    if not rows:
        return "No city stocks all requested items."
    return f"Cities with all items: {', '.join(rows)}"


@Agent_Smith.tool
def execute_sql(ctx: RunContext[DependDB], sql_query: str) -> str:
    """Execute a SELECT SQL query against the stock database and return raw results.

    Args:
        sql_query (str): A valid SELECT statement to run against the database.
    """
    if not sql_query.strip().upper().startswith("SELECT"):
        return "Only SELECT queries are allowed."
    try:
        cur = ctx.deps.conn.execute(sql_query)
        rows = cur.fetchall()
        if not rows:
            return "Query returned no results."
        col_names = [d[0] for d in cur.description]
        lines = [", ".join(col_names)] + [", ".join(str(v) for v in row) for row in rows]
        return "\n".join(lines)
    except Exception as e:
        return f"SQL error: {e}"


# ======================================================================
# REQUEST / RESPONSE
# ======================================================================

# Pydantic Schema
class ToolRequest(BaseModel):
    params: str


def truncate(text: str, max_chars: int = 490) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


@app.post("/api/v1/S03E04-tool")
async def handle_request(req: ToolRequest) -> dict:
    logfire.info("request", params=req.params)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        result = await Agent_Smith.run(req.params, deps=DependDB(conn=conn))
    finally:
        conn.close()
    
    async with _tt_lock:
        tt.sum_tokens(Agent_Smith.model, result.usage())
        logfire.info("Token usage", token_stats=tt.as_dict())
        tt.summary()
        requests.post(
            DISCORD_WEB_HOOK,
            json={"content": str(tt.as_dict())},
        )

    logfire.info("Agent run complete")

    return {"output": truncate(result.output)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
