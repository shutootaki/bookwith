import uuid
from dataclasses import dataclass

from src.domain.shared.identifiers import normalize_strict_uuid


@dataclass(frozen=True)
class AnnotationId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            normalize_strict_uuid(self.value, name="AnnotationId", generate_if_empty=True),
        )

    @classmethod
    def new(cls) -> "AnnotationId":
        """新しいIDを生成"""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, id_str: str | None) -> "AnnotationId":
        """文字列からAnnotationIdを生成"""
        if not id_str:
            return cls.new()
        return cls(id_str)
