from abc import ABC, abstractmethod

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)


class UpdateAnnotationUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        annotation_id: str,
        text: str | None = None,
        notes: str | None = None,
        color: str | None = None,
    ) -> Annotation:
        pass


class UpdateAnnotationUseCaseImpl(UpdateAnnotationUseCase):
    def __init__(self, annotation_repository: AnnotationRepository) -> None:
        self.annotation_repository = annotation_repository

    def execute(
        self,
        annotation_id: str,
        text: str | None = None,
        notes: str | None = None,
        color: str | None = None,
    ) -> Annotation:
        pass
