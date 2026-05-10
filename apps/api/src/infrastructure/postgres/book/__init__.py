from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.book.book_repository import BookRepositoryImpl

__all__ = ["BookDTO", "BookRepositoryImpl"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "BookDTO":
        from src.infrastructure.postgres.book.book_dto import BookDTO

        return BookDTO
    if name == "BookRepositoryImpl":
        from src.infrastructure.postgres.book.book_repository import BookRepositoryImpl

        return BookRepositoryImpl
    raise AttributeError(name)
