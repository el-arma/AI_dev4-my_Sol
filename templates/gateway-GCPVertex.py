from dotenv import load_dotenv
from pydantic_ai import Agent


load_dotenv()

agent = Agent(
    'gateway/google-vertex:gemini-2.5-flash'
)

result = agent.run_sync('Hello world!')

print(result)