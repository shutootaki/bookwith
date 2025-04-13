from dataclasses import dataclass
from enum import Enum


class AnnotationTypeEnum(Enum):
    """アノテーションタイプ列挙型"""

    HIGHLIGHT = "highlight"
    # 将来的に他のタイプが追加される可能性があります


@dataclass(frozen=True)
class AnnotationType:
    value: str

    def __post_init__(self):
        if not any(self.value == type_.value for type_ in AnnotationTypeEnum):
            raise ValueError(f"Invalid annotation type: {self.value}")

    @classmethod
    def highlight(cls) -> "AnnotationType":
        """ハイライトタイプのアノテーションを作成"""
        return cls(AnnotationTypeEnum.HIGHLIGHT.value)

    @classmethod
    def default(cls) -> "AnnotationType":
        """デフォルトタイプのアノテーションを作成"""
        return cls.highlight()

    @classmethod
    def from_string(cls, type_str: str | None) -> "AnnotationType":
        """文字列からAnnotationTypeを生成"""
        if not type_str:
            return cls.default()
        return cls(type_str)
