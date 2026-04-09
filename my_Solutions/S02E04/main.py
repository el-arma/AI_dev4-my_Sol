import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
from prompts_lib import construct_input_prompt_S02E04
from pydantic_ai import Agent
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import (task_result_verification, 
                # #   fetch_csv_from_URL, 
                #     save_to_json_file, 
                #     load_json_file, 
                #     get_png_from_url,
                    post_json_data_to_API,
                    save_to_context,
                    get_from_context
                )

from pathlib import Path
import os
from typing import Final

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# Endpoints:
MAIL: Final[str] = os.environ["MAIL"]

# URL:
BASE_URL: Final[str] = os.environ["BASE_URL"]
API_ZMAIL_URL: Final[str] = f"{BASE_URL}/{MAIL}"

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

ToolBox = [post_json_data_to_API, task_result_verification,
           get_from_context, save_to_context]

# ======================================================================
# AGENTS
# ======================================================================

system_prompt: str = "Check avialiable tools, use it if needed."

# "gateway/google-vertex:gemini-2.5-flash"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

Agent_Thompson = Agent(
    model='gateway/google-vertex:gemini-2.5-flash',
    system_prompt=system_prompt,
    name="Agent Thompson",
    # toolsets=[toolset],
    tools=ToolBox, 
    retries=2 # number of retires of the tool
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):
    
    logfire.info("WF Starts")

    user_prompt1 = f"""
    To {API_ZMAIL_URL}, send POST JSON query

    ```json
    {{
    "action": "help",
    "page": 1
    }}
    ```
    You will receive back a set of instruction and parameters. Prepare it form which would be understandable for another LLM, but make it concise.
    
    Then use tool save to context to save it. 

    """
    result = await Agent_Thompson.run(user_prompt1)
    
    logfire.info("Step 2")

    user_prompt2 = construct_input_prompt_S02E04(task_name)

    result = await Agent_Thompson.run(user_prompt2)

    print(result.output)

if __name__ == "__main__":
    
    task_name: str = "mailbox"
    
    asyncio.run(main(task_name))