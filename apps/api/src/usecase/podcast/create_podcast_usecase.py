import logging
from datetime import UTC, datetime

from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.exceptions.podcast_exceptions import PodcastAlreadyExistsError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus

logger = logging.getLogger(__name__)


class CreatePodcastUseCase:
    """Use case for creating a new podcast"""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, book_id: BookId, user_id: UserId, title: str) -> PodcastId:
        """Create a new podcast for a book

        Args:
            book_id: ID of the book to create podcast for
            user_id: ID of the user creating the podcast
            title: Title for the podcast

        Returns:
            ID of the created podcast

        Raises:
            PodcastAlreadyExistsError: If podcast already exists for this book and user

        """
        # Check if podcast already exists
        existing_podcast = await self.podcast_repository.find_by_book_id_and_user_id(book_id, user_id)

        if existing_podcast:
            raise PodcastAlreadyExistsError(str(book_id), str(user_id))

        # Create new podcast
        podcast_id = PodcastId.generate()
        podcast = Podcast(
            id=podcast_id,
            book_id=book_id,
            user_id=user_id,
            title=title,
            status=PodcastStatus.pending(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Save to repository
        saved_podcast = await self.podcast_repository.save(podcast)

        logger.info(f"Created podcast {podcast_id} for book {book_id}")

        return saved_podcast.id
