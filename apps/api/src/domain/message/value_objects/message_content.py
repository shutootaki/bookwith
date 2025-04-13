from dataclasses import dataclass


@dataclass(frozen=True)
class MessageContent:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Message content cannot be empty")

        if len(self.value) > 5000:
            raise ValueError("Message content must be 5000 characters or less")
