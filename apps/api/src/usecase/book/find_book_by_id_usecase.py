"""特定の書籍を取得するユースケース"""

from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId


class FindBookByIdUseCase(ABC):
    """FindBookByIdUseCaseは、IDで特定の書籍を取得するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self, book_id: str) -> Book:
        """IDで特定の書籍を取得する"""
        pass


class FindBookByIdUseCaseImpl(FindBookByIdUseCase):
    """FindBookByIdUseCaseImplは、IDで特定の書籍を取得するユースケース実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(self, book_id: str) -> Book:
        """IDで特定の書籍を取得する。見つからない場合は例外を発生させる。"""
        book_id_obj = BookId(book_id)
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        return book
