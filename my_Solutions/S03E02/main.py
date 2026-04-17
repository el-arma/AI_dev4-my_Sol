import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
import os
import pandas as pd
from pathlib import Path
from prompts_lib import sys_prompt_S03E02
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
                )
from utils import short_hash
from typing import Final

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# Endpoints:
# 

# URL:
S03E01_SENSORS_DATA: Final[str] = os.environ["S03E01_SENSORS_DATA"]

# ======================================================================
# LOGFIRE SETUP
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

# ======================================================================
# MCP TOOLSET
# ======================================================================

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

# ======================================================================
# TOOLS
# ======================================================================

ToolBox1 = [
            # download_zip_from_URL,
            # extract_zip_file,
            # get_content_from_Website,
            task_result_verification,
            # get_png_from_url,
            # get_from_context, save_to_context,
            post_json_data_to_API
            ]

# ToolBox2 = [save_to_context]

# ToolBox3 = [task_result_verification,
#             get_from_context, save_to_context,
#             read_txt]

# ======================================================================
# AGENTS
# ======================================================================

system_prompt: str = "Check avialiable tools, use it if needed."

# GATWAY NO LONGER ACTIVE!!!
# "gateway/google-vertex:gemini-2.5-flash"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

sys_prompt = sys_prompt_S03E02

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=sys_prompt,
    name="Agent Smith, specialty: Special Agent", 
    tools=ToolBox1
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):

    logfire.info("WF Starts")

    # ----------------------------------------------------------------------

    logfire.info("Init context session")
    
    logfire.info("Step 1")

    user_prompt1 = "Execute system prompt"

    res1 = await Agent_Smith.run(user_prompt1)

    print(res1)

    logfire.info("WF FINISH!")

if __name__ == "__main__":
    
    task_name: str = "evaluation"
    
    asyncio.run(main(task_name))