from pydantic import BaseModel

class QueryToAgent(BaseModel):
    msg: str

class AgentResponse(BaseModel):
    msg: str
