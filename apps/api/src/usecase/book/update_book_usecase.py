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
            # Update individual metadata fields
            book.metadata_title = book_metadata.get('title', book.metadata_title)
            book.metadata_creator = book_metadata.get('creator', book.metadata_creator)
            book.metadata_description = book_metadata.get('description', book.metadata_description)
            book.metadata_pubdate = book_metadata.get('pubdate', book.metadata_pubdate)
            book.metadata_publisher = book_metadata.get('publisher', book.metadata_publisher)
            book.metadata_identifier = book_metadata.get('identifier', book.metadata_identifier)
            book.metadata_language = book_metadata.get('language', book.metadata_language)
            book.metadata_rights = book_metadata.get('rights', book.metadata_rights)
            book.metadata_modified_date = book_metadata.get('modified_date', book.metadata_modified_date)
            book.metadata_layout = book_metadata.get('layout', book.metadata_layout)
            book.metadata_orientation = book_metadata.get('orientation', book.metadata_orientation)
            book.metadata_flow = book_metadata.get('flow', book.metadata_flow)
            book.metadata_viewport = book_metadata.get('viewport', book.metadata_viewport)
            book.metadata_spread = book_metadata.get('spread', book.metadata_spread)

        if definitions is not None:
            book.definitions = definitions

        if configuration is not None:
            book.configuration = configuration

        if annotations is not None:
            book.annotations = [Annotation(**annotation.model_dump(mode="json")) for annotation in annotations]

        self.book_repository.save(book)

        return book
