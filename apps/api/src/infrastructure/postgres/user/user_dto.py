from sqlalchemy import (
    Column,
    DateTime,
    String,
)
from sqlalchemy.orm import relationship

from src.db import Base
from src.infrastructure.postgres.db_util import TimestampMixin


class UserDTO(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    deleted_at = Column(DateTime, nullable=True)

    books = relationship("BookDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    annotations = relationship("AnnotationDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    chats = relationship("ChatDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
    messages = relationship("MessageDTO", back_populates="user", cascade="all, delete-orphan", uselist=True)
