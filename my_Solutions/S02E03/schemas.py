from pydantic import BaseModel, Field
from typing import Any, List
# from pydantic import BaseModel, Field
# from typing import Any, List, Literal


class APIKey(BaseModel):
    apikey: str

class Answer(BaseModel):
    logs: str

class TaskResultRequest(APIKey):
    task: str
    answer: Answer


    


# class Input(BaseModel):
#     context: List[dict] = Field(..., description="Context for the agent")

# class SurvivorPersData(BaseModel):
#     name: str
#     surname: str
#     born: int

# class LocationRequest(APIKey):
#     name: str
#     surname: str

# class AccecssRequest(APIKey):
#     name: str
#     surname: str
#     birthYear: int

# class Location(BaseModel):
#     latitude: float
#     longitude: float

# class LocationResponse(BaseModel):
#     name: str
#     surname: str
#     locations: List[Location]

# class AccecssResponse(BaseModel):
#     name: str
#     surname: str
#     accessLevel: int

# class Candidate(BaseModel):
#     name: str
#     surname: str
#     powerPlant: str

# class QueryToAgent(BaseModel):
#     sessionID: str
#     msg: str

# class AgentResponse(BaseModel):
#     msg: str

# class PackageRequest(BaseModel):
#     apikey: str  = Field("placeholder", description="No worries, will be injected")
#     action: str = Field(
#         ...,
#         description="Operation to perform in the logistics system. Use 'check' to retrieve package status."
#     )
#     packageid: str = Field(
#         ...,
#         description="Unique alphanumeric package identifier in the logistics system. Used to check current status, location, and processing details."
#     )

# class RedirectPackageRequest(BaseModel):
#     apikey: str  = Field("placeholder", description="No worries, will be injected")
#     action: Literal["redirect"] = Field(
#         ...,
#         description="Must be 'redirect'. Used to change the delivery destination of a package."
#     )
#     packageid: str = Field(
#         ...,
#         description="Unique alphanumeric package identifier in the logistics system. Identifies which package should be redirected."
#     )
#     destination: str = Field(
#         ...,
#         description="Target destination code where the package should be redirected."
#     )
#     code: str = Field(
#         ...,
#         description="Security authorization code provided by the operator during the conversation. Required to approve the redirection."
#     )

# class WeatherRequest(BaseModel):
#     city: str = Field(..., description="City name to check weather for")