from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


ollama_model = OpenAIChatModel(
    model_name='qwen3:4b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

agent = Agent(ollama_model
)

user_prompt = "Capital of France? One word only"

result = agent.run_sync(user_prompt)

print(result.output)

print(result.usage())


