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
    async def find_by_id_for_user(self, podcast_id: PodcastId, user_id: UserId) -> Podcast | None:
        """CR-3: 指定 user_id 所有の Podcast のみ返す"""

    @abstractmethod
    async def find_by_book_id(self, book_id: BookId) -> list[Podcast]:
        """Find all podcasts for a specific book"""

    @abstractmethod
    async def find_by_book_id_for_user(self, book_id: BookId, user_id: UserId) -> list[Podcast]:
        """CR-3: 指定 user_id 所有の book に紐づく Podcast のみ返す"""

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
    async def update_status_with_optimistic_lock(
        self,
        podcast_id: PodcastId,
        expected_status: PodcastStatus,
        new_status: PodcastStatus,
        audio_url: str | None = None,
        error_message: str | None = None,
        clear_error_message: bool = False,
    ) -> bool:
        """M-1: 楽観ロック付き status 更新。expected_status の場合のみ更新する。

        clear_error_message=True で前回失敗時の error_message を NULL に戻す。
        """

    @abstractmethod
    async def delete_for_user(self, podcast_id: PodcastId, user_id: UserId) -> bool:
        """CR-3: 指定 user_id 所有の Podcast のみ削除する"""

    @abstractmethod
    async def find_by_status(self, status: PodcastStatus) -> list[Podcast]:
        """Find all podcasts with a specific status"""
