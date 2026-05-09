from dataclasses import dataclass

from src.domain.shared.identifiers import normalize_strict_uuid


@dataclass(frozen=True)
class ChatId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_strict_uuid(self.value, name="Chat ID"))
