from fastapi import Depends
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.book.repositories.book_repository import BookRepository
from src.infrastructure.postgres.book.book_repository import PostgresBookRepository
from src.usecase.book.create_book_usecase import (
    CreateBookUseCase,
    CreateBookUseCaseImpl,
)
from src.usecase.book.delete_book_usecase import (
    BulkDeleteBooksUseCase,
    BulkDeleteBooksUseCaseImpl,
    DeleteBookUseCase,
    DeleteBookUseCaseImpl,
)
from src.usecase.book.find_book_by_id_usecase import (
    FindBookByIdUseCase,
    FindBookByIdUseCaseImpl,
)
from src.usecase.book.find_books_usecase import (
    FindBooksByUserIdUseCase,
    FindBooksByUserIdUseCaseImpl,
    FindBooksUseCase,
    FindBooksUseCaseImpl,
)
from src.usecase.book.update_book_usecase import (
    UpdateBookUseCase,
    UpdateBookUseCaseImpl,
)


def get_book_repository(db: Session = Depends(get_db)) -> BookRepository:
    return PostgresBookRepository(db)


def get_create_book_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> CreateBookUseCase:
    return CreateBookUseCaseImpl(book_repository)


def get_find_books_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> FindBooksUseCase:
    return FindBooksUseCaseImpl(book_repository)


def get_find_books_by_user_id_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> FindBooksByUserIdUseCase:
    return FindBooksByUserIdUseCaseImpl(book_repository)


def get_find_book_by_id_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> FindBookByIdUseCase:
    return FindBookByIdUseCaseImpl(book_repository)


def get_update_book_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> UpdateBookUseCase:
    return UpdateBookUseCaseImpl(book_repository)


def get_delete_book_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> DeleteBookUseCase:
    return DeleteBookUseCaseImpl(book_repository)


def get_bulk_delete_books_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> BulkDeleteBooksUseCase:
    return BulkDeleteBooksUseCaseImpl(book_repository)
