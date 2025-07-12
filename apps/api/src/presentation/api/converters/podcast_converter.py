"""Converter functions for Podcast domain objects to API response schemas"""

from src.domain.podcast.entities.podcast import Podcast
from src.presentation.api.schemas.podcast_schema import (
    PodcastResponse,
    PodcastScriptTurn,
)


def convert_podcast_to_response(podcast: Podcast) -> PodcastResponse:
    """Convert Podcast domain entity to PodcastResponse schema

    Args:
        podcast: Podcast domain entity

    Returns:
        PodcastResponse schema object

    """
    # Convert script to response format
    script_data = None
    if podcast.script:
        script_data = [PodcastScriptTurn(speaker=str(turn.speaker), text=turn.text) for turn in podcast.script.turns]

    return PodcastResponse(
        id=str(podcast.id),
        book_id=str(podcast.book_id),
        user_id=str(podcast.user_id),
        title=podcast.title,
        status=str(podcast.status),
        audio_url=podcast.audio_url,
        error_message=podcast.error_message,
        script=script_data,
        created_at=podcast.created_at,
        updated_at=podcast.updated_at,
    )


def convert_podcasts_to_response_list(podcasts: list[Podcast]) -> list[PodcastResponse]:
    """Convert list of Podcast domain entities to list of PodcastResponse schemas

    Args:
        podcasts: List of Podcast domain entities

    Returns:
        List of PodcastResponse schema objects

    """
    return [convert_podcast_to_response(podcast) for podcast in podcasts]
