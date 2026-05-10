from pydantic import BaseModel
from typing import Any, Dict, Literal


class APIKey(BaseModel):
    apikey: str

class TaskResultRequest(APIKey):
    task: str
    answer: Any

# ======================================================================
# S04E02 — Wind Turbine Scheduler
# ======================================================================

class TurbineSlotConfig(BaseModel):
    pitchAngle: int
    turbineMode: Literal["production", "idle"]
    unlockCode: str | None = None

class TurbineConfigAction(BaseModel):
    action: Literal["config"]
    configs: Dict[str, TurbineSlotConfig]  # key: "YYYY-MM-DD HH:00:00"

class TurbineScheduleAnswer(BaseModel):
    answer: TurbineConfigAction