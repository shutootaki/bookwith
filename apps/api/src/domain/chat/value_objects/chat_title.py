from dataclasses import dataclass

from src.domain.shared.text_sanitizer import sanitize_plain_text


@dataclass(frozen=True)
class ChatTitle:
    value: str

    def __post_init__(self) -> None:
        # B-14: 空文字を許容しない。H-15: 制御文字・HTML 構文をストリップする。
        if self.value is None:
            raise ValueError("Chat title is required")
        sanitized = sanitize_plain_text(self.value, max_length=255)
        if not sanitized:
            raise ValueError("Chat title must not be empty")
        # frozen dataclass なので object.__setattr__ で書き換える。
        object.__setattr__(self, "value", sanitized)
