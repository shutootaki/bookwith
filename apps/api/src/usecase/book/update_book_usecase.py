from abc import ABC, abstractmethod
from typing import Any

from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.presentation.api.schemas.annotation_schema import AnnotationSchema
from src.usecase.shared.access_control import resolve_owned_or_raise


class UpdateBookUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        book_id: str,
        user_id: str,
        name: str | None = None,
        author: str | None = None,
        cfi: str | None = None,
        percentage: float | None = None,
        annotations: list[AnnotationSchema] | None = None,
        book_metadata: dict[str, Any] | None = None,
        definitions: list[str] | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> Book:
        pass


class UpdateBookUseCaseImpl(UpdateBookUseCase):
    def __init__(self, book_repository: BookRepository) -> None:
        self.book_repository = book_repository

    def execute(
        self,
        book_id: str,
        user_id: str,
        name: str | None = None,
        author: str | None = None,
        cfi: str | None = None,
        percentage: float | None = None,
        annotations: list[AnnotationSchema] | None = None,
        book_metadata: dict[str, Any] | None = None,
        definitions: list[str] | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> Book:
        book_id_obj = BookId(book_id)
        book = resolve_owned_or_raise(
            find_for_user=lambda: self.book_repository.find_by_id_for_user(book_id_obj, user_id),
            find_any=lambda: self.book_repository.find_by_id(book_id_obj),
            not_found_exc=BookNotFoundException(book_id),
            forbidden_exc=BookPermissionDeniedException(),
        )
        book.assert_owned_by(user_id)

        if name is not None and name != book.name.value:
            book_title = BookTitle(name)
            book.update_title(book_title)

        if author is not None:
            book.author = author

        if cfi is not None or percentage is not None:
            current_cfi = cfi if cfi is not None else book.cfi
            current_percentage = percentage if percentage is not None else book.percentage
            if current_cfi is not None:
                book.update_reading_progress(current_cfi, current_percentage)

        if book_metadata is not None:
            metadata_keys = (
                "title",
                "creator",
                "description",
                "pubdate",
                "publisher",
                "identifier",
                "language",
                "rights",
                "modified_date",
                "layout",
                "orientation",
                "flow",
                "viewport",
                "spread",
            )
            for key in metadata_keys:
                attr = f"metadata_{key}"
                setattr(book, attr, book_metadata.get(key, getattr(book, attr)))

        if definitions is not None:
            book.definitions = definitions

        if configuration is not None:
            book.configuration = configuration

        if annotations is not None:
            # Annotation の book_id をパス引数で強制的に上書きする (権限境界の防御)。
            normalized: list[Annotation] = []
            for annotation in annotations:
                payload = annotation.model_dump(mode="json")
                payload["book_id"] = book_id
                normalized.append(Annotation(**payload))
            book.annotations = normalized

        self.book_repository.save(book)

        return book
