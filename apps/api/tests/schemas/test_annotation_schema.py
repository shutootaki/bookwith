"""AnnotationSchema の strict 動作テスト.

CR-4 補強: 予期しないフィールド（`user_id` 等）を含む annotation は 422 で拒否される。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.annotation_schema import AnnotationSchema


_BOOK_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_ANN_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _base_payload() -> dict:
    return {
        "id": _ANN_ID,
        "book_id": _BOOK_ID,
        "cfi": "epubcfi(/6/4)",
        "color": "yellow",
        "spine": {"index": 0},
        "text": "highlight",
        "type": "highlight",
    }


def test_annotation_schema_accepts_valid_payload():
    schema = AnnotationSchema(**_base_payload())
    assert schema.id == _ANN_ID
    assert schema.book_id == _BOOK_ID


def test_annotation_schema_rejects_extra_field():
    payload = _base_payload()
    payload["user_id"] = "evil-user"  # 予期しないキー
    with pytest.raises(ValidationError):
        AnnotationSchema(**payload)


def test_annotation_schema_rejects_too_long_text():
    payload = _base_payload()
    payload["text"] = "x" * 9000
    with pytest.raises(ValidationError):
        AnnotationSchema(**payload)


def test_annotation_schema_camel_case_alias():
    """フロント由来の camelCase（bookId）でも受理される（既存 API 互換）."""
    payload = {
        "id": _ANN_ID,
        "bookId": _BOOK_ID,
        "cfi": "epubcfi(/6/4)",
        "color": "yellow",
        "spine": {"index": 0},
        "text": "highlight",
        "type": "highlight",
    }
    schema = AnnotationSchema(**payload)
    assert schema.book_id == _BOOK_ID
