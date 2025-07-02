from dataclasses import dataclass


@dataclass(frozen=True)
class AnnotationNotes:
    value: str | None

    def __post_init__(self) -> None:
        if self.value is not None and not isinstance(self.value, str):
            raise ValueError("Annotation notes must be a string")

    @classmethod
    def from_string(cls, notes_str: str | None) -> "AnnotationNotes":
        """文字列からAnnotationNotesを生成"""
        return cls(notes_str)
