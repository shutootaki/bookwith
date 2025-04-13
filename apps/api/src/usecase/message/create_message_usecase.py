from abc import ABC, abstractmethod
from typing import Any

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.sender_type import SenderType


class CreateMessageUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """新しいMessageを作成して返す"""


class CreateMessageUseCaseImpl(CreateMessageUseCase):
    def __init__(self, message_repository: MessageRepository) -> None:
        self.message_repository = message_repository

    def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """新しいMessageを作成して保存し、作成したMessageエンティティを返す"""
        message_content = MessageContent(content)

        meta = metadata or {}

        message = Message.create(
            content=message_content,
            sender_id=sender_id,
            sender_type=SenderType.user(),
            chat_id=chat_id,
            metadata=meta,
        )

        self.message_repository.save(message)

        return message
