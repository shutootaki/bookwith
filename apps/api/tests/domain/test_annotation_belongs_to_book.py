"""Annotation.assert_belongs_to_book の単体テスト.

CR-4 / H-17: book_id を path 引数で強制上書きするだけでなく、
ドメインエンティティ自身でも `book_id` 一致を主張させる。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.annotation.entities.annotation import Annotation

_BOOK_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_BOOK_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _make_annotation(book_id: str) -> Annotation:
    return Annotation.create(
        book_id=book_id,
        cfi="epubcfi(/6/4)",
        text="ハイライト",
        spine={"index": 0},
    )


def test_assert_belongs_to_book_passes():
    ann = _make_annotation(_BOOK_A)
    ann.assert_belongs_to_book(_BOOK_A)  # 例外でない


def test_assert_belongs_to_book_raises_for_mismatch():
    ann = _make_annotation(_BOOK_A)
    with pytest.raises(ValueError, match="book_id"):
        ann.assert_belongs_to_book(_BOOK_B)


def test_assert_belongs_to_book_strict_string_match():
    """大文字小文字の差や前後空白も拒否される."""
    ann = _make_annotation(_BOOK_A)
    with pytest.raises(ValueError):
        ann.assert_belongs_to_book(_BOOK_A.upper())
    with pytest.raises(ValueError):
        ann.assert_belongs_to_book(f" {_BOOK_A} ")
