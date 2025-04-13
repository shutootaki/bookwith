from datetime import datetime
from typing import Any

from src.domain.book.exceptions.book_exceptions import (
    BookAlreadyCompletedException,
    BookAlreadyStartedException,
)
from src.domain.book.value_objects.book_description import BookDescription
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_status import BookStatus, BookStatusEnum
from src.domain.book.value_objects.book_title import BookTitle


class Book:
    def __init__(
        self,
        id: BookId,
        title: BookTitle,
        user_id: str,
        file_path: str,
        description: BookDescription | None = None,
        status: BookStatus = BookStatus(BookStatusEnum.NOT_STARTED),
        author: str | None = None,
        cover_path: str | None = None,
        size: int = 0,
        cfi: str | None = None,
        percentage: float = 0,
        book_metadata: dict[str, Any] | None = None,
        definitions: list[dict[str, Any]] | None = None,
        configuration: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        completed_at: datetime | None = None,
        deleted_at: datetime | None = None,
        annotations: list[dict[str, Any]] | None = None,
    ) -> None:
        self._id = id
        self._title = title
        self._description = description
        self._status = status
        self._user_id = user_id
        self._file_path = file_path
        self._author = author
        self._cover_path = cover_path
        self._size = size
        self._cfi = cfi
        self._percentage = percentage
        self._book_metadata = book_metadata or {}
        self._definitions = definitions or []
        self._configuration = configuration or {}
        self._created_at = created_at if created_at is not None else datetime.now()
        self._updated_at = updated_at if updated_at is not None else datetime.now()
        self._completed_at = completed_at
        self._deleted_at = deleted_at
        self._annotations = annotations or []

    @classmethod
    def create(
        cls,
        title: BookTitle,
        user_id: str,
        file_path: str,
        description: BookDescription | None = None,
        author: str | None = None,
        cover_path: str | None = None,
        size: int = 0,
        book_metadata: dict[str, Any] | None = None,
    ) -> "Book":
        book_id = BookId.generate()
        return cls(
            id=book_id,
            title=title,
            user_id=user_id,
            file_path=file_path,
            description=description,
            author=author,
            cover_path=cover_path,
            size=size,
            book_metadata=book_metadata,
        )

    def update_title(self, title: BookTitle) -> None:
        self._title = title
        self._updated_at = datetime.now()

    def update_description(self, description: BookDescription) -> None:
        self._description = description
        self._updated_at = datetime.now()

    def update_reading_progress(self, cfi: str, percentage: float) -> None:
        self._cfi = cfi
        self._percentage = percentage
        self._updated_at = datetime.now()

    def start(self) -> None:
        if self._status.is_in_progress():
            raise BookAlreadyStartedException()

        if self._status.is_completed():
            self._status = BookStatus(BookStatusEnum.IN_PROGRESS)
        else:
            self._status = BookStatus(BookStatusEnum.IN_PROGRESS)

        self._updated_at = datetime.now()

    def complete(self) -> None:
        if self._status.is_completed():
            raise BookAlreadyCompletedException()

        self._status = BookStatus(BookStatusEnum.COMPLETED)
        self._completed_at = datetime.now()
        self._updated_at = datetime.now()

    def mark_as_deleted(self) -> None:
        if not self._deleted_at:
            self._deleted_at = datetime.now()
            self._updated_at = datetime.now()

    @property
    def id(self) -> BookId:
        return self._id

    @property
    def title(self) -> BookTitle:
        return self._title

    @property
    def description(self) -> BookDescription | None:
        return self._description

    @property
    def status(self) -> BookStatus:
        return self._status

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def author(self) -> str | None:
        return self._author

    @property
    def cover_path(self) -> str | None:
        return self._cover_path

    @property
    def size(self) -> int:
        return self._size

    @property
    def cfi(self) -> str | None:
        return self._cfi

    @property
    def percentage(self) -> float:
        return self._percentage

    @property
    def book_metadata(self) -> dict[str, Any]:
        return self._book_metadata

    @property
    def definitions(self) -> list[dict[str, Any]]:
        return self._definitions

    @property
    def configuration(self) -> dict[str, Any]:
        return self._configuration

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    @property
    def annotations(self) -> list[dict[str, Any]]:
        return self._annotations

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return False
        return self._id == other._id
