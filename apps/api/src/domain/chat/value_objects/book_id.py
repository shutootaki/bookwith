from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BookId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Book ID is required")
        try:
            UUID(self.value)
        except ValueError:
            raise ValueError("Book ID must be a valid UUID")
