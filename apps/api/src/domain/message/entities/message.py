from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.message.exceptions.message_exceptions import (
    MessageAlreadyDeletedException,
)
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.message_id import MessageId
from src.domain.message.value_objects.sender_type import SenderType


class Message(BaseModel):
    id: MessageId = Field(default_factory=MessageId.generate)
    content: MessageContent
    sender_type: SenderType
    chat_id: str  # これはValueObjectにするべきかもしれないが、今回はそのまま
    sender_id: str  # これもValueObjectにするべきかもしれないが、今回はそのまま
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True  # Value Object を許容するため

    @classmethod
    def create(
        cls,
        content: MessageContent,
        sender_type: SenderType,
        chat_id: str,
        sender_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> "Message":
        # Pydanticがデフォルト値を処理するため、単純にインスタンス化する
        return cls(
            content=content,
            sender_type=sender_type,
            chat_id=chat_id,
            sender_id=sender_id,
            metadata=metadata or {},
        )

    def mark_as_deleted(self) -> None:
        if self.is_deleted:
            raise MessageAlreadyDeletedException

        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return self.id == other.id
