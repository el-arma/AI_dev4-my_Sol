# WORKS!!!

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModelSettings


load_dotenv()

settings = OpenRouterModelSettings(
    openrouter_provider={
        "order": ["OpenAI", "Google", "Anthropic"],  
        "allow_fallbacks": False,
    },
    openrouter_usage={"include": False},
)

# model = 'openrouter:google/gemini-2.5-flash'
# model = "openrouter:openai/gpt-4o-mini"
model = "openrouter:anthropic/claude-haiku-4-5"

agent = Agent(model = model,
              model_settings=settings)

result = agent.run_sync("Capital of France? One word only")

print(result.output)
print(result.usage())