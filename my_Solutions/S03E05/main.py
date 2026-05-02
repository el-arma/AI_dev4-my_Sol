import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
import os
import pandas as pd
from pathlib import Path
from pathfinder import solve as pathfinder_solve
from prompts_lib import sys_prompt_S03E05_full
from pydantic_ai import Agent, BinaryContent, ConcurrencyLimit
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from session import ContextSessionManager
# from schemas import XXX
from suit import (
                # download_zip_from_URL,
                # extract_zip_file,
                # load_json_file,
                # save_to_json_file,
                task_result_verification,
                # fetch_csv_from_URL, 
                # save_to_json_file, 
                # load_json_file, 
                # get_png_from_url,
                post_json_data_to_API,
                # save_to_context,
                # get_from_context,
                # get_content_from_Website,
                # read_txt
                # HIL, 
                save_to_markdown_file
                )
from utils import short_hash
from token_tracker import CostTracker
from typing import Final

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# Endpoints:
# 

# URL:
# S03E01_SENSORS_DATA: Final[str] = os.environ["S03E01_SENSORS_DATA"]

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

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

# ======================================================================
# TOOLS
# ======================================================================

def run_pathfinder(grid: list) -> list | None:
    """
    Solve the optimal route on the given grid.

    Args:
        grid: 2D list of terrain characters, row-major (list of rows).
              Each cell is one of: '.' empty, 'T' tree, 'W' water, 'R' rock,
              'S' start position, 'G' goal position.
              Example: [[".", "S", "T"], ["W", ".", "G"]]

    Returns:
        Answer list ready for submission, e.g. ["rocket", "up", "right", "dismount", "right"].
        Returns None if no valid path exists within the resource budget.
    """
    return pathfinder_solve(grid)

ToolBox1 = [
            # download_zip_from_URL,
            # extract_zip_file,
            # get_content_from_Website,
            task_result_verification,
            # get_png_from_url,
            # get_from_context, save_to_context,
            post_json_data_to_API,
            save_to_markdown_file,
            run_pathfinder,
            ]

# ToolBox2 = [save_to_context]

# ToolBox3 = [task_result_verification,
#             get_from_context, save_to_context,
#             read_txt]

# ======================================================================
# AGENTS
# ======================================================================

# GATWAY NO LONGER ACTIVE!!!
# "gateway/google-vertex:gemini-2.5-flash"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

task_models = {
    "A":"google-gla:gemini-2.5-flash",
    "B":"google-gla:gemini-2.5-flash",
    "C":"openai:gpt-4o",
    "Smith":"anthropic:claude-sonnet-4-6",
}

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=sys_prompt_S03E05_full,
    name="Agent Smith, specialty: Special Agent",
    description="Heavy Duty Agent",
    tools=ToolBox1
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):

    logfire.info("WF Starts")

    logfire.info("Phase I — discover, solve, submit")

    res1 = await Agent_Smith.run("Execute system prompt.")

    tt.sum_tokens(Agent_Smith.model, res1.usage())

    logfire.info("WF FINISH!")

    tt.summary()

if __name__ == "__main__":
    
    task_name: str = "savethem"
    
    asyncio.run(main(task_name))