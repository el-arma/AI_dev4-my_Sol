import asyncio
from logger import AgentLogger
from dotenv import load_dotenv
import logfire
import os
from prompts_lib import S04E04_flag_prompt, S04E04_replicate_prompt
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from session import ContextSessionManager
from suit import (task_result_verification, download_zip_from_URL,
                  extract_zip_file, wait_for_API)
from token_tracker import CostTracker
from typing import Final


# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

S04E04_FILE_SYS_DIR: Final[str] = os.environ["S04E04_FILE_SYS_DIR"]

# ======================================================================
# LOGFIRE SETUP & Tracking
# ======================================================================

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

tt = CostTracker()

# ======================================================================
# MCP TOOLSET
# ======================================================================

fastmcp_server = FastMCP()

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
                "-v", f"{S04E04_FILE_SYS_DIR}:/workspace",
                "mcp/filesystem:latest",
                "/workspace"
            ]
        }
    }
}

toolset_mcpfiles: FastMCPToolset[ContextSessionManager] = FastMCPToolset(mcp_config)

# ======================================================================
# AGENTS
# ======================================================================

Smith_log = AgentLogger("Agent_Smith")

# Agent 1: fetches notes, builds plan, sends to API, gets flag, saves plan JSON
Agent_Smith = Agent(
    model="openai:gpt-5.4",
    name="Agent Smith, specialty: Flag Getter",
    description="Fetches data, gets the flag, saves plan for replication",
    deps_type=ContextSessionManager,
    tools=[task_result_verification, download_zip_from_URL,
           extract_zip_file, wait_for_API],
    toolsets=[toolset_mcpfiles],
    capabilities=[Smith_log.get_hooks()]  # type: ignore[arg-type]
)

Replicator_log = AgentLogger("Agent_Replicator")

# Agent 2: reads plan JSON, replicates file structure locally via MCP
Agent_Replicator = Agent(
    model="openai:gpt-5.4",
    name="Agent Replicator, specialty: Local FS Replication",
    description="Reads plan JSON and builds local filesystem structure via MCP",
    deps_type=ContextSessionManager,
    toolsets=[toolset_mcpfiles],
    capabilities=[Replicator_log.get_hooks()]  # type: ignore[arg-type]
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main():

    logfire.info("WF Starts")

    # ── TASK 1: Get the flag ──────────────────────────────────────────
    logfire.info("TASK 1: Flag acquisition")
    session1 = ContextSessionManager()
    flag_res = await Agent_Smith.run(S04E04_flag_prompt, deps=session1)
    print(flag_res.output)
    Smith_log.close()
    if flag_res is not None:
        tt.sum_tokens(Agent_Smith.model, flag_res.usage())

    # ── TASK 2: Replicate locally ─────────────────────────────────────
    logfire.info("TASK 2: Local filesystem replication")
    session2 = ContextSessionManager()
    replicate_res = await Agent_Replicator.run(S04E04_replicate_prompt, deps=session2)
    print(replicate_res.output)
    Replicator_log.close()
    if replicate_res is not None:
        tt.sum_tokens(Agent_Replicator.model, replicate_res.usage())

    tt.summary()

    logfire.info("WF FINISH!")

if __name__ == "__main__":

    asyncio.run(main())
