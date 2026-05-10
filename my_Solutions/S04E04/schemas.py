from pydantic import BaseModel
from typing import Any, Dict, Literal


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any
