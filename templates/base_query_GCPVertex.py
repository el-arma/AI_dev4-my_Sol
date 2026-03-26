from dotenv import load_dotenv
from pydantic_ai import Agent

# GCP key must be provided (JSON)
load_dotenv()

agent = Agent(
    'gemini-2.5-flash'
)

result = agent.run_sync('Hello world!')

print(result)