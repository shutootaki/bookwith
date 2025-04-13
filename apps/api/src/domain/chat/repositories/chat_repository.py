from abc import ABC, abstractmethod

from src.domain.chat.entities.chat import Chat
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.user_id import UserId


class ChatRepository(ABC):
    """Chatリポジトリのインターフェース"""

    @abstractmethod
    def save(self, chat: Chat) -> None:
        """Chatを保存する"""

    @abstractmethod
    def find_by_id(self, chat_id: ChatId) -> Chat | None:
        """IDでChatを検索する"""

    @abstractmethod
    def find_by_user_id(self, user_id: UserId) -> list[Chat]:
        """ユーザーIDに紐づくChatをすべて取得する"""

    @abstractmethod
    def find_by_book_id(self, book_id: BookId) -> list[Chat]:
        """本IDに紐づくChatをすべて取得する"""

    @abstractmethod
    def find_by_user_id_and_book_id(self, user_id: UserId, book_id: BookId) -> list[Chat]:
        """ユーザーIDと本IDに紐づくChatを検索する"""

    @abstractmethod
    def delete(self, chat_id: ChatId) -> None:
        """IDでChatを削除する"""
