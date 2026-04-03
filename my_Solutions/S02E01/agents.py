from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import task_result_verification, fetch_csv_from_URL, save_to_json_file, load_json_file


load_dotenv()

# ----------------------------------------------------------------------
# LOGFIRE SETUP
# ----------------------------------------------------------------------

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ----------------------------------------------------------------------
# MCP TOOLSET
# ----------------------------------------------------------------------

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

Tools1 = [fetch_csv_from_URL, save_to_json_file]
Tools2 = [task_result_verification, load_json_file]


# ----------------------------------------------------------------------
# MAIN AGENTS
# ----------------------------------------------------------------------

system_prompt: str = "Check avialiable tools, use it if needed."

# "gemini-2.5-pro"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

Agent_Thompson = Agent(
    model='gateway/openai:gpt-5.2',
    system_prompt=system_prompt,
    # toolsets=[toolset],
    tools=Tools1, 
    retries=1 # number of retires of the tool
)

system_prompt2: str = """
You are a Prompt Engineering Agent tasked with iteratively 
improving a classification prompt under strict constraints.
Use avialiable tools."""

Agent_Smith = Agent(
    model='gateway/anthropic:claude-sonnet-4-6',
    system_prompt=system_prompt2,
    # toolsets=[toolset],
    tools=Tools2, 
    retries=1 # number of retires of the tool
)

# ----------------------------------------------------------------------
# WF
# ----------------------------------------------------------------------

# "Classify 'DNG' if weapon/explosive/flammable device/baton or 'NEU' if tool/part/component/electronics.For reactor/nuclear ALWAYS 'NEU' {here put ID and item description}"

def main():

    user_prompt1 = """
    Fetch csv data from task_name 'categorize', insert only task name, all other paratemtres are default. Save result as 'items.json' using available tools.
    """

    prev_result = Agent_Thompson.run_sync(user_prompt1)

    log_agent_run(prev_result)

    user_prompt2 = """

    0. Use tool to read JSON file named 'items.json'.

    For each object from the provided list you must design a minimal prompt (≤100 tokens total with input) to classify items as DNG or NEU.

    Rules:
    - Output must be exactly one of two two categories: DNG or NEU.
    - Reactor-related items (reactor parts, fuel, nuclear modules, etc.) MUST ALWAYS be classified as NEU, regardless of description.
    - All other items should be classified correctly (DNG if dangerous/harmful/hazardous, otherwise NEU).

    Process:
    1. For each item, send your prompt to the verification API (tool: task_result_verification, task_name 'categorize').

    anwser format:

    answer = {
        "prompt": "Classify 'DNG' if weapon/explosive/flammable device/baton or 'NEU' if tool/part/component/electronics.For reactor/nuclear ALWAYS 'NEU'. {ID} {descr}"
    }
    
    Use provided prompt only as example, modify it as needed.
    
    2. If any classification fails or budget exceeded → send (tool: task_result_verification, task_name 'categorize'

    answer = {
        "prompt": "reset"
    }

    to start ower.

    3. Improve prompt using feedback and retry.
    4. Repeat until all 10 correct and FLAG ({FLG:...}) is returned as reply.

    Constraints:
    - Max 100 tokens including item data.
    - Keep prompt static and append variables at the end (for caching).
    - Optimize for brevity and correctness
    - Output: DNG or NEU.

    FINAL GOAL: obtain FLAG ({FLG:...})

    """

    result = Agent_Smith.run_sync(user_prompt2)

    log_agent_run(result)

if __name__ == "__main__":

    main()