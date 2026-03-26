import asyncio
from dotenv import load_dotenv
from logger import log_agent_run
import logfire
import os
from mcp_server.mcp_calc_server import fastmcp_server
from pydantic_ai import Agent, ImageUrl
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from schemas import Answer
from typing import Final



load_dotenv()

S01E04_PACKAGE_DOCUMENTATION_URL: Final[str] = os.environ["S01E04_PACKAGE_DOCUMENTATION_URL"]
MCP_DATABANK_DIR: Final[str] = os.environ["MCP_DATABANK_DIR"]

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

my_toolset = FastMCPToolset(fastmcp_server,
                        tool_error_behavior="model_retry",
                        max_retries=1)

mcp_config = {
    "mcpServers": {
        "filesystem": {
            "transport": "stdio",
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-v", f"{MCP_DATABANK_DIR}:/workspace",
                "mcp/filesystem:latest",
                "/workspace"
            ]
        }
    }
}

toolset_mcpfiles = FastMCPToolset(mcp_config)

# ----------------------------------------------------------------------
# VISION AGENT
# ----------------------------------------------------------------------

vision_agent = Agent(
    model="gateway/anthropic:claude-sonnet-4-6"
    )

async def analyze_img_from_url(url: str) -> str:
    """Analyze provided image from a given URL and return a detailed description for another LLM Agent"""
    
    res = await vision_agent.run([
        "Describe this image in detail",
        ImageUrl(url=url)
    ])

    return res.output

# ----------------------------------------------------------------------
# MAIN AGENT
# ----------------------------------------------------------------------

system_prompt: str = "USE PROVIDED TOOLS WHEN NEEDED."

# "gemini-2.5-pro"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"


agent = Agent(
    model="gateway/openai:gpt-5.2",
    system_prompt=system_prompt,
    toolsets=[toolset_mcpfiles, my_toolset],
    # tools=[analyze_img_from_url]
)

# ----------------------------------------------------------------------
# PROMPT
# ----------------------------------------------------------------------

user_prompt = f"""

## Task
Go to the documentation URL in the documentation section. 
SAVE all found resources, in your workspace folder.

## Documentation

Available at:
{S01E04_PACKAGE_DOCUMENTATION_URL}

## Steps

1. Fetch documentation (start from `index.md`, follow all links)
2. Read ALL relevant files (including images → use vision if needed)
3. Find declaration template

SAVE all found resources, in your workspace folder.

## Rules

- Do NOT skip any documentation files
- Images may contain critical data
- Format must be exact (validated strictly)
- Do NOT invent values — use documentation

"""

async def main():
    async with agent:
        result = await agent.run(user_prompt,
                                output_type=Answer)
        log_agent_run(result)
        print(result.output)

if __name__ == "__main__":

    asyncio.run(main())