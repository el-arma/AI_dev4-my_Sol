from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel


# Configure Logfire
logfire.configure(
    send_to_logfire='if-token-present',  
)
logfire.instrument_pydantic_ai()

load_dotenv()

model = GoogleModel(
    "gemini-2.5-flash" # stronger: gemini-2.5-pro
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant"
)

result = agent.run_sync("Why is 2+2?")
print(result.output)