import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
import os
from pathlib import Path
from prompts_lib import sys_prompt_S04E01
from pydantic_ai import Agent
from session import ContextSessionManager
from suit import (
                task_result_verification,
                get_content_from_Website
                )
from utils import short_hash
from token_tracker import CostTracker
from typing import Final
from website_loggin import get_OKO_cookie

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# URL:
S04E01_OKO_PANEL_URL: Final[str] = os.environ["S04E01_OKO_PANEL_URL"]

# Login Data
S04E01_OKO_LOGIN: Final[str] = os.environ["S04E01_OKO_LOGIN"]
S04E01_OKO_PASSWORD: Final[str] = os.environ["S04E01_OKO_PASSWORD"]

# API Key:
AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]

# Task Name:
S04E01_TASK_NAME: Final[str] = os.environ["S04E01_TASK_NAME"]

# ======================================================================
# LOGFIRE SETUP & Tracking
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

tt = CostTracker()

# ======================================================================
# MCP TOOLSET
# ======================================================================

# ======================================================================
# TOOLS
# ======================================================================

ToolBox1 = [

            get_content_from_Website,
            task_result_verification,
            ]

# ======================================================================
# AGENTS
# ======================================================================

task_models = {
    "A":"google-gla:gemini-2.5-flash",
    "B":"google-gla:gemini-2.5-flash",
    "C":"openai:gpt-4o",
    "Smith":"anthropic:claude-sonnet-4-6",
}

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=sys_prompt_S04E01,
    name="Agent Smith, specialty: Special Agent",
    description="Heavy Duty Agent",
    tools=ToolBox1
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):
    
    logfire.info("WF Starts")

    # force async to wait for playwright
    res = await asyncio.wait_for(
        asyncio.to_thread(
            get_OKO_cookie,
            url=S04E01_OKO_PANEL_URL,
            login=S04E01_OKO_LOGIN,
            psw=S04E01_OKO_PASSWORD,
            api_key=AI_DEV4_API_KEY
        ),
        timeout=10
    )

    OKO_session_coockie = {"oko_session": res[0]['value']}

    # ----------------------------------------------------------------------

    user_prompt1 = f"USE provided coockie in get_content_from_Website tool: {OKO_session_coockie}"

    res1 = await Agent_Smith.run(user_prompt1)

    tt.sum_tokens(Agent_Smith.model, res1.usage())

    log_agent_run(res1)

    print(res1)

    logfire.info("WF FINISH!")

    tt.summary()

if __name__ == "__main__":
    
    task_name: str = S04E01_TASK_NAME

    asyncio.run(main(task_name))