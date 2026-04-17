from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-haiku-4-5')
# model = AnthropicModel('claude-sonnet-4-5')
agent = Agent(model)

result = agent.run_sync('Hello world!')

print(result)