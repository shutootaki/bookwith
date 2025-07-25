from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.db import Base
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.chat.chat_dto import ChatDTO
    from src.infrastructure.postgres.message.message_dto import MessageDTO
    from src.infrastructure.postgres.podcast.podcast_dto import PodcastDTO


class UserDTO(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))

    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    books: Mapped[list["BookDTO"]] = relationship("BookDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    chats: Mapped[list["ChatDTO"]] = relationship("ChatDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    messages: Mapped[list["MessageDTO"]] = relationship("MessageDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    podcasts: Mapped[list["PodcastDTO"]] = relationship("PodcastDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
