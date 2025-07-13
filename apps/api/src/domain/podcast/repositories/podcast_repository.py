from abc import ABC, abstractmethod

from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus


class PodcastRepository(ABC):
    """Repository interface for Podcast entities"""

    @abstractmethod
    async def save(self, podcast: Podcast) -> Podcast:
        """Save a podcast entity"""

    @abstractmethod
    async def find_by_id(self, podcast_id: PodcastId) -> Podcast | None:
        """Find a podcast by its ID"""

    @abstractmethod
    async def find_by_book_id(self, book_id: BookId) -> list[Podcast]:
        """Find all podcasts for a specific book"""

    @abstractmethod
    async def find_by_book_id_and_user_id(self, book_id: BookId, user_id: UserId) -> Podcast | None:
        """Find a podcast by book ID and user ID"""

    @abstractmethod
    async def update(self, podcast: Podcast) -> Podcast:
        """Update an existing podcast"""

    @abstractmethod
    async def update_status(
        self,
        podcast_id: PodcastId,
        status: PodcastStatus,
        audio_url: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update podcast status and optionally audio_url or error_message"""

    @abstractmethod
    async def delete(self, podcast_id: PodcastId) -> None:
        """Delete a podcast by its ID"""

    @abstractmethod
    async def find_by_status(self, status: PodcastStatus) -> list[Podcast]:
        """Find all podcasts with a specific status"""
