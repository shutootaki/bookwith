from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.db import Base
from src.domain.chat.entities.chat import Chat
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId
from src.infrastructure.postgres.book.book_dto import BookDTO
from src.infrastructure.postgres.db_util import TimestampMixin
from src.infrastructure.postgres.message.message_dto import MessageDTO

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.message.message_dto import MessageDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO


class ChatDTO(TimestampMixin, Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)
    book_id: Mapped[str | None] = mapped_column(String, ForeignKey("books.id"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["UserDTO"] = relationship("UserDTO", back_populates="chats", uselist=False)
    book: Mapped["BookDTO"] = relationship("BookDTO", back_populates="chats", uselist=False)
    messages: Mapped[list["MessageDTO"]] = relationship(
        "MessageDTO", back_populates="chat", cascade="all, delete-orphan", order_by="MessageDTO.created_at", uselist=True
    )

    def to_entity(self) -> Chat:
        return Chat(
            id=ChatId(value=str(self.id)),
            user_id=UserId(value=str(self.user_id)),
            title=ChatTitle(value=str(self.title)),
            book_id=BookId(value=str(self.book_id)) if self.book_id else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )

    @staticmethod
    def from_entity(chat: Chat) -> "ChatDTO":
        return ChatDTO(
            id=chat.id.value,
            user_id=chat.user_id.value,
            title=chat.title.value,
            book_id=chat.book_id.value if chat.book_id else None,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            deleted_at=chat.deleted_at,
        )
