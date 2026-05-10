"""M-1 (TOCTOU) Podcast retry の楽観的ロック動作のテスト.

`PodcastRepositoryImpl.update_status_with_optimistic_lock` が
`expected_status` と一致した行だけを更新し、
不一致なら更新行 0 件で False を返してロールバックすることを検証する。

実 DB は不要。SQLAlchemy session を MagicMock 化し、`execute` の戻り値の `rowcount` を切り替えて分岐を網羅する。
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

import pytest

from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus
from src.infrastructure.postgres.podcast.podcast_repository import PodcastRepositoryImpl


def _make_session(rowcount: int) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    session.execute.return_value = result
    return session


PODCAST_ID = PodcastId("11111111-2222-3333-4444-555555555555")


def test_optimistic_lock_returns_true_when_status_matches() -> None:
    session = _make_session(rowcount=1)
    repo = PodcastRepositoryImpl(session)

    result = asyncio.run(
        repo.update_status_with_optimistic_lock(
            PODCAST_ID,
            expected_status=PodcastStatus.failed(),
            new_status=PodcastStatus.pending(),
            error_message="",
        )
    )

    assert result is True
    session.execute.assert_called_once()
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_optimistic_lock_returns_false_when_status_mismatch() -> None:
    """並行リトライで先行リクエストがすでに status を更新済みのケース."""
    session = _make_session(rowcount=0)
    repo = PodcastRepositoryImpl(session)

    result = asyncio.run(
        repo.update_status_with_optimistic_lock(
            PODCAST_ID,
            expected_status=PodcastStatus.failed(),
            new_status=PodcastStatus.pending(),
            error_message="",
        )
    )

    assert result is False
    session.execute.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_called_once()


def test_optimistic_lock_includes_audio_url_when_provided() -> None:
    """`audio_url` を指定した呼び出しがエラーなく通過すること."""
    session = _make_session(rowcount=1)
    repo = PodcastRepositoryImpl(session)

    result = asyncio.run(
        repo.update_status_with_optimistic_lock(
            PODCAST_ID,
            expected_status=PodcastStatus.processing(),
            new_status=PodcastStatus.completed(),
            audio_url="https://example.com/audio.mp3",
        )
    )

    assert result is True


@pytest.mark.parametrize(
    ("expected", "new"),
    [
        (PodcastStatus.failed(), PodcastStatus.pending()),
        (PodcastStatus.processing(), PodcastStatus.completed()),
        (PodcastStatus.processing(), PodcastStatus.failed()),
        (PodcastStatus.pending(), PodcastStatus.processing()),
    ],
)
def test_optimistic_lock_supports_all_state_transitions(expected: PodcastStatus, new: PodcastStatus) -> None:
    """すべての主要状態遷移で楽観的ロックが機能する."""
    session = _make_session(rowcount=1)
    repo = PodcastRepositoryImpl(session)

    result = asyncio.run(repo.update_status_with_optimistic_lock(PODCAST_ID, expected_status=expected, new_status=new))

    assert result is True
