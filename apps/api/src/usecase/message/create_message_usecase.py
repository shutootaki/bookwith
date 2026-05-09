"""メッセージ作成ユースケース."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_service import MemoryService
from src.usecase.message.ai_response_generator import AIResponseGenerator
from src.usecase.message.chat_manager import ChatManager
from src.usecase.message.message_processor import MessageProcessor

logger = logging.getLogger(__name__)

DEFAULT_SSE_STREAM_TIMEOUT_SECONDS = 180.0


class CreateMessageUseCase(ABC):
    """メッセージ作成ユースケースの抽象基底クラス."""

    @abstractmethod
    def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str]:
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""


class CreateMessageUseCaseImpl(CreateMessageUseCase):
    """メッセージ作成ユースケースの実装クラス.

    各種サービスに責務を分離し、シンプルなオーケストレーションを行う。
    """

    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        memory_service: MemoryService,
        stream_timeout_seconds: float = DEFAULT_SSE_STREAM_TIMEOUT_SECONDS,
    ) -> None:
        """メッセージ作成ユースケースの初期化."""
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.memory_service = memory_service
        self.stream_timeout_seconds = stream_timeout_seconds

        self.chat_manager = ChatManager(chat_repository)
        self.message_processor = MessageProcessor(message_repository, memory_service)
        self.ai_response_generator = AIResponseGenerator()

    async def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str]:
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す.

        B-2 (アドエンダム): SSE ストリーミング型 DoS 対策（完全対応）
            1. `asyncio.timeout(stream_timeout_seconds)` で生成全体に上限を課す。
               LLM がハング/暴走しても 180 秒（既定）でストリームを強制終了する。
            2. クライアント切断時は `GeneratorExit` 経由で生成器が閉じ、
               `finally` 節で部分応答を保存する。
            3. タイムアウト時も同様に部分応答を保存し、ユーザーへ可視のエラーを送る。
            4. 攻撃面の制限は `slowapi` `expensive_limit()` (20/min) と
               `BodySizeLimitMiddleware` (上限 7 MiB+) で多層化されている。
        """
        self.chat_manager.ensure_chat_exists(chat_id, sender_id, book_id, content)

        self.message_processor.save_user_message(content, sender_id, chat_id, metadata)

        self.message_processor.process_summarization(chat_id, sender_id)

        latest_messages = self.message_processor.get_latest_messages(chat_id, sender_id)
        memory_prompt = self.memory_service.build_memory_prompt(buffer=latest_messages, user_query=content, user_id=sender_id, chat_id=chat_id)

        ai_response_chunks: list[str] = []
        client_disconnected = False
        timed_out = False
        try:
            async with asyncio.timeout(self.stream_timeout_seconds):
                async for chunk in self.ai_response_generator.stream_ai_response(
                    question=memory_prompt, user_id=sender_id, book_id=book_id
                ):
                    ai_response_chunks.append(chunk)
                    yield chunk
        except TimeoutError:
            timed_out = True
            logger.warning(
                "SSE stream timed out after %.1fs (chat_id=%s, user_id=%s)",
                self.stream_timeout_seconds,
                chat_id,
                sender_id,
            )
            yield "\n\n[stream timed out — partial response saved]"
        except GeneratorExit:
            client_disconnected = True
            raise
        finally:
            full_ai_response = "".join(ai_response_chunks)
            if full_ai_response:
                try:
                    self.message_processor.save_ai_message(
                        full_ai_response, sender_id, chat_id, metadata
                    )
                except Exception:
                    logger.exception(
                        "Failed to persist AI message (disconnected=%s, timeout=%s)",
                        client_disconnected,
                        timed_out,
                    )
