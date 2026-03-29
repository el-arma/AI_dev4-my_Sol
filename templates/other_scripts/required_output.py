from dotenv import load_dotenv
from pydantic_ai import Agent


# =========================
# MODELS
# =========================

from pydantic import BaseModel
from typing import Any


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

# =========================
# AGENT
# =========================

load_dotenv()

agent = Agent(
    'gateway/google-vertex:gemini-2.5-flash'
)


user_prompt = "Generate some sample results."

result = agent.run_sync(user_prompt, 
                        output_type=TaskResultRequest
                        )

print(result)

# JSON:
print(result.output.model_dump_json())

# dict:
print(result.output.model_dump())