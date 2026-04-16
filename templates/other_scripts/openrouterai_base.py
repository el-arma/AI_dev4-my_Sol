# WORKS!!!

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
import os


load_dotenv()

model = OpenRouterModel(
    'anthropic/claude-haiku-4.5',
    provider=OpenRouterProvider(api_key=os.environ['OPENROUTER_API_KEY']),
)

settings = OpenRouterModelSettings(
    openrouter_provider={
        "order": ["Anthropic"],
        "allow_fallbacks": False,
    },
    openrouter_usage={"include": True},
)

agent = Agent(model, model_settings=settings) 

result = agent.run_sync("Capital of France? One word only")
print(result.output)
print(result.usage())

