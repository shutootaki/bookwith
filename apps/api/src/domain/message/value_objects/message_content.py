from dataclasses import dataclass


@dataclass(frozen=True)
class MessageContent:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Message content cannot be empty")
