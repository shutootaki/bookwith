"""特定の書籍を取得するユースケース"""

from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.usecase.shared.access_control import resolve_owned_or_raise


class FindBookByIdUseCase(ABC):
    """FindBookByIdUseCaseは、IDで特定の書籍を取得するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self, book_id: str, user_id: str) -> Book:
        """IDで特定の書籍を取得する"""


class FindBookByIdUseCaseImpl(FindBookByIdUseCase):
    """FindBookByIdUseCaseImplは、IDで特定の書籍を取得するユースケース実装。"""

    def __init__(self, book_repository: BookRepository) -> None:
        self.book_repository = book_repository

    def execute(self, book_id: str, user_id: str) -> Book:
        """IDで特定の書籍を取得する。所有者が異なる場合は 403、見つからない場合は 404."""
        book_id_obj = BookId(book_id)

        book = resolve_owned_or_raise(
            find_for_user=lambda: self.book_repository.find_by_id_for_user(book_id_obj, user_id),
            find_any=lambda: self.book_repository.find_by_id(book_id_obj),
            not_found_exc=BookNotFoundException(book_id),
            forbidden_exc=BookPermissionDeniedException(),
        )
        book.assert_owned_by(user_id)
        return book
