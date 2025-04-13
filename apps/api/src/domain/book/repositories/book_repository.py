from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.value_objects.book_id import BookId


class BookRepository(ABC):
    @abstractmethod
    def save(self, book: Book) -> None:
        pass

    @abstractmethod
    def find_by_id(self, book_id: BookId) -> Book | None:
        pass

    @abstractmethod
    def find_all(self) -> list[Book]:
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[Book]:
        pass

    @abstractmethod
    def delete(self, book_id: BookId) -> None:
        pass

    @abstractmethod
    def bulk_delete(self, book_ids: list[BookId]) -> list[BookId]:
        pass
