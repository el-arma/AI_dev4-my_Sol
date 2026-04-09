import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
# from prompts_lib import puzzle_system_prompt, construct_input_prompt
from pydantic_ai import Agent
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import (task_result_verification, 
                #   fetch_csv_from_URL,
                    get_txt_from_url,
                    save_to_json_file, 
                    load_json_file, 
                    get_png_from_url,
                    read_txt_logs)

from pathlib import Path
import os

#
# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

S02E03_DATA_SOURCE_LOGS_URL = os.environ["S02E03_DATA_SOURCE_LOGS_URL"]

# ======================================================================
# LOGFIRE SETUP
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ======================================================================
# MCP TOOLSET
# ======================================================================

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

# ======================================================================
# TOOLS
# ======================================================================

ToolBox1 = [get_txt_from_url]
ToolBox2 = [read_txt_logs, task_result_verification]
# ToolBox2 = [save_to_json_file, load_json_file]
# ToolBox3 = [task_result_verification, load_json_file]

# ======================================================================
# AGENTS
# ======================================================================

system_prompt: str = "Check avialiable tools, use it if needed."

# "gateway/google-vertex:gemini-2.5-flash" - quick and cheap

# Strong:
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

Agent_Thompson = Agent(
    model='gateway/google-vertex:gemini-2.5-flash',
    name="Agent Thompson",
    system_prompt=system_prompt,
    # toolsets=[toolset],
    tools=ToolBox1, 
    retries=1 # number of retires of the tool
)

Agent_Smith = Agent(
    model='gateway/google-vertex:gemini-2.5-pro',
    name="Agent Smith",
    system_prompt=system_prompt,
    # toolsets=[toolset],
    tools=ToolBox2, 
    retries=1 # number of retires of the tool
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):

    # ------------------------------------------------------------------------
    user_prompt1 = f"""
    Go to {S02E03_DATA_SOURCE_LOGS_URL} and save the logs as 'failure.log'
    """
    res1 = await Agent_Thompson.run(user_prompt1)

    print(res1.output)

    # ------------------------------------------------------------------------

    user_prompt2 = f"""

    Read file: 'failure.log' (it will return outp in chunks, so you may whave to use it a couple of times)

    Filter out only important events: [ERRO], [WARN], [CRIT]

    Select only those related to power plant components and failures/outages.

    Try to compress the information, but don't lose the timestamps, event lvls or crucial infromation in given log.

    Use task_result_verification tool to send the answer:

    task_name = {task_name}

    ANSWER FORMAT:
    * CRUCIAL! must fit within 1500 tokens,
    * preserves the multi-line format — one event per line.

    As argument 'answer' use dict: 'logs' : 'First line of logs\\nSecond line of logs...'
    
    """
    res2 = await Agent_Smith.run(user_prompt2)

    print(res2.output)


if __name__ == "__main__":
    
    task_name: str = "failure"
    
    asyncio.run(main(task_name))
