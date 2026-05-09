"""メッセージ処理サービス."""

from typing import Any

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.sender_type import SenderType
from src.infrastructure.memory.memory_service import MemoryService


class MessageProcessor:
    """メッセージの保存とベクトル化を行うサービス."""

    def __init__(self, message_repository: MessageRepository, memory_service: MemoryService) -> None:
        """メッセージ処理サービスの初期化."""
        self.message_repository = message_repository
        self.memory_service = memory_service

    def save_user_message(self, content: str, sender_id: str, chat_id: str, metadata: dict[str, Any] | None = None) -> Message:
        """ユーザーメッセージを保存してベクトル化する."""
        return self._save_message(content, sender_id, chat_id, SenderType.user(), metadata)

    def save_ai_message(self, content: str, sender_id: str, chat_id: str, metadata: dict[str, Any] | None = None) -> Message:
        """AIメッセージを保存してベクトル化する."""
        return self._save_message(content, sender_id, chat_id, SenderType.assistant(), metadata)

    def _save_message(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        sender_type: SenderType,
        metadata: dict[str, Any] | None,
    ) -> Message:
        message = Message.create(
            content=MessageContent(content),
            sender_id=sender_id,
            sender_type=sender_type,
            chat_id=chat_id,
            metadata=metadata or {},
        )
        self.message_repository.save(message)
        self.memory_service.vectorize_message(message)
        return message

    def process_summarization(self, chat_id: str, sender_id: str) -> None:
        """必要に応じてチャットの要約を実行する."""
        message_count = self.message_repository.count_by_chat_id(chat_id)

        self.memory_service.summarize_chat(
            chat_id=chat_id,
            user_id=sender_id,
            message_count=message_count,
        )

    def get_latest_messages(self, chat_id: str, user_id: str) -> list[Message]:
        """最新のメッセージを取得し、古い順にソートして返す（所有者検証込み）."""
        # H-16: チャットの所有者検証を join で組み込んだ取得を使う。
        latest_messages = self.message_repository.find_latest_by_chat_id_for_user(chat_id, limit=5, user_id=user_id)
        return sorted(latest_messages, key=lambda msg: msg.created_at)
