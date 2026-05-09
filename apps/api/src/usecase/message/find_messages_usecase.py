from abc import ABC, abstractmethod

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository


class FindMessagesUseCase(ABC):
    @abstractmethod
    def execute_find_by_chat_id(self, chat_id: str, user_id: str) -> list[Message]:
        """チャットIDでMessageを検索する（所有者検証込み）"""


class FindMessagesUseCaseImpl(FindMessagesUseCase):
    def __init__(self, message_repository: MessageRepository) -> None:
        self.message_repository = message_repository

    def execute_find_by_chat_id(self, chat_id: str, user_id: str) -> list[Message]:
        # H-16: 所有者検証込み
        return self.message_repository.find_by_chat_id_for_user(chat_id, user_id)
