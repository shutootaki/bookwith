from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("User ID is required")
        try:
            UUID(self.value)
        except ValueError:
            raise ValueError("User ID must be a valid UUID")
