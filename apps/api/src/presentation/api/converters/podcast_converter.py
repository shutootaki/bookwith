"""Converter functions for Podcast domain objects to API response schemas

Note: 将来的にはBookエンティティと同様に、Podcastエンティティのmodel_dump(mode="json")を
直接使用し、PodcastResponseのfrom_attributes=Trueと組み合わせることで、
このconverterレイヤーを削除できる可能性があります。
例: PodcastResponse(**podcast.model_dump(mode="json"))
"""

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
        script_data = [PodcastScriptTurn(speaker=turn.speaker.value.value, text=turn.text) for turn in podcast.script.turns]

    return PodcastResponse(
        id=podcast.id.value,
        book_id=podcast.book_id.value,
        user_id=podcast.user_id.value,
        title=podcast.title,
        status=podcast.status.value.value,
        language=podcast.language,
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
