from dataclasses import dataclass

from src.domain.shared.text_sanitizer import sanitize_plain_text

_MAX_MESSAGE_CONTENT = 30_000


@dataclass(frozen=True)
class MessageContent:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("Message content must be a string")
        # H-15: 長さ制限 + HTML 構文ストリップ
        sanitized = sanitize_plain_text(self.value, max_length=_MAX_MESSAGE_CONTENT)
        if not sanitized:
            raise ValueError("Message content cannot be empty")
        object.__setattr__(self, "value", sanitized)
