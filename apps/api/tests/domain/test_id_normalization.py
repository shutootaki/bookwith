"""BookId / AnnotationId の正規化テスト.

B-12 / B-11: UUID は小文字に正規化されることで、`AAAA...` と `aaaa...` が
重複行として保存される事故を防ぐ。
"""

from __future__ import annotations

import os
import uuid

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.domain.book.value_objects.book_id import BookId


def test_book_id_normalizes_uppercase_to_lowercase():
    bid = BookId("AAAAAAAA-1111-1111-1111-111111111111")
    assert bid.value == "aaaaaaaa-1111-1111-1111-111111111111"


def test_book_id_keeps_lowercase_unchanged():
    val = "11111111-2222-3333-4444-555555555555"
    assert BookId(val).value == val


def test_book_id_generated_value_is_lowercase_uuid():
    bid = BookId.generate()
    # 値が UUID 形式かつ小文字で構成されている
    assert bid.value == bid.value.lower()
    uuid.UUID(bid.value)


def test_book_id_rejects_uuid_with_braces():
    with pytest.raises(ValueError):
        BookId("{11111111-1111-1111-1111-111111111111}")


def test_book_id_rejects_urn_uuid_prefix():
    with pytest.raises(ValueError):
        BookId("urn:uuid:11111111-1111-1111-1111-111111111111")


def test_annotation_id_normalizes_uppercase_to_lowercase():
    aid = AnnotationId("BBBBBBBB-2222-2222-2222-222222222222")
    assert aid.value == "bbbbbbbb-2222-2222-2222-222222222222"


def test_annotation_id_generates_lowercase_uuid_when_blank():
    aid = AnnotationId("")
    assert aid.value == aid.value.lower()
    uuid.UUID(aid.value)
