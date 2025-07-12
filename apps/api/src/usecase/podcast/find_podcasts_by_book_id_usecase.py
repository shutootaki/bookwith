import logging

from src.domain.book.value_objects.book_id import BookId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.repositories.podcast_repository import PodcastRepository

logger = logging.getLogger(__name__)


class FindPodcastsByBookIdUseCase:
    """Use case for finding podcasts by book ID"""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, book_id: BookId) -> list[Podcast]:
        """Find all podcasts for a specific book

        Args:
            book_id: ID of the book

        Returns:
            List of podcasts for the book

        """
        try:
            podcasts = await self.podcast_repository.find_by_book_id(book_id)

            logger.debug(f"Found {len(podcasts)} podcasts for book {book_id}")

            return podcasts

        except Exception as e:
            logger.error(f"Error finding podcasts for book {book_id}: {str(e)}")
            raise
