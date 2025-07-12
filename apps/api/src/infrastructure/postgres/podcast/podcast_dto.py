from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.db import Base
from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_script import PodcastScript, ScriptTurnDict
from src.domain.podcast.value_objects.podcast_status import PodcastStatus, PodcastStatusEnum
from src.infrastructure.postgres.db_util import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO


class PodcastDTO(TimestampMixin, Base):
    __tablename__ = "podcasts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    book_id: Mapped[str] = mapped_column(String, ForeignKey("books.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[PodcastStatusEnum] = mapped_column(
        Enum(PodcastStatusEnum, name="podcast_status_enum"),
        nullable=False,
        default=PodcastStatusEnum.PENDING,
    )
    script: Mapped[list[ScriptTurnDict] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    book: Mapped["BookDTO"] = relationship("BookDTO", back_populates="podcasts", uselist=False)
    user: Mapped["UserDTO"] = relationship("UserDTO", back_populates="podcasts", uselist=False)

    def to_entity(self) -> Podcast:
        """Convert DTO to domain entity"""
        script_obj = None
        if self.script:
            script_obj = PodcastScript.from_list(self.script)

        return Podcast(
            id=PodcastId(self.id),
            book_id=BookId(self.book_id),
            user_id=UserId(self.user_id),
            title=str(self.title),
            audio_url=str(self.audio_url) if self.audio_url else None,
            status=PodcastStatus.from_string(str(self.status.value)),
            script=script_obj,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, podcast: Podcast) -> "PodcastDTO":
        """Create DTO from domain entity"""
        script_data = None
        if podcast.script:
            script_data = podcast.script.to_list()

        return cls(
            id=podcast.id.value,
            book_id=podcast.book_id.value,
            user_id=podcast.user_id.value,
            title=podcast.title,
            audio_url=podcast.audio_url,
            status=podcast.status.value,
            script=script_data,
            error_message=podcast.error_message,
            created_at=podcast.created_at,
            updated_at=podcast.updated_at,
        )
