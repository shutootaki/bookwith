from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ChatId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Chat ID is required")
        try:
            UUID(self.value)
        except ValueError:
            raise ValueError("Chat ID must be a valid UUID")
