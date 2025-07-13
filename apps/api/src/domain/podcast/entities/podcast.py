from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_script import PodcastScript
from src.domain.podcast.value_objects.podcast_status import PodcastStatus


class Podcast(BaseModel):
    """Podcast domain entity implemented with Pydantic."""

    id: PodcastId
    book_id: BookId
    user_id: UserId
    title: str
    status: PodcastStatus
    language: PodcastLanguage = PodcastLanguage.EN_US
    audio_url: str | None = None
    script: PodcastScript | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            PodcastId: lambda x: x.value,
            BookId: lambda x: x.value,
            UserId: lambda x: x.value,
            PodcastStatus: lambda x: str(x),
            PodcastScript: lambda x: x.to_list() if x else None,
        },
    )

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("title must be a non-empty string")
        return v

    def update_status(
        self,
        status: PodcastStatus,
        audio_url: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update podcast status and related fields"""
        self.status = status
        if audio_url is not None:
            self.audio_url = audio_url
        if error_message is not None:
            self.error_message = error_message
        self.updated_at = datetime.now(UTC)

    def set_script(self, script: PodcastScript) -> None:
        """Set the podcast script"""
        self.script = script
        self.updated_at = datetime.now(UTC)

    def mark_as_processing(self) -> None:
        """Mark podcast as processing"""
        self.update_status(PodcastStatus.processing())

    def mark_as_completed(self, audio_url: str) -> None:
        """Mark podcast as completed with audio URL"""
        if not audio_url:
            raise ValueError("audio_url is required when marking as completed")
        self.update_status(PodcastStatus.completed(), audio_url=audio_url)

    def mark_as_failed(self, error_message: str) -> None:
        """Mark podcast as failed with error message"""
        if not error_message:
            raise ValueError("error_message is required when marking as failed")
        self.update_status(PodcastStatus.failed(), error_message=error_message)

    def can_be_processed(self) -> bool:
        """Check if podcast can be processed"""
        return self.status.can_process()

    def is_completed(self) -> bool:
        """Check if podcast is completed"""
        return self.status.is_completed()

    def is_failed(self) -> bool:
        """Check if podcast generation failed"""
        return self.status.is_failed()
