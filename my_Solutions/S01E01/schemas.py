from pydantic import BaseModel
from typing import Any, List


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

class WorkerTags(BaseModel):
    id: int
    tags: List[str]


class WorkersTagging(BaseModel):
    workers: List[WorkerTags]
