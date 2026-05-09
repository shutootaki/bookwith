from dataclasses import dataclass

from src.domain.shared.text_sanitizer import sanitize_plain_text

# 注釈本文の最大長。EPUB の章まるごとを切り取られても受け止める。
_MAX_ANNOTATION_TEXT = 8_000


@dataclass(frozen=True)
class AnnotationText:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("Annotation text must be a string")
        # H-15: 長さ制限 + HTML 構文ストリップ
        sanitized = sanitize_plain_text(self.value, max_length=_MAX_ANNOTATION_TEXT)
        if not sanitized:
            raise ValueError("Annotation text is required")
        object.__setattr__(self, "value", sanitized)

    @classmethod
    def from_string(cls, text_str: str) -> "AnnotationText":
        """文字列からAnnotationTextを生成"""
        return cls(text_str)
