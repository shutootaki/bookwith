from abc import ABC, abstractmethod
from typing import Any

from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.presentation.api.schemas.annotation_schema import AnnotationSchema


class UpdateBookUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        book_id: str,
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
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        if name is not None and name != book.name.value:
            book_title = BookTitle(name)
            book.update_title(book_title)

        if author is not None:
            book.author = author

        if cfi is not None or percentage is not None:
            current_cfi = "" if book.cfi is None and cfi is None else cfi if cfi is not None else book.cfi

            current_percentage = percentage if percentage is not None else book.percentage
            if current_cfi is not None:
                book.update_reading_progress(current_cfi, current_percentage)

        if book_metadata is not None:
            book.book_metadata = book_metadata

        if definitions is not None:
            book.definitions = definitions

        if configuration is not None:
            book.configuration = configuration

        if annotations is not None:
            book.annotations = [Annotation(**annotation.model_dump(mode="json")) for annotation in annotations]

        self.book_repository.save(book)

        return book
