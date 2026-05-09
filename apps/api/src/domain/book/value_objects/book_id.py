import uuid
from dataclasses import dataclass

from src.domain.shared.identifiers import normalize_strict_uuid


@dataclass(frozen=True)
class BookId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_strict_uuid(self.value, name="BookId"))

    @classmethod
    def generate(cls) -> "BookId":
        return cls(str(uuid.uuid4()))
