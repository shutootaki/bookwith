from dataclasses import dataclass


@dataclass(frozen=True)
class ChatTitle:
    value: str

    def __post_init__(self) -> None:
        if self.value and len(self.value) > 255:
            raise ValueError("Chat title must be 255 characters or less")
