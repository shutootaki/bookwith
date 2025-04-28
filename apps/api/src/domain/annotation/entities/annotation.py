from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from src.domain.annotation.value_objects.annotation_cfi import AnnotationCfi
from src.domain.annotation.value_objects.annotation_color import AnnotationColor
from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.domain.annotation.value_objects.annotation_notes import AnnotationNotes
from src.domain.annotation.value_objects.annotation_text import AnnotationText
from src.domain.annotation.value_objects.annotation_type import AnnotationType


class Annotation(BaseModel):
    id: AnnotationId
    book_id: str

    cfi: AnnotationCfi
    color: AnnotationColor
    notes: AnnotationNotes | None = None
    spine: dict[str, Any] | None = None
    text: AnnotationText
    type: AnnotationType

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Value Object を許容するため
        json_encoders={
            AnnotationId: lambda x: x.value,
            AnnotationCfi: lambda x: x.value,
            AnnotationColor: lambda x: x.value,
            AnnotationType: lambda x: x.value,
            AnnotationText: lambda x: x.value,
            AnnotationNotes: lambda x: x.value,
        },
    )

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, Annotation):
            return self.id == obj.id
        return False

    @field_validator("id", mode="before")
    @classmethod
    def _validate_id(cls, v):
        if isinstance(v, AnnotationId):
            return v
        return AnnotationId(v)

    @field_validator("cfi", mode="before")
    @classmethod
    def _validate_cfi(cls, v):
        if isinstance(v, AnnotationCfi):
            return v
        return AnnotationCfi(v)

    @field_validator("text", mode="before")
    @classmethod
    def _validate_text(cls, v):
        if isinstance(v, AnnotationText):
            return v
        return AnnotationText(v)

    @field_validator("notes", mode="before")
    @classmethod
    def _validate_notes(cls, v):
        if v is None or isinstance(v, AnnotationNotes):
            return v
        return AnnotationNotes(v)

    @field_validator("color", mode="before")
    @classmethod
    def _validate_color(cls, v):
        if isinstance(v, AnnotationColor):
            return v
        return AnnotationColor(v)

    @field_validator("type", mode="before")
    @classmethod
    def _validate_type(cls, v):
        if isinstance(v, AnnotationType):
            return v
        return AnnotationType(v)

    @field_validator("spine", mode="before")
    @classmethod
    def _validate_spine(cls, v):
        # dict 型ならそのまま。必要なら更に検証を追加
        if isinstance(v, dict):
            return v
        raise TypeError("spine must be a dict")

    @classmethod
    def create(
        cls,
        book_id: str,
        cfi: str,
        text: str,
        notes: str | None = None,
        color: str | None = None,
        type: str | None = None,
        spine: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> "Annotation":
        return cls(
            id=AnnotationId.from_string(id),
            book_id=book_id,
            cfi=AnnotationCfi.from_string(cfi),
            text=AnnotationText.from_string(text),
            notes=AnnotationNotes.from_string(notes),
            color=AnnotationColor.from_string(color),
            type=AnnotationType.from_string(type),
            spine=spine,
        )
