from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.podcast.podcast_repository import PodcastRepositoryImpl

__all__ = ["PodcastRepositoryImpl"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "PodcastRepositoryImpl":
        from src.infrastructure.postgres.podcast.podcast_repository import PodcastRepositoryImpl

        return PodcastRepositoryImpl
    raise AttributeError(name)
