from pathlib import Path
from pydantic import BaseModel
from typing import List, Any


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

class SurvivorPersData(BaseModel):
    name: str
    surname: str
    born: int

class LocationRequest(APIKey):
    name: str
    surname: str

class AccecssRequest(APIKey):
    name: str
    surname: str
    birthYear: int

class Location(BaseModel):
    latitude: float
    longitude: float

class LocationResponse(BaseModel):
    name: str
    surname: str
    locations: List[Location]

class AccecssResponse(BaseModel):
    name: str
    surname: str
    accessLevel: int

class Candidate(BaseModel):
    name: str
    surname: str
    powerPlant: str