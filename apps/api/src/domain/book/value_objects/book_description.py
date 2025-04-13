from dataclasses import dataclass


@dataclass(frozen=True)
class BookDescription:
    value: str | None = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("説明は1000文字以下である必要があります")
