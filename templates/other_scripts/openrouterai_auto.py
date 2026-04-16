# NOT WORKING - MODEL OVERLOAD?

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings

load_dotenv()

agent = Agent(
    OpenRouterModel('meta-llama/llama-3.3-70b-instruct:free'),
    model_settings=OpenRouterModelSettings(
        openrouter_provider={"allow_fallbacks": True}
    )
)

# OpenRouterModel picks up OPENROUTER_API_KEY from env automatically 
# No OpenRouterProvider needed. 
# No routing settings either since it's a free model with no BYOK.

result = agent.run_sync("Capital of France? One word only")
print(result.output)
print(result.usage())


# April 12, 2026, there are **27 free models** available on OpenRouter. Limits: **20 req/min, 200 req/day**.

# All of them have the `:free` suffix in their name (except `openrouter/free`):

# | Model                                    | Provider   | Context | Capabilities                   |
# | ---------------------------------------- | ---------- | ------- | ------------------------------ |
# | `openrouter/free`                        | OpenRouter | 200K    | Vision + Tools (auto-selected) |
# | `google/gemma-4-26b-a4b-it:free`         | Google     | 262K    | Vision + Tools                 |
# | `google/gemma-4-31b-it:free`             | Google     | 262K    | Vision + Tools                 |
# | `nvidia/nemotron-3-super-120b-a12b:free` | NVIDIA     | 262K    | Tools                          |
# | `qwen/qwen3-next-80b-a3b-instruct:free`  | Qwen       | 262K    | Tools                          |
# | `qwen/qwen3-coder:free`                  | Qwen       | 262K    | Tools                          |
# | `openai/gpt-oss-120b:free`               | OpenAI     | 131K    | Tools                          |
# | `openai/gpt-oss-20b:free`                | OpenAI     | 131K    | Tools                          |
# | `meta-llama/llama-3.3-70b-instruct:free` | Meta       | 66K     | Tools                          |
# | `google/gemma-3-27b-it:free`             | Google     | 131K    | Vision                         |
# | `arcee-ai/trinity-large-preview:free`    | Arcee      | 131K    | Tools                          |
# | `nvidia/nemotron-nano-12b-v2-vl:free`    | NVIDIA     | 128K    | Vision + Tools                 |
# | `minimax/minimax-m2.5:free`              | MiniMax    | 197K    | Tools                          |
# | `z-ai/glm-4.5-air:free`                  | Z.ai       | 131K    | Tools                          |
# | `liquid/lfm-2.5-1.2b-thinking:free`      | LiquidAI   | 33K     | Reasoning                      |
# | `google/gemma-3-12b-it:free`             | Google     | 33K     | Vision                         |
# | `google/gemma-3-4b-it:free`              | Google     | 33K     | Vision                         |
# | `meta-llama/llama-3.2-3b-instruct:free`  | Meta       | 131K    | -                              |

# ---

# Best per use-case according to OpenRouter:

# * **Coding** → `qwen/qwen3-coder:free`
# * **Reasoning** → `liquid/lfm-2.5-1.2b-thinking:free`
# * **General** → `meta-llama/llama-3.3-70b-instruct:free`
# * **Vision** → `nvidia/nemotron-nano-12b-v2-vl:free`

# For testing with pydantic-ai, it’s enough to change the model string:

# ```python
# model = OpenRouterModel('meta-llama/llama-3.3-70b-instruct:free', ...)
# ```
