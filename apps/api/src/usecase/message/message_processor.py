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
        meta = metadata or {}

        user_message = Message.create(
            content=MessageContent(content),
            sender_id=sender_id,
            sender_type=SenderType.user(),
            chat_id=chat_id,
            metadata=meta,
        )

        # メッセージを保存
        self.message_repository.save(user_message)

        # メッセージをベクトル化
        self.memory_service.vectorize_message(user_message)

        return user_message

    def save_ai_message(self, content: str, sender_id: str, chat_id: str, metadata: dict[str, Any] | None = None) -> Message:
        """AIメッセージを保存してベクトル化する."""
        meta = metadata or {}

        ai_message = Message.create(
            content=MessageContent(content),
            sender_id=sender_id,
            sender_type=SenderType.assistant(),
            chat_id=chat_id,
            metadata=meta,
        )

        # メッセージを保存
        self.message_repository.save(ai_message)

        # AIのレスポンスもベクトル化
        self.memory_service.vectorize_message(ai_message)

        return ai_message

    def process_summarization(self, chat_id: str, sender_id: str) -> None:
        """必要に応じてチャットの要約を実行する."""
        # チャットのメッセージ数を取得
        message_count = self.message_repository.count_by_chat_id(chat_id)

        # 必要に応じて要約を実行
        self.memory_service.summarize_chat(
            chat_id=chat_id,
            user_id=sender_id,
            message_count=message_count,
        )

    def get_latest_messages(self, chat_id: str) -> list[Message]:
        """最新のメッセージを取得し、古い順にソートして返す."""
        # 新しい順（降順）で必要な分だけ取得
        latest_messages = self.message_repository.find_latest_by_chat_id(chat_id, limit=5)

        # 古い順（昇順）に並べ直す
        return sorted(latest_messages, key=lambda msg: msg.created_at)
