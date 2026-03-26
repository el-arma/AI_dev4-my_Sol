from pydantic import BaseModel
from typing import Any, List, Literal, Optional, Union


Number = Union[int, float]

class CalculatorInput(BaseModel):
    operation: Literal["add", "multiply", "subtract", "divide", "sum"]

    a: Optional[Number] = None
    b: Optional[Number] = None

    operands: Optional[List[Number]] = None

class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

class Answer(BaseModel):
    declaration: str