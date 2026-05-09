from dataclasses import dataclass

from src.domain.shared.text_sanitizer import sanitize_plain_text

_MAX_ANNOTATION_NOTES = 4_000


@dataclass(frozen=True)
class AnnotationNotes:
    value: str | None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        if not isinstance(self.value, str):
            raise ValueError("Annotation notes must be a string")
        # H-15: 長さ制限 + HTML サニタイズ
        sanitized = sanitize_plain_text(self.value, max_length=_MAX_ANNOTATION_NOTES)
        object.__setattr__(self, "value", sanitized or None)

    @classmethod
    def from_string(cls, notes_str: str | None) -> "AnnotationNotes":
        """文字列からAnnotationNotesを生成"""
        return cls(notes_str)
