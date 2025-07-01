from dataclasses import dataclass


@dataclass(frozen=True)
class BookTitle:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("タイトルは必須です")
        if len(self.value) > 100:
            raise ValueError("タイトルは100文字以下である必要があります")
