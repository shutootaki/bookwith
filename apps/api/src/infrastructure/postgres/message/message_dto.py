from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base
from src.domain.message.entities.message import Message
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.message_id import MessageId
from src.domain.message.value_objects.sender_type import SenderType, SenderTypeEnum
from src.infrastructure.postgres.db_util import TimestampMixin


class MessageDTO(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    sender_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    sender_type: Mapped[SenderTypeEnum] = mapped_column(SQLAlchemyEnum(SenderTypeEnum), nullable=False)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    user = relationship("UserDTO", back_populates="messages", foreign_keys=[sender_id])
    chat = relationship("ChatDTO", back_populates="messages")

    def to_entity(self) -> Message:
        message_id = MessageId(value=str(self.id))
        message_content = MessageContent(value=str(self.content))

        return Message(
            id=message_id,
            content=message_content,
            sender_id=self.sender_id,
            sender_type=SenderType(self.sender_type.value),
            chat_id=self.chat_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            metadata=self.message_metadata or {},
        )

    @staticmethod
    def to_orm_dict(message: Message) -> dict[str, Any]:
        return {
            "id": message.id.value,
            "content": message.content.value,
            "sender_id": message.sender_id,
            "sender_type": SenderTypeEnum(message.sender_type.value),
            "chat_id": message.chat_id,
            "created_at": message.created_at,
            "updated_at": message.updated_at,
            "deleted_at": message.deleted_at,
            "message_metadata": message.metadata,
        }

    @staticmethod
    def from_entity(message: Message) -> "MessageDTO":
        return MessageDTO(
            id=message.id.value,
            content=message.content.value,
            sender_id=message.sender_id,
            sender_type=SenderTypeEnum(message.sender_type.value),
            chat_id=message.chat_id,
            created_at=message.created_at,
            updated_at=message.updated_at,
            deleted_at=message.deleted_at,
            message_metadata=message.metadata,
        )
