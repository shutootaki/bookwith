"""text_sanitizer のユニットテスト.

H-15 / B-14 の根幹。HTML タグ除去・制御文字排除・長さ制限を検証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.shared.text_sanitizer import sanitize_plain_text


def test_strips_html_tags():
    assert sanitize_plain_text("<script>alert(1)</script>hello", max_length=100) == "hello"


def test_strips_attribute_with_quotes():
    assert (
        sanitize_plain_text('<a href="javascript:alert(1)">click</a>', max_length=100)
        == "click"
    )


def test_keeps_plain_text_with_newlines_and_tabs():
    assert sanitize_plain_text("line1\nline2\tcol", max_length=100) == "line1\nline2\tcol"


def test_strips_null_and_control_bytes():
    raw = "ok\x00\x07\x08text"
    assert sanitize_plain_text(raw, max_length=100) == "oktext"


def test_unicode_normalization_nfkc():
    # 全角英数字 → 半角に正規化
    assert sanitize_plain_text("ABC", max_length=10) == "ABC"


def test_html_entities_get_amp_escaped():
    # `&amp;xyz;` 形式が含まれていても `&amp;amp;xyz;` のように再エスケープされる
    out = sanitize_plain_text("a&amp;b", max_length=100)
    assert "&amp;amp;" in out


def test_max_length_enforced():
    with pytest.raises(ValueError):
        sanitize_plain_text("x" * 1000, max_length=10)


def test_empty_string_after_strip_returns_empty():
    assert sanitize_plain_text("   <br/>   ", max_length=100) == ""
