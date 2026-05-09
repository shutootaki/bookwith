"""GCS upload_file の content_type allow-list を検証する.

H-13: text/html / image/svg+xml 等の HTML 解釈系を GCS に置けないことを保証。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.infrastructure.external.gcs import (
    ALLOWED_UPLOAD_CONTENT_TYPES,
    GCSClient,
    GCSContentTypeNotAllowedError,
)


def test_allowed_content_types_include_basic_types():
    """ホワイトリストに必須エントリが揃っていること."""
    assert "application/epub+zip" in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "image/jpeg" in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "image/png" in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "audio/mpeg" in ALLOWED_UPLOAD_CONTENT_TYPES


def test_allowed_content_types_exclude_html_and_svg():
    """HTML / SVG / JS は GCS に上げられないこと（XSS 経路の防御）."""
    assert "text/html" not in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "image/svg+xml" not in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "application/javascript" not in ALLOWED_UPLOAD_CONTENT_TYPES
    assert "application/xhtml+xml" not in ALLOWED_UPLOAD_CONTENT_TYPES


def test_upload_file_rejects_disallowed_content_type():
    """upload_file 自体が disallowed type で例外を投げる."""
    client = GCSClient(bucket_name="test")
    with pytest.raises(GCSContentTypeNotAllowedError):
        # GCS への接続は試みず、引数バリデーションで失敗するはず。
        client.upload_file("evil.html", b"<script>alert(1)</script>", "text/html")


def test_upload_file_rejects_svg_xml():
    client = GCSClient(bucket_name="test")
    with pytest.raises(GCSContentTypeNotAllowedError):
        client.upload_file("evil.svg", b"<svg/>", "image/svg+xml")
