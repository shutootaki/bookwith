from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.db import Base
from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.value_objects.annotation_cfi import AnnotationCfi
from src.domain.annotation.value_objects.annotation_color import AnnotationColor
from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.domain.annotation.value_objects.annotation_notes import AnnotationNotes
from src.domain.annotation.value_objects.annotation_text import AnnotationText
from src.domain.annotation.value_objects.annotation_type import AnnotationType
from src.domain.book.entities.book import Book
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO
    from src.infrastructure.postgres.chat.chat_dto import ChatDTO
    from src.infrastructure.postgres.podcast.podcast_dto import PodcastDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO


class BookDTO(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String, index=True)
    author: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    file_path: Mapped[str] = mapped_column(String)
    cover_path: Mapped[str | None] = mapped_column(String, nullable=True)
    size: Mapped[int] = mapped_column(Integer)
    cfi: Mapped[str | None] = mapped_column(String, nullable=True)
    percentage: Mapped[float] = mapped_column(Float, default=0)
    definitions: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    configuration: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # EPub metadata fields
    metadata_title: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_creator: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_pubdate: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_publisher: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_identifier: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    metadata_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata_rights: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_modified_date: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_layout: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_flow: Mapped[str | None] = mapped_column(String(30), nullable=True)
    metadata_viewport: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_spread: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["UserDTO"] = relationship("UserDTO", back_populates="books")
    annotations: Mapped[list["AnnotationDTO"]] = relationship("AnnotationDTO", back_populates="book", cascade="all, delete-orphan")
    chats: Mapped[list["ChatDTO"]] = relationship("ChatDTO", back_populates="book", cascade="all, delete-orphan")
    podcasts: Mapped[list["PodcastDTO"]] = relationship("PodcastDTO", back_populates="book", cascade="all, delete-orphan")

    def to_entity(self) -> Book:
        book_id = BookId(self.id)
        book_title = BookTitle(self.name)

        # Convert annotations
        annotations_data: list[Annotation] = []
        if self.annotations:
            for annotation in self.annotations:
                annotations_data.append(
                    Annotation(
                        id=AnnotationId(annotation.id),
                        book_id=annotation.book_id,
                        cfi=AnnotationCfi(annotation.cfi),
                        text=AnnotationText(annotation.text),
                        notes=AnnotationNotes(annotation.notes) if annotation.notes else None,
                        color=AnnotationColor(annotation.color.value) if annotation.color else None,
                        type=AnnotationType(annotation.type.value),
                        spine=annotation.spine,
                        created_at=annotation.created_at,
                        updated_at=annotation.updated_at,
                    )
                )

        return Book(
            id=book_id,
            name=book_title,
            user_id=str(self.user_id),
            file_path=str(self.file_path),
            author=str(self.author),
            cover_path=str(self.cover_path),
            size=self.size,
            cfi=self.cfi,
            percentage=self.percentage,
            # EPub metadata fields
            metadata_title=self.metadata_title,
            metadata_creator=self.metadata_creator,
            metadata_description=self.metadata_description,
            metadata_pubdate=self.metadata_pubdate,
            metadata_publisher=self.metadata_publisher,
            metadata_identifier=self.metadata_identifier,
            metadata_language=self.metadata_language,
            metadata_rights=self.metadata_rights,
            metadata_modified_date=self.metadata_modified_date,
            metadata_layout=self.metadata_layout,
            metadata_orientation=self.metadata_orientation,
            metadata_flow=self.metadata_flow,
            metadata_viewport=self.metadata_viewport,
            metadata_spread=self.metadata_spread,
            definitions=self.definitions,
            configuration=self.configuration,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            annotations=annotations_data,
        )

    @staticmethod
    def from_entity(book: Book) -> "BookDTO":
        return BookDTO(
            id=book.id.value,
            user_id=book.user_id,
            name=book.name.value,
            author=book.author,
            file_path=book.file_path,
            cover_path=book.cover_path,
            size=book.size,
            cfi=book.cfi,
            percentage=book.percentage,
            definitions=book.definitions,
            configuration=book.configuration,
            created_at=book.created_at,
            updated_at=book.updated_at,
            deleted_at=book.deleted_at,
            metadata_title=book.metadata_title,
            metadata_creator=book.metadata_creator,
            metadata_description=book.metadata_description,
            metadata_pubdate=book.metadata_pubdate,
            metadata_publisher=book.metadata_publisher,
            metadata_identifier=book.metadata_identifier,
            metadata_language=book.metadata_language,
            metadata_rights=book.metadata_rights,
            metadata_modified_date=book.metadata_modified_date,
            metadata_layout=book.metadata_layout,
            metadata_orientation=book.metadata_orientation,
            metadata_flow=book.metadata_flow,
            metadata_viewport=book.metadata_viewport,
            metadata_spread=book.metadata_spread,
        )
