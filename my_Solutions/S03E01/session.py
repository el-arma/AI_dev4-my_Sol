from dataclasses import dataclass, field
from pydantic import BaseModel
from typing import Any

class ContextItem(BaseModel):
    description: str
    value: Any

@dataclass
class ContextSessionManager:
    items: dict[str, ContextItem] = field(default_factory=dict)

    def put(self, key: str, value: Any, description: str):
        self.items[key] = ContextItem(description=description, value=value)