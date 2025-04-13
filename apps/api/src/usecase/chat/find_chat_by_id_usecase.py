from abc import ABC, abstractmethod

from src.domain.chat.entities.chat import Chat
from src.domain.chat.exceptions.chat_exceptions import ChatNotFoundError
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.chat_id import ChatId


class FindChatByIdUseCase(ABC):
    @abstractmethod
    def execute(self, chat_id: ChatId) -> Chat:
        """IDでChatを検索する"""


class FindChatByIdUseCaseImpl(FindChatByIdUseCase):
    def __init__(self, chat_repository: ChatRepository) -> None:
        self.chat_repository = chat_repository

    def execute(self, chat_id: ChatId) -> Chat:
        """IDでChatを検索する"""
        chat = self.chat_repository.find_by_id(chat_id)
        if chat is None:
            raise ChatNotFoundError(f"Chat with ID {chat_id.value} not found")
        return chat
