from abc import ABC, abstractmethod
from typing import Any

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)


class CreateAnnotationUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        book_id: str,
        user_id: str,
        cfi: str,
        text: str,
        notes: str | None = None,
        color: str | None = None,
        type: str | None = None,
        spine: dict[str, Any] | None = None,
    ) -> Annotation:
        pass


class CreateAnnotationUseCaseImpl(CreateAnnotationUseCase):
    def __init__(self, annotation_repository: AnnotationRepository) -> None:
        self.annotation_repository = annotation_repository

    def execute(
        self,
        book_id: str,
        user_id: str,
        cfi: str,
        text: str,
        notes: str | None = None,
        color: str | None = None,
        type: str | None = None,
        spine: dict[str, Any] | None = None,
    ) -> Annotation:
        annotation = Annotation.create(
            book_id=book_id,
            user_id=user_id,
            cfi=cfi,
            text=text,
            notes=notes,
            color=color,
            type=type,
            spine=spine,
        )
        self.annotation_repository.save(annotation)
        return annotation
