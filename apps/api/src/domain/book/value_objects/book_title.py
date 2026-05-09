from dataclasses import dataclass

from src.domain.shared.text_sanitizer import sanitize_plain_text

# 100 字制約はメタデータ由来のタイトルに対してきつすぎるので 500 に拡張する。
_MAX_BOOK_TITLE = 500


@dataclass(frozen=True)
class BookTitle:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("Book title must be a string")
        sanitized = sanitize_plain_text(self.value, max_length=_MAX_BOOK_TITLE)
        if not sanitized:
            raise ValueError("タイトルは必須です")
        object.__setattr__(self, "value", sanitized)
