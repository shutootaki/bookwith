from abc import ABC, abstractmethod

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.value_objects.annotation_id import AnnotationId


class AnnotationRepository(ABC):
    @abstractmethod
    def save(self, annotation: Annotation) -> None:
        pass

    @abstractmethod
    def find_by_id(self, annotation_id: AnnotationId) -> Annotation | None:
        pass

    @abstractmethod
    def find_all(self) -> list[Annotation]:
        pass

    @abstractmethod
    def find_by_book_id(self, book_id: str) -> list[Annotation]:
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[Annotation]:
        pass

    @abstractmethod
    def find_by_book_id_and_user_id(self, book_id: str, user_id: str) -> list[Annotation]:
        pass

    @abstractmethod
    def delete(self, annotation_id: AnnotationId) -> None:
        pass
