from abc import ABC, abstractmethod

from src.domain.chat.entities.chat import Chat
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId


class CreateChatUseCase(ABC):
    @abstractmethod
    def execute(self, user_id: UserId, title: ChatTitle | None = None, book_id: BookId | None = None) -> Chat:
        """新しいChatを作成する"""


class CreateChatUseCaseImpl(CreateChatUseCase):
    def __init__(self, chat_repository: ChatRepository) -> None:
        self.chat_repository = chat_repository

    def execute(self, user_id: UserId, title: ChatTitle | None = None, book_id: BookId | None = None) -> Chat:
        """新しいChatを作成する"""
        chat = Chat.create(user_id=user_id, title=title, book_id=book_id)
        self.chat_repository.save(chat)
        return chat
