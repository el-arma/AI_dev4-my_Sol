from dotenv import load_dotenv
from pydantic_ai import Agent
from cost_estimates import CostTracker

load_dotenv()

PROMPT = "1+1=? One number only."

# pydantic_ai resolves "provider:model" strings to the direct provider SDK
MODELS = [
    "google-gla:gemini-2.5-flash",
    "google-gla:gemini-2.5-flash",
    "openai:gpt-4o",
    "anthropic:claude-sonnet-4-6",
]

tracker = CostTracker()

for model_id in MODELS:
    agent = Agent(model_id)
    result = agent.run_sync(PROMPT)
    usage = result.usage()
    tracker.sum_tokkens(model_id, usage)
    print(f"{model_id:45s} {result.output!r:6} {usage}")

tracker.summary()
