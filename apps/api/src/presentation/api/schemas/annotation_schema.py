from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum


class AnnotationSchema(BaseModel):
    id: str
    book_id: str = Field(alias="bookId")
    cfi: str
    spine: dict[str, Any]
    type: AnnotationTypeEnum
    color: AnnotationColorEnum
    notes: str | None = None
    text: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
