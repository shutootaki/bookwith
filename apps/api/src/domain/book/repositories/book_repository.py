from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.value_objects.book_id import BookId


class BookRepository(ABC):
    @abstractmethod
    def save(self, book: Book) -> None:
        """Bookを保存する"""

    @abstractmethod
    def find_by_id(self, book_id: BookId) -> Book | None:
        """IDでBookを検索する"""

    @abstractmethod
    def find_all(self) -> list[Book]:
        """全てのBookを取得する"""

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[Book]:
        """ユーザーIDに紐づくBookを全て取得する"""

    @abstractmethod
    def delete(self, book_id: BookId) -> None:
        """IDでBookを削除する（論理削除）"""

    @abstractmethod
    def bulk_delete(self, book_ids: list[BookId]) -> list[BookId]:
        """複数のIDでBookを一括削除する（論理削除）。削除されたIDのリストを返す"""
