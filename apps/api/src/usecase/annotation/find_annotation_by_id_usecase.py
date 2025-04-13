"""
アノテーションをIDで検索するユースケース
"""

from abc import ABC, abstractmethod

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.exceptions.annotation_exceptions import (
    AnnotationNotFoundError,
)
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)
from src.domain.annotation.value_objects.annotation_id import AnnotationId


class FindAnnotationByIdUseCase(ABC):
    """アノテーションをIDで検索するユースケースのインターフェース"""

    @abstractmethod
    def execute(self, annotation_id: str) -> Annotation:
        """IDでアノテーションを検索する"""
        pass


class FindAnnotationByIdUseCaseImpl(FindAnnotationByIdUseCase):
    """アノテーションをIDで検索するユースケースの実装"""

    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository

    def execute(self, annotation_id: str) -> Annotation:
        """IDでアノテーションを検索する"""
        annotation = self.annotation_repository.find_by_id(AnnotationId(annotation_id))
        if annotation is None:
            raise AnnotationNotFoundError(annotation_id)
        return annotation
