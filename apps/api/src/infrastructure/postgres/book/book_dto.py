from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.db import Base
from src.domain.book.entities.book import Book
from src.domain.book.value_objects.book_description import BookDescription
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_status import BookStatus, BookStatusEnum
from src.domain.book.value_objects.book_title import BookTitle
from src.infrastructure.database.models import TimestampMixin


class BookDTO(Base, TimestampMixin):
    __tablename__ = "books"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    name = Column(String, index=True)
    author = Column(String, index=True, nullable=True)
    file_path = Column(String)
    cover_path = Column(String, nullable=True)
    size = Column(Integer)
    cfi = Column(String, nullable=True)
    percentage = Column(Float, default=0)
    book_metadata = Column(JSON, nullable=True)
    definitions = Column(JSON, default=list)
    configuration = Column(JSON, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="books")
    annotations = relationship("AnnotationDTO", back_populates="book", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="book", cascade="all, delete-orphan")

    def to_entity(self) -> Book:
        book_id = BookId(self.id)
        book_title = BookTitle(self.name)
        book_description = BookDescription(None)  # 現在のモデルでは説明フィールドがないため

        # ステータスの決定（現状のモデルにstatusフィールドがないため、完了日に基づいて設定）
        status = BookStatusEnum.NOT_STARTED
        if self.percentage > 0:
            status = BookStatusEnum.IN_PROGRESS

        book_status = BookStatus(status)

        # アノテーションの変換
        annotations_data = []
        if self.annotations:
            for annotation in self.annotations:
                annotations_data.append(
                    {
                        "id": annotation.id,
                        "book_id": annotation.book_id,
                        "user_id": annotation.user_id,
                        "cfi": annotation.cfi,
                        "text": annotation.text,
                        "notes": annotation.notes,
                        "color": annotation.color.value if annotation.color else None,
                        "type": annotation.type.value,
                        "spine": annotation.spine,
                        "created_at": annotation.created_at,
                        "updated_at": annotation.updated_at,
                    }
                )

        return Book(
            id=book_id,
            title=book_title,
            user_id=self.user_id,
            file_path=self.file_path,
            description=book_description,
            status=book_status,
            author=self.author,
            cover_path=self.cover_path,
            size=self.size,
            cfi=self.cfi,
            percentage=self.percentage,
            book_metadata=self.book_metadata,
            definitions=self.definitions,
            configuration=self.configuration,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            annotations=annotations_data,
        )

    @staticmethod
    def to_orm_dict(book: Book) -> dict[str, Any]:
        return {
            "id": book.id.value,
            "user_id": book.user_id,
            "name": book.title.value,
            "author": book.author,
            "file_path": book.file_path,
            "cover_path": book.cover_path,
            "size": book.size,
            "cfi": book.cfi,
            "percentage": book.percentage,
            "book_metadata": book.book_metadata,
            "definitions": book.definitions,
            "configuration": book.configuration,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "deleted_at": book.deleted_at,
        }

    @staticmethod
    def from_entity(book: Book) -> "BookDTO":
        return BookDTO(
            id=book.id.value,
            user_id=book.user_id,
            name=book.title.value,
            author=book.author,
            file_path=book.file_path,
            cover_path=book.cover_path,
            size=book.size,
            cfi=book.cfi,
            percentage=book.percentage,
            book_metadata=book.book_metadata,
            definitions=book.definitions,
            configuration=book.configuration,
            created_at=book.created_at,
            updated_at=book.updated_at,
            deleted_at=book.deleted_at,
        )
