from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent, exceptions
from pydantic_ai.settings import ModelSettings

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# ======================================================================
# LOGFIRE SETUP
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ======================================================================
# AGENTS
# ======================================================================

system_prompt = "You are a helpful assistant."

agent = Agent(
    model="gateway/openai:gpt-5.2",
    model_settings=ModelSettings(max_tokens=100), # Hard token limits
    name="Miller",
    system_prompt=system_prompt,
    # toolsets=[toolset],
    # tools=ToolBox, 
    # retries=1 # number of retires of the tool
)

try:
    user_prompt1 = "Write me an essay about current world state."

    # Will return error - output tokens limit hits
    res = agent.run_sync(user_prompt1)

except exceptions.UnexpectedModelBehavior as e:
    print(f"[ERROR] {e}")

    user_prompt2 = "Write me latin phrase <100 tokens."

    # Will return error - output tokens limit hits
    res = agent.run_sync(user_prompt2)

print(res.output)



