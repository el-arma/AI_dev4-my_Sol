from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider

provider = gateway_provider(
    'openai',
    api_key='paig_<example_key>',
    route='builtin-openai'
)
model = OpenAIChatModel('gpt-5.2', provider=provider)
agent = Agent(model)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)

"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""