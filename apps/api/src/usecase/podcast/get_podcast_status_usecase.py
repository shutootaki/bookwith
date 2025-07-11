import logging
from typing import Any

from src.domain.podcast.exceptions.podcast_exceptions import PodcastNotFoundError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId

logger = logging.getLogger(__name__)


class GetPodcastStatusUseCase:
    """Use case for getting podcast generation status"""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, podcast_id: PodcastId) -> dict[str, Any]:
        """Get the status and details of a podcast

        Args:
            podcast_id: ID of the podcast

        Returns:
            Dictionary containing podcast status information

        Raises:
            PodcastNotFoundError: If podcast doesn't exist

        """
        try:
            podcast = await self.podcast_repository.find_by_id(podcast_id)

            if not podcast:
                raise PodcastNotFoundError(str(podcast_id))

            status_info: dict[str, Any] = {
                "id": str(podcast.id),
                "status": str(podcast.status),
                "title": podcast.title,
                "book_id": str(podcast.book_id),
                "user_id": str(podcast.user_id),
                "audio_url": podcast.audio_url,
                "error_message": podcast.error_message,
                "created_at": podcast.created_at.isoformat(),
                "updated_at": podcast.updated_at.isoformat(),
                "has_script": podcast.script is not None,
            }

            # Add script details if available
            if podcast.script:
                status_info.update(
                    {
                        "script_turn_count": podcast.script.get_turn_count(),
                        "script_character_count": podcast.script.get_total_length(),
                    }
                )

            logger.debug(f"Retrieved status for podcast {podcast_id}: {podcast.status}")

            return status_info

        except PodcastNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting podcast status {podcast_id}: {str(e)}")
            raise
