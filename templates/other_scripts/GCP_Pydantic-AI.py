from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel

load_dotenv()

model = GoogleModel(
    "gemini-2.5-flash"
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant"
)

result = agent.run_sync("Why is the sky blue?")
print(result.output)