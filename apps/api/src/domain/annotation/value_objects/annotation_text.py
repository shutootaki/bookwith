from dataclasses import dataclass


@dataclass(frozen=True)
class AnnotationText:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Annotation text is required")
        if not isinstance(self.value, str):
            raise ValueError("Annotation text must be a string")

    @classmethod
    def from_string(cls, text_str: str) -> "AnnotationText":
        """文字列からAnnotationTextを生成"""
        return cls(text_str)
