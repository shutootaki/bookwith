import enum
import re
import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship

from src.db import Base
from src.infrastructure.database.models import TimestampMixin


class AnnotationDTO(Base, TimestampMixin):
    """アノテーション（注釈、ハイライト）モデル.
    アノテーションデータとORM（SQLAlchemy）モデル間の変換を行うDTOクラス.
    """

    class AnnotationTypeEnum(enum.Enum):
        highlight = "highlight"

    class AnnotationColorEnum(enum.Enum):
        yellow = "yellow"
        red = "red"
        green = "green"
        blue = "blue"

    __tablename__ = "annotations"

    id = Column(String, primary_key=True, index=True)
    book_id = Column(String, ForeignKey("books.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    cfi = Column(String, index=True)
    text = Column(Text)
    notes = Column(Text, nullable=True)
    color = Column(SQLAlchemyEnum(AnnotationColorEnum), nullable=True)
    type = Column(
        SQLAlchemyEnum(AnnotationTypeEnum),
        default=AnnotationTypeEnum.highlight,
        nullable=False,
    )
    spine = Column(JSON, nullable=True)

    book = relationship("BookDTO", back_populates="annotations")
    user = relationship("User", back_populates="annotations")

    @staticmethod
    def from_api_dict(annotation_dict: dict[str, Any], book_id: str = None) -> dict[str, Any]:
        result = {}

        # 特定のキーの明示的なマッピング
        key_mapping = {
            "bookId": "book_id",
            "userId": "user_id",
            "createAt": "created_at",
            "updateAt": "updated_at",
            # 必要に応じて他のキーも追加
        }

        for key, value in annotation_dict.items():
            if key in key_mapping:
                result_key = key_mapping[key]
            else:
                result_key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower()

            result[result_key] = value

        # book_idが指定されていれば追加（新規作成時に使用）
        if book_id and "book_id" not in result:
            result["book_id"] = book_id

        # idがなければ新規生成（新規作成時に使用）
        if "id" not in result:
            result["id"] = str(uuid.uuid4())

        return result

    @staticmethod
    def to_api_dict(annotation: "AnnotationDTO") -> dict[str, Any]:
        data = {
            "id": annotation.id,
            "bookId": annotation.book_id,
            "userId": annotation.user_id,
            "cfi": annotation.cfi,
            "text": annotation.text,
            "notes": annotation.notes,
            "color": annotation.color.value if annotation.color else None,
            "type": annotation.type.value,
            "spine": annotation.spine,
            "createdAt": annotation.created_at.isoformat() if annotation.created_at else None,
            "updatedAt": annotation.updated_at.isoformat() if annotation.updated_at else None,
        }

        return data

    @staticmethod
    def create_annotation(annotation_dict: dict[str, Any], book_id: str) -> "AnnotationDTO":
        orm_dict = AnnotationDTO.from_api_dict(annotation_dict, book_id)
        return AnnotationDTO(**orm_dict)

    @staticmethod
    def update_annotation(annotation: "AnnotationDTO", annotation_dict: dict[str, Any]) -> None:
        orm_dict = AnnotationDTO.from_api_dict(annotation_dict)

        if "id" in orm_dict:
            del orm_dict["id"]

        for key, value in orm_dict.items():
            if hasattr(annotation, key):
                setattr(annotation, key, value)
