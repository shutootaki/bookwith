from abc import ABC, abstractmethod

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository


class FindMessagesUseCase(ABC):
    @abstractmethod
    def execute_find_all(self) -> list[Message]:
        """全てのMessageを取得する"""

    @abstractmethod
    def execute_find_by_chat_id(self, chat_id: str) -> list[Message]:
        """チャットIDでMessageを検索する"""

    @abstractmethod
    def execute_find_by_sender_id(self, sender_id: str) -> list[Message]:
        """送信者IDでMessageを検索する"""


class FindMessagesUseCaseImpl(FindMessagesUseCase):
    def __init__(self, message_repository: MessageRepository) -> None:
        self.message_repository = message_repository

    def execute_find_all(self) -> list[Message]:
        return self.message_repository.find_all()

    def execute_find_by_chat_id(self, chat_id: str) -> list[Message]:
        return self.message_repository.find_by_chat_id(chat_id)

    def execute_find_by_sender_id(self, sender_id: str) -> list[Message]:
        return self.message_repository.find_by_sender_id(sender_id)
