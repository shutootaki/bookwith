from typing import Any

from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum
from src.presentation.api.schemas.base_schema import BaseSchemaModel


class AnnotationSchema(BaseSchemaModel):
    id: str
    book_id: str

    cfi: str
    color: AnnotationColorEnum
    notes: str | None = None
    spine: dict[str, Any]
    text: str
    type: AnnotationTypeEnum
