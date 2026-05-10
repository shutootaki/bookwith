"""エラーメッセージが固定文言であることを検証する.

H-5: 例外メッセージにユーザー入力や内部エラー文字列が混入しないように、
すべてのエラー文言テンプレートは `{error}` のような placeholder を含まないこと。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from src.presentation.api.error_messages import book_error_message


def test_no_format_placeholders_in_error_messages() -> None:
    """`{error}` `{message}` のような placeholder が残っていない."""
    forbidden = ("{error}", "{message}", "{e}", "{exc}")
    for name in dir(book_error_message):
        if name.startswith("_"):
            continue
        value = getattr(book_error_message, name)
        if not isinstance(value, str):
            continue
        for tok in forbidden:
            assert tok not in value, f"{name} still contains placeholder {tok}"


def test_error_message_constants_are_non_empty() -> None:
    for name in (
        "BOOK_NOT_FOUND",
        "BOOK_ACCESS_DENIED",
        "BOOK_FILE_NOT_FOUND",
        "BOOK_CREATE_ERROR",
        "BOOK_UPDATE_ERROR",
        "BOOK_DELETE_ERROR",
        "BOOK_BULK_DELETE_ERROR",
        "BOOK_FETCH_ERROR",
        "BOOK_COVER_FETCH_ERROR",
        "BOOK_FILE_FETCH_ERROR",
        "SIGNED_URL_GENERATION_ERROR",
    ):
        v = getattr(book_error_message, name)
        assert isinstance(v, str) and v, f"{name} should be a non-empty string"
