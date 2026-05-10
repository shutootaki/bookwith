"""B-2 (アドエンダム): SSE ストリームのタイムアウトと部分応答保存のテスト."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from src.usecase.message.create_message_usecase import CreateMessageUseCaseImpl

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class _FakeChatManager:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def ensure_chat_exists(self, chat_id: str, sender_id: str, book_id: str | None, content: str) -> None:
        self.calls.append((chat_id, sender_id, book_id, content))


class _FakeMessageProcessor:
    def __init__(self) -> None:
        self.saved_user: list[tuple[Any, ...]] = []
        self.saved_ai: list[tuple[Any, ...]] = []
        self.summarize_calls = 0
        self.fetched: list[Any] = []

    def save_user_message(self, *args: Any, **kwargs: Any) -> None:
        self.saved_user.append((args, kwargs))

    def save_ai_message(self, *args: Any, **kwargs: Any) -> None:
        self.saved_ai.append((args, kwargs))

    def process_summarization(self, chat_id: str, sender_id: str) -> None:
        self.summarize_calls += 1

    def get_latest_messages(self, chat_id: str, sender_id: str) -> list[Any]:
        self.fetched.append((chat_id, sender_id))
        return []


class _FakeMemoryService:
    def build_memory_prompt(self, **kwargs: Any) -> str:
        return "prompt"


class _FakeAIResponseGenerator:
    """テスト用 AI 応答ジェネレータ. 各 chunk の前後に sleep を入れてタイムアウトを誘発できる."""

    def __init__(self, chunks: list[str], delay: float) -> None:
        self.chunks = chunks
        self.delay = delay

    async def stream_ai_response(self, *, question: str, user_id: str, book_id: str | None) -> AsyncGenerator[str]:
        for chunk in self.chunks:
            await asyncio.sleep(self.delay)
            yield chunk


def _build_usecase(
    chunks: list[str],
    chunk_delay: float,
    timeout_seconds: float,
) -> tuple[CreateMessageUseCaseImpl, _FakeMessageProcessor]:
    usecase = CreateMessageUseCaseImpl(
        message_repository=MagicMock(),
        chat_repository=MagicMock(),
        memory_service=_FakeMemoryService(),
        stream_timeout_seconds=timeout_seconds,
    )
    processor = _FakeMessageProcessor()
    usecase.chat_manager = _FakeChatManager()  # type: ignore[assignment]
    usecase.message_processor = processor  # type: ignore[assignment]
    usecase.ai_response_generator = _FakeAIResponseGenerator(chunks, chunk_delay)  # type: ignore[assignment]
    return usecase, processor


@pytest.mark.asyncio
async def test_stream_completes_within_timeout_persists_full_response() -> None:
    """タイムアウト内に完了した場合、フル応答が保存され、特殊メッセージは入らない."""
    usecase, processor = _build_usecase(chunks=["hello ", "world"], chunk_delay=0.001, timeout_seconds=2.0)
    received: list[str] = []
    async for chunk in usecase.execute(content="q", sender_id="user-1", chat_id="chat-1", book_id=None):
        received.append(chunk)
    assert "".join(received) == "hello world"
    assert processor.saved_ai, "AI 応答は保存されているはず"
    saved_args, _ = processor.saved_ai[0]
    assert saved_args[0] == "hello world"


@pytest.mark.asyncio
async def test_stream_timeout_yields_marker_and_persists_partial() -> None:
    """ストリームがタイムアウトすると、ユーザーへ可視メッセージを送り、部分応答を保存する."""
    # チャンク 1 つの送出に 0.4 秒かかる × 5 チャンク = 約 2.0 秒。タイムアウト 0.5 秒で打ち切られる。
    usecase, processor = _build_usecase(chunks=["a", "b", "c", "d", "e"], chunk_delay=0.4, timeout_seconds=0.5)
    received: list[str] = []
    async for chunk in usecase.execute(content="q", sender_id="user-1", chat_id="chat-1", book_id=None):
        received.append(chunk)

    # 最後のチャンクはタイムアウト通知メッセージ
    assert received[-1].startswith("\n\n[stream timed out")
    # 少なくとも 1 つの実チャンクと、部分保存があるはず
    saved_args, _ = processor.saved_ai[0]
    persisted = saved_args[0]
    assert persisted, "タイムアウト時でも生成済み部分は保存される"
    assert "[stream timed out" not in persisted, "保存される本文にタイムアウト通知メッセージは含めない"


@pytest.mark.asyncio
async def test_stream_persists_zero_chunk_does_not_save() -> None:
    """1 チャンクも来ずにタイムアウトした場合は AI メッセージを保存しない."""
    usecase, processor = _build_usecase(chunks=["delayed"], chunk_delay=2.0, timeout_seconds=0.1)
    received: list[str] = []
    async for chunk in usecase.execute(content="q", sender_id="user-1", chat_id="chat-1", book_id=None):
        received.append(chunk)
    # タイムアウト通知のみ
    assert any(c.startswith("\n\n[stream timed out") for c in received)
    # ai chunk が一つも蓄積されていないので保存はスキップ
    assert processor.saved_ai == []
