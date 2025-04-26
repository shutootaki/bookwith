from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base
from src.domain.book.entities.book import Book
from src.domain.book.value_objects.book_description import BookDescription
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_status import BookStatus, BookStatusEnum
from src.domain.book.value_objects.book_title import BookTitle
from src.domain.book.value_objects.tennant_id import TenantId
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO
    from src.infrastructure.postgres.chat.chat_dto import ChatDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO


class BookDTO(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String, index=True)
    author: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    file_path: Mapped[str] = mapped_column(String)
    cover_path: Mapped[str | None] = mapped_column(String, nullable=True)
    size: Mapped[int] = mapped_column(Integer)
    cfi: Mapped[str | None] = mapped_column(String, nullable=True)
    percentage: Mapped[float] = mapped_column(Float, default=0)
    book_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    definitions: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    configuration: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["UserDTO"] = relationship("UserDTO", back_populates="books")
    annotations: Mapped[list["AnnotationDTO"]] = relationship("AnnotationDTO", back_populates="book", cascade="all, delete-orphan")
    chats: Mapped[list["ChatDTO"]] = relationship("ChatDTO", back_populates="book", cascade="all, delete-orphan")

    def to_entity(self) -> Book:
        book_id = BookId(self.id)
        book_title = BookTitle(self.name)
        book_description = BookDescription(None)  # No description field in current model
        tenant_id = TenantId(self.tenant_id) if self.tenant_id else None

        # Determine status (based on percentage as there's no status field in current model)
        status = BookStatusEnum.NOT_STARTED
        if self.percentage > 0:
            status = BookStatusEnum.IN_PROGRESS

        book_status = BookStatus(status)

        # Convert annotations
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
            user_id=str(self.user_id),
            file_path=str(self.file_path),
            description=book_description,
            status=book_status,
            tenant_id=tenant_id,
            author=str(self.author),
            cover_path=str(self.cover_path),
            size=self.size,
            cfi=str(self.cfi),
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
            "tenant_id": book.tenant_id.value if book.tenant_id else None,
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
            tenant_id=book.tenant_id.value if book.tenant_id else None,
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
