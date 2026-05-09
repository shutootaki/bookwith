from typing import Any

from pydantic import ConfigDict, Field

from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum
from src.presentation.api.schemas.base_schema import BaseSchemaModel, to_camel


class AnnotationSchema(BaseSchemaModel):
    # CR-4 補強: クライアントが余分な属性（user_id 等）を密入できないよう extra='forbid'.
    # alias_generator は base 由来の camelCase 変換を引き継ぐ。
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(..., max_length=64)
    book_id: str = Field(..., max_length=64)

    cfi: str = Field(..., max_length=2_000)
    color: AnnotationColorEnum
    notes: str | None = Field(None, max_length=4_000)
    spine: dict[str, Any]
    text: str = Field(..., max_length=8_000)
    type: AnnotationTypeEnum
