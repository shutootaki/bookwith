from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository


class FindBooksUseCase(ABC):
    @abstractmethod
    def execute(self) -> list[Book]:
        pass


class FindBooksUseCaseImpl(FindBooksUseCase):
    def __init__(self, book_repository: BookRepository) -> None:
        self.book_repository = book_repository

    def execute(self) -> list[Book]:
        return self.book_repository.find_all()


class FindBooksByUserIdUseCase(ABC):
    @abstractmethod
    def execute(self, user_id: str) -> list[Book]:
        pass


class FindBooksByUserIdUseCaseImpl(FindBooksByUserIdUseCase):
    def __init__(self, book_repository: BookRepository) -> None:
        self.book_repository = book_repository

    def execute(self, user_id: str) -> list[Book]:
        return self.book_repository.find_by_user_id(user_id)
