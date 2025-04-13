"""書籍一覧取得のユースケース"""

from abc import ABC, abstractmethod
from typing import List

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository


class FindBooksUseCase(ABC):
    """FindBooksUseCaseは、すべての書籍を取得するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self) -> List[Book]:
        """すべての書籍を取得する"""
        pass


class FindBooksUseCaseImpl(FindBooksUseCase):
    """FindBooksUseCaseImplは、すべての書籍を取得するユースケースの実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(self) -> List[Book]:
        """すべての書籍を取得する"""
        return self.book_repository.find_all()


class FindBooksByUserIdUseCase(ABC):
    """FindBooksByUserIdUseCaseは、特定のユーザーの書籍を取得するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self, user_id: str) -> List[Book]:
        """特定のユーザーのすべての書籍を取得する"""
        pass


class FindBooksByUserIdUseCaseImpl(FindBooksByUserIdUseCase):
    """FindBooksByUserIdUseCaseImplは、特定のユーザーの書籍を取得するユースケースの実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(self, user_id: str) -> List[Book]:
        """特定のユーザーのすべての書籍を取得する"""
        return self.book_repository.find_by_user_id(user_id)
