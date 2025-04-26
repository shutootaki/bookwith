from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base
from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO


class AnnotationDTO(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    book_id: Mapped[str] = mapped_column(String, ForeignKey("books.id"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)

    cfi: Mapped[str] = mapped_column(String, index=True)
    text: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[AnnotationColorEnum | None] = mapped_column(SQLAlchemyEnum(AnnotationColorEnum), nullable=True)
    type: Mapped[AnnotationTypeEnum] = mapped_column(
        SQLAlchemyEnum(AnnotationTypeEnum),
        default=AnnotationTypeEnum.HIGHLIGHT,
        nullable=False,
    )
    spine: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    book: Mapped["BookDTO"] = relationship("BookDTO", back_populates="annotations", uselist=False)
    user: Mapped["UserDTO"] = relationship("UserDTO", back_populates="annotations", uselist=False)

    @staticmethod
    def from_dict(data: dict) -> dict:
        result = data.copy()

        if "color" in result and isinstance(result["color"], str):
            try:
                result["color"] = AnnotationColorEnum(result["color"])
            except ValueError:
                result["color"] = None

        if "type" in result and isinstance(result["type"], str):
            try:
                result["type"] = AnnotationTypeEnum(result["type"])
            except ValueError:
                result["type"] = AnnotationTypeEnum.HIGHLIGHT

        return result
