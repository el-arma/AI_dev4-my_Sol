from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
import logfire

load_dotenv()


# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

joke_selection_agent = Agent(  
  'gateway/openai:gpt-5.2',
  instructions=(
      'Use the `joke_factory` to generate 3 jokes, then choose the best. '
      'You must return just a single joke.'
  ),
)

joke_generation_agent = Agent(  
  'gateway/google-vertex:gemini-2.5-flash', output_type=list[str]
)

@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
  r = await joke_generation_agent.run(  
      f'Please generate {count} jokes.',
      usage=ctx.usage,  
  )
  return r.output  

result = joke_selection_agent.run_sync(
  'Tell me a joke.',
#   usage_limits=UsageLimits(request_limit=5, total_tokens_limit=500),
)

print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

print(result.usage())
#> RunUsage(input_tokens=165, output_tokens=24, requests=3, tool_calls=1)