import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
from prompts_lib import puzzle_system_prompt, construct_input_prompt
from pydantic_ai import Agent
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import (task_result_verification, 
                #   fetch_csv_from_URL, 
                    save_to_json_file, 
                    load_json_file, 
                    get_png_from_url)

from pathlib import Path
import os

# IMG OCR WF:
from img_tools import img_processing, classify_shape


# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

S02E02_ELECTRICITY_SCHME_STATE_URL = os.environ["S02E02_ELECTRICITY_SCHME_STATE_URL"]
S02E02_ELECTRICITY_SCHME_SOLVED_URL = os.environ["S02E02_ELECTRICITY_SCHME_SOLVED_URL"]

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

ToolBox1 = [get_png_from_url]
ToolBox2 = [save_to_json_file, load_json_file]
ToolBox3 = [task_result_verification, load_json_file]

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
    # toolsets=[toolset],
    tools=ToolBox1, 
    retries=1 # number of retires of the tool
)

Agent_Smith = Agent(model='gateway/anthropic:claude-sonnet-4-6', 
              system_prompt=puzzle_system_prompt,
              tools=ToolBox2)

Agent_Smith2 = Agent(model='gateway/openai:gpt-5.2', 
              system_prompt="Use available tools if needed",
              tools=ToolBox3)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):
    
    # THIS PART WORKS PERFECTLY!
    # ----------------------------------------------------------------------
    user_prompt1 = f"""
    Go to {S02E02_ELECTRICITY_SCHME_STATE_URL} and save the Image as 'electricity.png'
    """

    user_prompt2 = f"""
    Go to {S02E02_ELECTRICITY_SCHME_SOLVED_URL} and save the Image as 'solved_electricity.png'
    """

    res1, res2 = await asyncio.gather(
        Agent_Thompson.run(user_prompt1),
        Agent_Thompson.run(user_prompt2),
    )

    log_agent_run(res1)
    log_agent_run(res2)

    # ----------------------------------------------------------------------
    # IMG OCR WorkFlow
    # ----------------------------------------------------------------------

    crnt_state_FileName  = "electricity.png"
    solved_state_FileName  = "solved_electricity.png"

    crnt_state_shreds = Path("my_Solutions/S02E02/IMG/CRNT_STATE_SHREDS")
    solved_state_shreds = Path("my_Solutions/S02E02/IMG/SOLVED_STATE_SHREDS")

    crnt_state_shreds.mkdir(parents=True, exist_ok=True)
    solved_state_shreds.mkdir(parents=True, exist_ok=True)

    img_processing(crnt_state_FileName, crnt_state_shreds)
    img_processing(solved_state_FileName, solved_state_shreds)

    cord_dict_crnt: dict = {img.stem : classify_shape(img) for img in crnt_state_shreds.glob("*.png")}
    cord_dict_solved: dict = {img.stem : classify_shape(img) for img in solved_state_shreds.glob("*.png")}

    puzzle_input_user_prompt = construct_input_prompt(cord_dict_crnt, cord_dict_solved)

    print(puzzle_input_user_prompt)
    # ----------------------------------------------------------------------
    
    result = await Agent_Smith.run(puzzle_input_user_prompt)
    
    print(result.output)

    log_agent_run(result)
    # ----------------------------------------------------------------------

    final_prompt = f"""

    You are sending a solution for a puzzle. The solution is already prepared.

    Your task is to transform and send it step by step.

    ----------------------------------------
    STEP 1 — LOAD DATA
    ----------------------------------------
    Load the JSON file: 'rotations.json'

    ----------------------------------------
    STEP 2 — MAP COORDINATES
    ----------------------------------------
    Convert grid labels:

    A1 | B1 | C1
    A2 | B2 | C2
    A3 | B3 | C3

    into:

    1x1 | 1x2 | 1x3
    2x1 | 2x2 | 2x3
    3x1 | 3x2 | 3x3

    (row x column)

    ----------------------------------------
    STEP 3 — PROCESS ROTATIONS
    ----------------------------------------
    For each entry in the JSON:

    - If rotation == 0 → ignore
    - If rotation > 0 → perform actions

    Each rotation must be sent as a SEPARATE request.

    ----------------------------------------
    STEP 4 — OUTPUT FORMAT
    ----------------------------------------
    Use tool: task_result_verification

    task_name = {task_name}

    EXAMPLE Answer argument format:

    {{
        "rotate": "2x3"
    }}

    ----------------------------------------
    IMPORTANT RULES
    ----------------------------------------
    - One request = one rotation
    - Never batch multiple rotations
    - Send requests sequentially
    - Stop when flag is returned:
    {{'FLG': '...'}}
    """

    result = await Agent_Smith2.run(final_prompt)
    
    print(result.output)

    log_agent_run(result)

if __name__ == "__main__":
    
    task_name: str = "electricity"
    
    asyncio.run(main(task_name))
