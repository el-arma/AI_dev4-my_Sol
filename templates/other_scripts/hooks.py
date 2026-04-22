# WORKS!!!

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModelSettings
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks

load_dotenv()

settings = OpenRouterModelSettings(
    openrouter_provider={
        "order": ["OpenAI", "Google", "Anthropic"],  
        "allow_fallbacks": False,
    },
    openrouter_usage={"include": False},
)

model = 'openrouter:google/gemini-2.5-flash'
# model = "openrouter:openai/gpt-4o-mini"
# model = "openrouter:anthropic/claude-haiku-4-5"


async def log_request(ctx: RunContext[None], request_context: ModelRequestContext) -> ModelRequestContext:
    # print(f'Sending {len(request_context.messages)} messages to the model')
    # print(request_context)
    print(ctx)
    return request_context


agent = Agent(model, 
              model_settings=settings,
              capabilities=[Hooks(before_model_request=log_request)])

result = agent.run_sync('Hello!')
print(result.usage())
print(result.output)
