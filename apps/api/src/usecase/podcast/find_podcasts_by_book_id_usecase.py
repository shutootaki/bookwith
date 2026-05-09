import logging

from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.repositories.podcast_repository import PodcastRepository

logger = logging.getLogger(__name__)


class FindPodcastsByBookIdUseCase:
    """Use case for finding podcasts by book ID (with ownership verification)."""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, book_id: BookId, user_id: UserId) -> list[Podcast]:
        return await self.podcast_repository.find_by_book_id_for_user(book_id, user_id)
