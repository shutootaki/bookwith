from abc import ABC, abstractmethod

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import AnnotationRepository
from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.presentation.api.schemas.annotation_schema import AnnotationSchema


class SyncAnnotationsUseCase(ABC):
    """アノテーション保存ユースケースのインターフェース"""

    @abstractmethod
    def execute(
        self,
        book_id: str,
        annotations: list[AnnotationSchema] | None = None,
    ) -> None:
        """アノテーションを更新する"""


class SyncAnnotationsUseCaseImpl(SyncAnnotationsUseCase):
    """アノテーション保存ユースケースの実装"""

    def __init__(
        self,
        annotation_repository: AnnotationRepository,
        book_repository: BookRepository,
    ) -> None:
        self.annotation_repository = annotation_repository
        self.book_repository = book_repository

    def execute(
        self,
        book_id: str,
        annotations: list[AnnotationSchema] | None = None,
    ) -> None:
        """アノテーションを更新する"""
        book_id_obj = BookId(book_id)
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        if annotations is not None:
            book.annotations = [Annotation(**annotation.model_dump(mode="json")) for annotation in annotations]

        self.annotation_repository.sync_annotations(book=book)
