from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from src.db import Base
from src.domain.chat.entities.chat import Chat
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId
from src.infrastructure.postgres.db_util import TimestampMixin


class ChatDTO(Base, TimestampMixin):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    book_id = Column(String, ForeignKey("books.id"), index=True, nullable=True)

    title = Column(String(255), index=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("UserDTO", back_populates="chats", uselist=False)
    book = relationship("BookDTO", back_populates="chats", uselist=False)
    messages = relationship("MessageDTO", back_populates="chat", cascade="all, delete-orphan", order_by="MessageDTO.created_at", uselist=True)

    def to_entity(self) -> Chat:
        return Chat(
            id=ChatId(value=self.id),
            user_id=UserId(value=self.user_id),
            title=ChatTitle(value=self.title),
            book_id=BookId(value=self.book_id) if self.book_id else None,
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
