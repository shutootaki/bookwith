from abc import ABC, abstractmethod

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import AnnotationRepository
from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.presentation.api.schemas.annotation_schema import AnnotationSchema
from src.usecase.shared.access_control import resolve_owned_or_raise


class SyncAnnotationsUseCase(ABC):
    """アノテーション保存ユースケースのインターフェース"""

    @abstractmethod
    def execute(
        self,
        book_id: str,
        user_id: str,
        annotations: list[AnnotationSchema] | None = None,
    ) -> None:
        """アノテーションを更新する（所有者検証込み）"""


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
        user_id: str,
        annotations: list[AnnotationSchema] | None = None,
    ) -> None:
        """アノテーションを更新する（所有者検証込み）"""
        book_id_obj = BookId(book_id)
        book = resolve_owned_or_raise(
            find_for_user=lambda: self.book_repository.find_by_id_for_user(book_id_obj, user_id),
            find_any=lambda: self.book_repository.find_by_id(book_id_obj),
            not_found_exc=BookNotFoundException(book_id),
            forbidden_exc=BookPermissionDeniedException(),
        )
        book.assert_owned_by(user_id)

        if annotations is not None:
            # book_id をパス引数で強制上書きし、Annotation 側でも整合性を主張させる (権限境界の防御)。
            normalized: list[Annotation] = []
            for annotation in annotations:
                payload = annotation.model_dump(mode="json")
                payload["book_id"] = book_id
                ann = Annotation(**payload)
                ann.assert_belongs_to_book(book_id)
                normalized.append(ann)
            book.annotations = normalized

        self.annotation_repository.sync_annotations(book=book)
