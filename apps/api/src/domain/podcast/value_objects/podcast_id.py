from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PodcastId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PodcastId value cannot be empty")

        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError("PodcastId must be a valid UUID")

    @classmethod
    def generate(cls) -> PodcastId:
        return cls(str(uuid.uuid4()))
