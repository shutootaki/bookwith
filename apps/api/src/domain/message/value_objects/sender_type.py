from dataclasses import dataclass
from enum import Enum


class SenderTypeEnum(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class SenderType:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SenderType value cannot be empty")

        if self.value not in SenderTypeEnum.__members__:
            raise ValueError(f"Invalid sender type: {self.value}")

    @classmethod
    def user(cls) -> "SenderType":
        return cls(SenderTypeEnum.USER.value)

    @classmethod
    def assistant(cls) -> "SenderType":
        return cls(SenderTypeEnum.ASSISTANT.value)

    @classmethod
    def from_string(cls, sender_type_str: str) -> "SenderType":
        return cls(sender_type_str)
