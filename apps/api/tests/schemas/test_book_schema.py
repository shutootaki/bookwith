"""BookCreateRequest / BookUpdateRequest / BulkDeleteRequestBody のバリデーションテスト.

CR-4 / H-12 / M-3: クライアントから受け取る ID は path 経由 / 認証 principal 経由のみ。
スキーマには `user_id` が無いことを保証する。
"""

from __future__ import annotations

import base64
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.book_schema import (
    BookCreateRequest,
    BookUpdateRequest,
    BulkDeleteRequestBody,
    RagProcessRequest,
)


def test_book_create_request_has_no_user_id_field():
    """CR-4: user_id を明示的に受け付けない."""
    sample = base64.b64encode(b"PK\x03\x04test").decode()
    req = BookCreateRequest(file_data=sample, file_name="x.epub")
    assert "user_id" not in req.model_dump(by_alias=False)
    assert "userId" not in req.model_dump(by_alias=True)


def test_rag_process_request_has_no_user_id_field():
    sample = base64.b64encode(b"PK\x03\x04test").decode()
    req = RagProcessRequest(book_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", file_data=sample, file_name="x.epub")
    assert "user_id" not in req.model_dump(by_alias=False)


def test_bulk_delete_request_max_count():
    BulkDeleteRequestBody(book_ids=[f"{i:08x}-0000-0000-0000-000000000000" for i in range(100)])

    with pytest.raises(ValidationError):
        BulkDeleteRequestBody(
            book_ids=[f"{i:08x}-0000-0000-0000-000000000000" for i in range(101)]
        )

    with pytest.raises(ValidationError):
        BulkDeleteRequestBody(book_ids=[])


def test_book_update_request_percentage_range():
    BookUpdateRequest(percentage=0)
    BookUpdateRequest(percentage=100)
    with pytest.raises(ValidationError):
        BookUpdateRequest(percentage=-1)
    with pytest.raises(ValidationError):
        BookUpdateRequest(percentage=101)


def test_book_update_request_long_name_rejected():
    with pytest.raises(ValidationError):
        BookUpdateRequest(name="x" * 1000)


def test_book_create_request_too_large_filedata_rejected():
    big = "A" * (50 * 1024 * 1024)  # _MAX_FILE_DATA_LEN は 40MB
    with pytest.raises(ValidationError):
        BookCreateRequest(file_data=big, file_name="x.epub")


def test_book_create_request_extra_field_rejected():
    """CR-4 補強: 不要な user_id / sender_type 等を送ると 422."""
    sample = base64.b64encode(b"PK\x03\x04test").decode()
    with pytest.raises(ValidationError):
        BookCreateRequest(
            file_data=sample,
            file_name="x.epub",
            user_id="evil-user",  # type: ignore[call-arg]
        )


def test_book_update_request_extra_field_rejected():
    with pytest.raises(ValidationError):
        BookUpdateRequest(name="x", user_id="evil-user")  # type: ignore[call-arg]


def test_bulk_delete_extra_field_rejected():
    with pytest.raises(ValidationError):
        BulkDeleteRequestBody(
            book_ids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            user_id="evil-user",  # type: ignore[call-arg]
        )


def test_rag_process_request_extra_field_rejected():
    sample = base64.b64encode(b"PK\x03\x04test").decode()
    with pytest.raises(ValidationError):
        RagProcessRequest(
            book_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            file_data=sample,
            file_name="x.epub",
            user_id="evil-user",  # type: ignore[call-arg]
        )
