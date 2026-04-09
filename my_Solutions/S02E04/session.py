from uuid import uuid4, UUID
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ContextSessionManager:
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    content: Any = None

    def get_ctx(self) -> Any:
        return self.content

    def save_ctx(self, new_content: Any) -> None:
        self.content = new_content

