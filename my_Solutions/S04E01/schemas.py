from pydantic import BaseModel, Field
from typing import Any
# from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

class SensorLogCheck(BaseModel):
    logs_batch: Dict[str, bool]
