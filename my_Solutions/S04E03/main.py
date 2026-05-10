import asyncio
from logger import AgentLogger
from dotenv import load_dotenv
import logfire
from prompts_lib import S04E03_system_prompt
from pydantic_ai import Agent
from suit import task_result_verification
from token_tracker import CostTracker


# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# ======================================================================
# LOGFIRE SETUP & Tracking
# ======================================================================

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

tt = CostTracker()

# ======================================================================
# AGENTS
# ======================================================================

Smith_log = AgentLogger("Agent_Smith")

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    name="Agent Smith, specialty: Special Agent",
    description="Heavy Duty Agent",
    tools=[task_result_verification],
    capabilities=[Smith_log.get_hooks()]
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main():

    logfire.info("WF Starts")

    AI_doc_res = await Agent_Smith.run(S04E03_system_prompt)

    print(AI_doc_res.output)

    Smith_log.close()

    if AI_doc_res is not None:
        tt.sum_tokens(Agent_Smith.model, AI_doc_res.usage())

    tt.summary()

    logfire.info("WF FINISH!")

if __name__ == "__main__":

    asyncio.run(main())
