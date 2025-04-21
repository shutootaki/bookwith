from abc import ABC, abstractmethod

from src.domain.message.entities.message import Message
from src.domain.message.value_objects.message_id import MessageId


class MessageRepository(ABC):
    @abstractmethod
    def save(self, message: Message) -> None:
        """メッセージを保存する."""

    @abstractmethod
    def find_by_id(self, message_id: MessageId) -> Message | None:
        """IDでメッセージを検索する."""

    @abstractmethod
    def find_all(self) -> list[Message]:
        """全てのメッセージを取得する."""

    @abstractmethod
    def find_by_chat_id(self, chat_id: str) -> list[Message]:
        """チャットIDでメッセージを検索する."""

    @abstractmethod
    def find_by_sender_id(self, sender_id: str) -> list[Message]:
        """送信者IDでメッセージを検索する."""

    @abstractmethod
    def delete(self, message_id: MessageId) -> None:
        """IDでメッセージを削除する."""

    @abstractmethod
    def bulk_delete(self, message_ids: list[MessageId]) -> list[MessageId]:
        """複数のメッセージを一括削除する。削除に失敗したメッセージIDのリストを返す."""

    @abstractmethod
    def count_by_chat_id(self, chat_id: str) -> int:
        """チャットIDに関連するメッセージの数を取得する."""

    @abstractmethod
    def find_chat_ids_by_user_id(self, user_id: str) -> list[str]:
        """ユーザーIDに関連するチャットIDを取得する."""
