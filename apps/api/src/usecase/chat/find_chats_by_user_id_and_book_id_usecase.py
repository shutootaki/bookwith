from abc import ABC, abstractmethod

from src.domain.chat.entities.chat import Chat
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId


class FindChatsByUserIdAndBookIdUseCase(ABC):
    @abstractmethod
    def execute(self, user_id: UserId, book_id: BookId) -> list[Chat]:
        """ユーザーIDと本IDに紐づくChatをすべて取得する."""


class FindChatsByUserIdAndBookIdUseCaseImpl(FindChatsByUserIdAndBookIdUseCase):
    def __init__(self, chat_repository: ChatRepository) -> None:
        self.chat_repository = chat_repository

    def execute(self, user_id: UserId, book_id: BookId) -> list[Chat]:
        """ユーザーIDと本IDに紐づくChatをすべて取得する."""
        return self.chat_repository.find_by_user_id_and_book_id(user_id, book_id)
