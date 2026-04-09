import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
from prompts_lib import S02E05_dam_img_prompt, S02E05_dam_atack_prompt
from pydantic_ai import Agent, BinaryContent
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import (task_result_verification, 
                # #   fetch_csv_from_URL, 
                #     save_to_json_file, 
                #     load_json_file, 
                    get_png_from_url,
                    post_json_data_to_API,
                    save_to_context,
                    get_from_context,
                    get_content_from_Website,
                    read_txt
                )

from pathlib import Path
import os
from typing import Final

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# Endpoints:
# 

# URL:
S02E05_DRONE_INSTRUCTION_URL: Final[str] = os.environ["S02E05_DRONE_INSTRUCTION_URL"]
S02E05_DAM_IMG_URL: Final[str] = os.environ["S02E05_DAM_IMG_URL"]

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

ToolBox1 = [get_content_from_Website, 
            task_result_verification,
            get_png_from_url,
            get_from_context, save_to_context]

ToolBox2 = [save_to_context]

ToolBox3 = [task_result_verification,
            get_from_context, save_to_context,
            read_txt]

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
    tools=ToolBox1, 
    retries=2 # number of retires of the tool
)

Agent_Jones = Agent(
    model='gateway/openai:gpt-5.4',
    system_prompt=system_prompt,
    name="Agent Jones, specialty: vision", 
    tools=ToolBox2
)

Agent_Smith = Agent(
    model='gateway/anthropic:claude-sonnet-4-6',
    system_prompt=system_prompt,
    name="Agent Smith, specialty: Special Agent", 
    tools=ToolBox3
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):
    
    logfire.info("WF Starts")

    # # THIS WORKS!!
    # # ----------------------------------------------------------------------------
    logfire.info("Step 1 & 2")

    user_prompt1 = f"""
    Go to {S02E05_DRONE_INSTRUCTION_URL}, save the website content as drone_instruction.md

    """
    
    user_prompt2 = f"""
    Go to {S02E05_DAM_IMG_URL}, save the Image as dam_image.png

    """

    res1, res2 = await asyncio.gather(
        Agent_Thompson.run(user_prompt1),
        Agent_Thompson.run(user_prompt2),
    )

    log_agent_run(res1)
    log_agent_run(res2)
    # #----------------------------------------------------------------------------

    logfire.info("Step 3")

    img_path = Path('my_Solutions/Data_Bank/dam_image.png')

    vision_user_prompt = S02E05_dam_img_prompt

    res3 = await Agent_Jones.run(
        user_prompt=[
            vision_user_prompt,
            BinaryContent(data=img_path.read_bytes(), media_type='image/png')           
        ],
    )

    # log_agent_run(res3)
    print(res3.output)

    logfire.info("Step 4")

    res4 = await Agent_Smith.run(S02E05_dam_atack_prompt)

    log_agent_run(res4)
    
    logfire.info("WF FINISH!")

if __name__ == "__main__":
    
    task_name: str = "drone"
    
    asyncio.run(main(task_name))