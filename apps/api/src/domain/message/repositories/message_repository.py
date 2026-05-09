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
    def find_by_id_for_user(self, message_id: MessageId, user_id: str) -> Message | None:
        """CR-3: 指定 user_id 所有チャットのメッセージのみ返す."""

    @abstractmethod
    def find_by_chat_id(self, chat_id: str) -> list[Message]:
        """チャットIDでメッセージを検索する."""

    @abstractmethod
    def find_by_chat_id_for_user(self, chat_id: str, user_id: str) -> list[Message]:
        """H-16: 指定 user_id 所有チャットのメッセージのみ返す."""

    @abstractmethod
    def find_latest_by_chat_id(self, chat_id: str, limit: int) -> list[Message]:
        """チャットIDで最新のメッセージを指定件数取得する."""

    @abstractmethod
    def find_latest_by_chat_id_for_user(self, chat_id: str, limit: int, user_id: str) -> list[Message]:
        """H-16: 指定 user_id 所有チャットの最新メッセージのみ返す."""

    @abstractmethod
    def delete_for_user(self, message_id: MessageId, user_id: str) -> bool:
        """CR-3: 指定 user_id 所有チャットのメッセージのみ削除する."""

    @abstractmethod
    def bulk_delete_for_user(self, message_ids: list[MessageId], user_id: str) -> list[MessageId]:
        """CR-3: 指定 user_id 所有チャットのメッセージのみ一括削除する."""

    @abstractmethod
    def count_by_chat_id(self, chat_id: str) -> int:
        """チャットIDに関連するメッセージの数を取得する."""
