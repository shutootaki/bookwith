from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.exceptions.podcast_exceptions import PodcastNotFoundError, PodcastPermissionDeniedError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.usecase.shared.access_control import resolve_owned_or_raise_async


class FindPodcastByIdUseCase:
    """Use case for finding a podcast by its ID (with ownership verification)."""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, podcast_id: PodcastId, user_id: UserId) -> Podcast:
        """Find a podcast scoped to the authenticated user."""
        return await resolve_owned_or_raise_async(
            find_for_user=lambda: self.podcast_repository.find_by_id_for_user(podcast_id, user_id),
            find_any=lambda: self.podcast_repository.find_by_id(podcast_id),
            not_found_exc=PodcastNotFoundError(str(podcast_id)),
            forbidden_exc=PodcastPermissionDeniedError(str(podcast_id)),
        )
