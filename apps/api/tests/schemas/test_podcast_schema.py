"""CreatePodcastRequest の strict 動作テスト.

CR-4 補強: クライアントから余計なフィールドを送られても 422 で弾く。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest
from pydantic import ValidationError

from src.domain.podcast.value_objects.language import PodcastLanguage
from src.presentation.api.schemas.podcast_schema import CreatePodcastRequest


def test_create_podcast_request_accepts_minimal_payload():
    req = CreatePodcastRequest(
        book_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        language=PodcastLanguage.JA_JP,
    )
    assert req.book_id


def test_create_podcast_request_rejects_extra_field():
    with pytest.raises(ValidationError):
        CreatePodcastRequest(
            book_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            language=PodcastLanguage.JA_JP,
            user_id="evil-user",  # type: ignore[call-arg]
        )


def test_create_podcast_request_title_max_length():
    with pytest.raises(ValidationError):
        CreatePodcastRequest(
            book_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            language=PodcastLanguage.JA_JP,
            title="x" * 1000,
        )


def test_create_podcast_request_book_id_max_length():
    with pytest.raises(ValidationError):
        CreatePodcastRequest(
            book_id="x" * 100,
            language=PodcastLanguage.JA_JP,
        )
