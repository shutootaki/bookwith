"""メッセージをIDで検索するユースケース"""

from abc import ABC, abstractmethod

from src.domain.message.entities.message import Message
from src.domain.message.exceptions.message_exceptions import MessageNotFoundException
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_id import MessageId


class FindMessageByIdUseCase(ABC):
    @abstractmethod
    def execute(self, message_id: str) -> Message:
        """メッセージをIDで検索する"""


class FindMessageByIdUseCaseImpl(FindMessageByIdUseCase):
    def __init__(self, message_repository: MessageRepository) -> None:
        self.message_repository = message_repository

    def execute(self, message_id: str) -> Message:
        """メッセージをIDで検索し、見つからない場合は例外をスローする"""
        message_id_obj = MessageId(message_id)
        message = self.message_repository.find_by_id(message_id_obj)

        if message is None:
            raise MessageNotFoundException(message_id)

        return message
