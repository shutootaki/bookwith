"""FindBookByIdUseCase / DeleteBookUseCase の owner_check ロジックを fake repo で検証.

CR-3 / DDD assert_owned_by の回帰検出。

実 DB を使わず、in-memory の fake で UseCase の振る舞いを検証する：
- 自分の本: 取得成功
- 他人の本: BookPermissionDeniedException
- 存在しない本: BookNotFoundException
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import (
    BookNotFoundException,
    BookPermissionDeniedException,
)
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.usecase.book.find_book_by_id_usecase import FindBookByIdUseCaseImpl


def _make_book(book_id: str, user_id: str) -> Book:
    return Book.create(
        id=BookId(book_id),
        name=BookTitle("sample"),
        user_id=user_id,
        file_path="gs://bucket/x.epub",
        author=None,
        size=100,
        cover_path=None,
    )


class FakeBookRepository(BookRepository):
    """in-memory implementation. CR-3 owner-aware メソッドが正しく動くか検証する用."""

    def __init__(self, books: list[Book]):
        self._books = {b.id.value: b for b in books}

    # 必要メソッドのみ実装。残りは raise NotImplementedError
    def save(self, book): raise NotImplementedError  # noqa: ANN001
    def find_by_user_id(self, user_id: str): raise NotImplementedError

    def find_by_id(self, book_id: BookId) -> Book | None:
        return self._books.get(book_id.value)

    def find_by_id_for_user(self, book_id: BookId, user_id: str) -> Book | None:
        book = self._books.get(book_id.value)
        if book and book.user_id == user_id:
            return book
        return None

    def delete_for_user(self, book_id: BookId, user_id: str) -> bool:
        book = self.find_by_id_for_user(book_id, user_id)
        if not book:
            return False
        del self._books[book_id.value]
        return True

    def bulk_delete_for_user(self, book_ids, user_id: str):  # noqa: ANN001
        deleted = []
        for bid in book_ids:
            if self.delete_for_user(bid, user_id):
                deleted.append(bid)
        return deleted


_OWNER = "11111111-1111-1111-1111-111111111111"
_OTHER = "22222222-2222-2222-2222-222222222222"
_BOOK_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_find_by_id_returns_owned_book():
    repo = FakeBookRepository([_make_book(_BOOK_ID, _OWNER)])
    usecase = FindBookByIdUseCaseImpl(repo)
    result = usecase.execute(_BOOK_ID, _OWNER)
    assert result.id.value == _BOOK_ID
    assert result.user_id == _OWNER


def test_find_by_id_other_user_raises_permission_denied():
    repo = FakeBookRepository([_make_book(_BOOK_ID, _OWNER)])
    usecase = FindBookByIdUseCaseImpl(repo)
    with pytest.raises(BookPermissionDeniedException):
        usecase.execute(_BOOK_ID, _OTHER)


def test_find_by_id_missing_raises_not_found():
    repo = FakeBookRepository([])
    usecase = FindBookByIdUseCaseImpl(repo)
    with pytest.raises(BookNotFoundException):
        usecase.execute(_BOOK_ID, _OWNER)


def test_book_assert_owned_by():
    book = _make_book(_BOOK_ID, _OWNER)
    book.assert_owned_by(_OWNER)  # 例外でない
    with pytest.raises(BookPermissionDeniedException):
        book.assert_owned_by(_OTHER)
