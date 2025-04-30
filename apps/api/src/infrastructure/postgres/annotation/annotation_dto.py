from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.db import Base
from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO


class AnnotationDTO(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    book_id: Mapped[str] = mapped_column(String, ForeignKey("books.id"), index=True)

    cfi: Mapped[str] = mapped_column(String, index=True)
    text: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[AnnotationColorEnum | None] = mapped_column(SQLAlchemyEnum(AnnotationColorEnum), nullable=True)
    type: Mapped[AnnotationTypeEnum] = mapped_column(SQLAlchemyEnum(AnnotationTypeEnum), default=AnnotationTypeEnum.HIGHLIGHT, nullable=False)
    spine: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    book: Mapped["BookDTO"] = relationship("BookDTO", back_populates="annotations", uselist=False)

    @staticmethod
    def from_dict(data: dict) -> "AnnotationDTO":
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

        return AnnotationDTO(**result)

    @staticmethod
    def enum_name_safe(a: Annotation) -> dict[str, Any]:
        annotation_data = a.model_dump(mode="json", exclude_unset=True)

        color_val = getattr(a, "color", None)
        if isinstance(color_val, AnnotationColorEnum):
            annotation_data["color"] = color_val.name
        elif isinstance(annotation_data.get("color"), str):
            try:
                annotation_data["color"] = AnnotationColorEnum(annotation_data["color"]).name
            except ValueError:
                annotation_data["color"] = None
        elif "color" in annotation_data and annotation_data["color"] is None:
            annotation_data["color"] = None

        type_val = getattr(a, "type", None)
        if isinstance(type_val, AnnotationTypeEnum):
            annotation_data["type"] = type_val.name
        elif isinstance(annotation_data.get("type"), str):
            try:
                annotation_data["type"] = AnnotationTypeEnum(annotation_data["type"]).name
            except ValueError:
                annotation_data["type"] = AnnotationTypeEnum.HIGHLIGHT.name

        return annotation_data
