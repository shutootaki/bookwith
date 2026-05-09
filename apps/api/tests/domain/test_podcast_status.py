"""PodcastStatus 値オブジェクトの整合性テスト.

M-1 補強: ステータス遷移の前提（pending → processing → completed / failed、failed → pending で retry）
が値オブジェクト側で破綻しないことを確認する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.podcast.value_objects.podcast_status import (
    PodcastStatus,
    PodcastStatusEnum,
)


def test_factory_methods_return_correct_enum():
    assert PodcastStatus.pending().value == PodcastStatusEnum.PENDING
    assert PodcastStatus.processing().value == PodcastStatusEnum.PROCESSING
    assert PodcastStatus.completed().value == PodcastStatusEnum.COMPLETED
    assert PodcastStatus.failed().value == PodcastStatusEnum.FAILED


def test_can_process_only_pending_or_failed():
    assert PodcastStatus.pending().can_process() is True
    assert PodcastStatus.failed().can_process() is True
    assert PodcastStatus.processing().can_process() is False
    assert PodcastStatus.completed().can_process() is False


def test_status_predicates():
    completed = PodcastStatus.completed()
    assert completed.is_completed()
    assert not completed.is_pending()
    assert not completed.is_processing()
    assert not completed.is_failed()


def test_string_representation():
    assert str(PodcastStatus.pending()) == "PENDING"
    assert str(PodcastStatus.completed()) == "COMPLETED"


def test_from_string_round_trip():
    assert PodcastStatus.from_string("FAILED") == PodcastStatus.failed()


def test_from_string_rejects_unknown():
    with pytest.raises(ValueError):
        PodcastStatus.from_string("UNKNOWN_STATE")


def test_post_init_rejects_non_enum():
    with pytest.raises(ValueError):
        PodcastStatus(value="PENDING")  # type: ignore[arg-type]


def test_dataclass_is_frozen():
    s = PodcastStatus.pending()
    with pytest.raises(Exception):
        s.value = PodcastStatusEnum.COMPLETED  # type: ignore[misc]
