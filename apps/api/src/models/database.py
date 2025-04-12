import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from src.db import Base


class User(Base):
    """ユーザーモデル"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # リレーションシップ
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    annotations = relationship(
        "Annotation", back_populates="user", cascade="all, delete-orphan"
    )
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")


class Book(Base):
    """書籍モデル"""

    __tablename__ = "books"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    name = Column(String, index=True)
    author = Column(String, index=True, nullable=True)
    file_path = Column(String)
    cover_path = Column(String, nullable=True)
    size = Column(Integer)
    cfi = Column(String, nullable=True)
    percentage = Column(Integer, default=0)
    book_metadata = Column(JSON, nullable=True)
    definitions = Column(JSON, default=list)
    configuration = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # 論理削除用のタイムスタンプ

    user = relationship("User", back_populates="books")
    annotations = relationship(
        "Annotation", back_populates="book", cascade="all, delete-orphan"
    )
    chats = relationship("Chat", back_populates="book", cascade="all, delete-orphan")


class Annotation(Base):
    """アノテーション（注釈、ハイライト）モデル"""

    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(String, ForeignKey("books.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    cfi = Column(String, index=True)
    text = Column(Text)
    note = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="annotations")
    user = relationship("User", back_populates="annotations")


class Chat(Base):
    """チャットセッションモデル"""

    __tablename__ = "chats"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    book_id = Column(String, ForeignKey("books.id"), index=True, nullable=True)

    title = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chats")
    book = relationship("Book", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class SenderTypeEnum(enum.Enum):
    user = "user"
    ai = "ai"


class Message(Base):
    """チャットメッセージモデル"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(String, ForeignKey("chats.id"), index=True, nullable=False)

    sender_type = Column(SQLAlchemyEnum(SenderTypeEnum), index=True, nullable=False)
    content = Column(Text, nullable=False)
    related_message_id = Column(
        Integer, ForeignKey("messages.id"), nullable=True, index=True
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    replaced_message = relationship(
        "Message",
        remote_side=[id],
        backref="replacing_message",
        foreign_keys=[related_message_id],
    )
