"""メッセージ作成ユースケース."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_service import MemoryService
from src.usecase.message.ai_response_generator import AIResponseGenerator
from src.usecase.message.chat_manager import ChatManager
from src.usecase.message.message_processor import MessageProcessor


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
    ) -> None:
        """メッセージ作成ユースケースの初期化."""
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.memory_service = memory_service

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
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""
        self.chat_manager.ensure_chat_exists(chat_id, sender_id, book_id, content)

        self.message_processor.save_user_message(content, sender_id, chat_id, metadata)

        self.message_processor.process_summarization(chat_id, sender_id)

        latest_messages = self.message_processor.get_latest_messages(chat_id)
        memory_prompt = self.memory_service.build_memory_prompt(buffer=latest_messages, user_query=content, user_id=sender_id, chat_id=chat_id)

        ai_response_chunks = []
        async for chunk in self.ai_response_generator.stream_ai_response(question=memory_prompt, user_id=sender_id, book_id=book_id):
            ai_response_chunks.append(chunk)
            yield chunk

        full_ai_response = "".join(ai_response_chunks)
        self.message_processor.save_ai_message(full_ai_response, sender_id, chat_id, metadata)
