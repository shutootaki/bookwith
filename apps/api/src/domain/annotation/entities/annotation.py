from datetime import datetime
from typing import Any

from src.domain.annotation.value_objects.annotation_cfi import AnnotationCfi
from src.domain.annotation.value_objects.annotation_color import AnnotationColor
from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.domain.annotation.value_objects.annotation_notes import AnnotationNotes
from src.domain.annotation.value_objects.annotation_text import AnnotationText
from src.domain.annotation.value_objects.annotation_type import AnnotationType


class Annotation:
    def __init__(
        self,
        id: AnnotationId,
        book_id: str,
        user_id: str,
        cfi: AnnotationCfi,
        text: AnnotationText,
        notes: AnnotationNotes | None = None,
        color: AnnotationColor | None = None,
        type: AnnotationType | None = None,
        spine: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._id = id
        self._book_id = book_id
        self._user_id = user_id
        self._cfi = cfi
        self._text = text
        self._notes = notes if notes is not None else AnnotationNotes(None)
        self._color = color if color is not None else AnnotationColor(None)
        self._type = type if type is not None else AnnotationType.default()
        self._spine = spine
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, Annotation):
            return self._id == obj._id
        return False

    @property
    def id(self) -> AnnotationId:
        return self._id

    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def cfi(self) -> AnnotationCfi:
        return self._cfi

    @property
    def text(self) -> AnnotationText:
        return self._text

    @property
    def notes(self) -> AnnotationNotes:
        return self._notes

    @property
    def color(self) -> AnnotationColor:
        return self._color

    @property
    def type(self) -> AnnotationType:
        return self._type

    @property
    def spine(self) -> dict[str, Any] | None:
        return self._spine

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @classmethod
    def create(
        cls,
        book_id: str,
        user_id: str,
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
            user_id=user_id,
            cfi=AnnotationCfi.from_string(cfi),
            text=AnnotationText.from_string(text),
            notes=AnnotationNotes.from_string(notes),
            color=AnnotationColor.from_string(color),
            type=AnnotationType.from_string(type),
            spine=spine,
        )
