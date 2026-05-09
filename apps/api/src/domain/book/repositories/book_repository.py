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
    def find_by_id_for_user(self, book_id: BookId, user_id: str) -> Book | None:
        """CR-3: 指定 user_id の所有する Book のみ返す."""

    @abstractmethod
    def find_by_ids_for_user(self, book_ids: list[BookId], user_id: str) -> list[Book]:
        """CR-3: 指定 user_id 所有の book のみを単一クエリで返す（bulk 操作の N+1 防止）."""

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[Book]:
        pass

    @abstractmethod
    def delete_for_user(self, book_id: BookId, user_id: str) -> bool:
        """CR-3: 指定 user_id 所有の book のみ論理削除。削除した場合 True."""

    @abstractmethod
    def bulk_delete_for_user(self, book_ids: list[BookId], user_id: str) -> list[BookId]:
        """CR-3: 指定 user_id 所有のもののみ削除。"""
