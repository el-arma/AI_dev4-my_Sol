from dotenv import load_dotenv
from pydantic_ai import Agent

load_dotenv()

agent = Agent(
    'gateway/openai:gpt-4.1'
)

result = agent.run_sync('Hello world!')

print(result)