"""主要値オブジェクトのバリデーションテスト.

CR-4 / H-15 / B-11 / B-12 / B-14: ID 検証、HTML サニタイズ、長さ制限が機能していること。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.domain.annotation.value_objects.annotation_notes import AnnotationNotes
from src.domain.annotation.value_objects.annotation_text import AnnotationText
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.message.value_objects.message_content import MessageContent


# ----------------------------------------
# BookId / AnnotationId
# ----------------------------------------


def test_book_id_strict_uuid_only():
    BookId("11111111-1111-1111-1111-111111111111")
    with pytest.raises(ValueError):
        BookId("urn:uuid:11111111-1111-1111-1111-111111111111")
    with pytest.raises(ValueError):
        BookId("{11111111-1111-1111-1111-111111111111}")
    with pytest.raises(ValueError):
        BookId("not-a-uuid")
    with pytest.raises(ValueError):
        BookId("")


def test_book_id_normalizes_to_lowercase():
    bid = BookId("AAAAAAAA-1111-1111-1111-111111111111")
    assert bid.value == "aaaaaaaa-1111-1111-1111-111111111111"


def test_annotation_id_generates_when_empty():
    aid = AnnotationId.from_string(None)
    BookId(aid.value)  # 形式は UUID のはず


def test_annotation_id_rejects_non_uuid():
    with pytest.raises(ValueError):
        AnnotationId("not-a-uuid")


# ----------------------------------------
# ChatTitle / BookTitle
# ----------------------------------------


def test_chat_title_strips_html_and_enforces_length():
    title = ChatTitle("<script>x</script>普通のタイトル")
    assert "<script>" not in title.value


def test_chat_title_rejects_empty_after_sanitize():
    with pytest.raises(ValueError):
        ChatTitle("   <br/>   ")


def test_chat_title_rejects_too_long():
    with pytest.raises(ValueError):
        ChatTitle("x" * 1000)


def test_book_title_strips_html():
    bt = BookTitle("<b>Hello</b>")
    assert bt.value == "Hello"


def test_book_title_rejects_empty():
    with pytest.raises(ValueError):
        BookTitle("")


# ----------------------------------------
# AnnotationText / AnnotationNotes
# ----------------------------------------


def test_annotation_text_required():
    with pytest.raises(ValueError):
        AnnotationText("")


def test_annotation_text_strips_html():
    at = AnnotationText("<i>note</i>")
    assert at.value == "note"


def test_annotation_notes_optional_none():
    notes = AnnotationNotes(None)
    assert notes.value is None


def test_annotation_notes_strips_html():
    notes = AnnotationNotes("<script>boom</script>memo")
    assert notes.value == "memo"


def test_annotation_notes_too_long_rejected():
    with pytest.raises(ValueError):
        AnnotationNotes("x" * 5000)


# ----------------------------------------
# MessageContent
# ----------------------------------------


def test_message_content_required():
    with pytest.raises(ValueError):
        MessageContent("")


def test_message_content_strips_html():
    mc = MessageContent("<a>hi</a>")
    assert mc.value == "hi"


def test_message_content_too_long_rejected():
    with pytest.raises(ValueError):
        MessageContent("x" * 100_000)
