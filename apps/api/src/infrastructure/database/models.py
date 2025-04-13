import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[DateTime]:
        return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @declared_attr
    def updated_at(cls) -> Mapped[DateTime]:
        return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class User(Base, TimestampMixin):
    """ユーザーモデル"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    deleted_at = Column(DateTime, nullable=True)

    books = relationship("BookDTO", back_populates="user", cascade="all, delete-orphan")
    annotations = relationship("AnnotationDTO", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")


# class BookDTO(Base, TimestampMixin):
#     """書籍モデル"""

#     __tablename__ = "books"

#     id = Column(String, primary_key=True, index=True)
#     user_id = Column(String, ForeignKey("users.id"), index=True)

#     name = Column(String, index=True)
#     author = Column(String, index=True, nullable=True)
#     file_path = Column(String)
#     cover_path = Column(String, nullable=True)
#     size = Column(Integer)
#     cfi = Column(String, nullable=True)
#     percentage = Column(Integer, default=0)
#     book_metadata = Column(JSON, nullable=True)
#     definitions = Column(JSON, default=list)
#     configuration = Column(JSON, nullable=True)
#     deleted_at = Column(DateTime, nullable=True)

#     user = relationship("User", back_populates="books")
#     annotations = relationship(
#         "Annotation", back_populates="book", cascade="all, delete-orphan"
#     )
#     chats = relationship("Chat", back_populates="book", cascade="all, delete-orphan")


# class Annotation(Base, TimestampMixin):
#     """アノテーション（注釈、ハイライト）モデル"""

#     class AnnotationTypeEnum(enum.Enum):
#         """アノテーションタイプ列挙型"""

#         highlight = "highlight"

#     class AnnotationColorEnum(enum.Enum):
#         """アノテーション色列挙型"""

#         yellow = "yellow"
#         red = "red"
#         green = "green"
#         blue = "blue"

#     __tablename__ = "annotations"

#     id = Column(String, primary_key=True, index=True)
#     book_id = Column(String, ForeignKey("books.id"), index=True)
#     user_id = Column(String, ForeignKey("users.id"), index=True)

#     cfi = Column(String, index=True)
#     text = Column(Text)
#     notes = Column(Text, nullable=True)
#     color = Column(SQLAlchemyEnum(AnnotationColorEnum), nullable=True)
#     type = Column(
#         SQLAlchemyEnum(AnnotationTypeEnum),
#         default=AnnotationTypeEnum.highlight,
#         nullable=False,
#     )
#     spine = Column(JSON, nullable=True)

#     book = relationship("BookDTO", back_populates="annotations")
#     user = relationship("User", back_populates="annotations")


class Chat(Base, TimestampMixin):
    """チャットセッションモデル"""

    __tablename__ = "chats"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    book_id = Column(String, ForeignKey("books.id"), index=True, nullable=True)

    title = Column(String(255), nullable=True, index=True)

    user = relationship("User", back_populates="chats")
    book = relationship("BookDTO", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    """チャットメッセージモデル"""

    class SenderTypeEnum(enum.Enum):
        user = "user"
        ai = "ai"

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(String, ForeignKey("chats.id"), index=True, nullable=False)

    sender_type = Column(SQLAlchemyEnum(SenderTypeEnum), index=True, nullable=False)
    content = Column(Text, nullable=False)
    related_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    chat = relationship("Chat", back_populates="messages")
    replaced_message = relationship(
        "Message",
        remote_side=[id],
        backref="replacing_message",
        foreign_keys=[related_message_id],
    )
