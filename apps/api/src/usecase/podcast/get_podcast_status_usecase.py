from typing import Any

from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.exceptions.podcast_exceptions import PodcastNotFoundError, PodcastPermissionDeniedError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.usecase.shared.access_control import resolve_owned_or_raise_async


class GetPodcastStatusUseCase:
    """Use case for getting podcast generation status (with ownership verification)."""

    def __init__(self, podcast_repository: PodcastRepository) -> None:
        self.podcast_repository = podcast_repository

    async def execute(self, podcast_id: PodcastId, user_id: UserId) -> dict[str, Any]:
        podcast = await resolve_owned_or_raise_async(
            find_for_user=lambda: self.podcast_repository.find_by_id_for_user(podcast_id, user_id),
            find_any=lambda: self.podcast_repository.find_by_id(podcast_id),
            not_found_exc=PodcastNotFoundError(str(podcast_id)),
            forbidden_exc=PodcastPermissionDeniedError(str(podcast_id)),
        )

        status_info: dict[str, Any] = {
            "id": str(podcast.id),
            "status": str(podcast.status),
            "title": podcast.title,
            "language": podcast.language,
            "book_id": str(podcast.book_id),
            "user_id": str(podcast.user_id),
            "audio_url": podcast.audio_url,
            "error_message": podcast.error_message,
            "created_at": podcast.created_at.isoformat(),
            "updated_at": podcast.updated_at.isoformat(),
            "has_script": podcast.script is not None,
        }

        if podcast.script:
            status_info.update(
                {
                    "script_turn_count": podcast.script.get_turn_count(),
                    "script_character_count": podcast.script.get_total_length(),
                }
            )

        return status_info
