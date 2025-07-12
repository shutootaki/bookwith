import logging

from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId

logger = logging.getLogger(__name__)


class FindPodcastByIdUseCase:
    """Use case for finding a podcast by its ID"""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, podcast_id: PodcastId) -> Podcast | None:
        """Find a podcast by its ID

        Args:
            podcast_id: ID of the podcast to find

        Returns:
            Podcast entity if found, None otherwise

        """
        try:
            podcast = await self.podcast_repository.find_by_id(podcast_id)

            if podcast:
                logger.debug(f"Found podcast {podcast_id}")
            else:
                logger.debug(f"Podcast {podcast_id} not found")

            return podcast

        except Exception as e:
            logger.error(f"Error finding podcast {podcast_id}: {str(e)}")
            raise
