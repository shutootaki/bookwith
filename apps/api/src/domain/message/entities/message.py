from datetime import datetime
from typing import Any

from src.domain.message.exceptions.message_exceptions import (
    MessageAlreadyDeletedException,
)
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.message_id import MessageId
from src.domain.message.value_objects.sender_type import SenderType


class Message:
    def __init__(
        self,
        id: MessageId,
        content: MessageContent,
        sender_id: str,
        sender_type: SenderType,
        chat_id: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._id = id
        self._content = content
        self._sender_id = sender_id
        self._sender_type = sender_type
        self._chat_id = chat_id
        self._created_at = created_at if created_at is not None else datetime.now()
        self._updated_at = updated_at if updated_at is not None else datetime.now()
        self._deleted_at = deleted_at
        self._metadata = metadata or {}

    @classmethod
    def create(
        cls,
        content: MessageContent,
        sender_id: str,
        sender_type: SenderType,
        chat_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> "Message":
        message_id = MessageId.generate()
        return cls(
            id=message_id,
            content=content,
            sender_id=sender_id,
            sender_type=sender_type,
            chat_id=chat_id,
            metadata=metadata,
        )

    def mark_as_deleted(self) -> None:
        if self.is_deleted:
            raise MessageAlreadyDeletedException

        self._deleted_at = datetime.now()
        self._updated_at = datetime.now()

    @property
    def id(self) -> MessageId:
        return self._id

    @property
    def content(self) -> MessageContent:
        return self._content

    @property
    def sender_id(self) -> str:
        return self._sender_id

    @property
    def sender_type(self) -> SenderType:
        return self._sender_type

    @property
    def chat_id(self) -> str:
        return self._chat_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return False
        return self._id == other._id
