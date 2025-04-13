import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageId value cannot be empty")

        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError("MessageId must be a valid UUID")

    @classmethod
    def generate(cls) -> "MessageId":
        return cls(str(uuid.uuid4()))
