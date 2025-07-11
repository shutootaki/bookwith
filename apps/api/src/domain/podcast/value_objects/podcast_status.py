from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PodcastStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PodcastStatus:
    value: PodcastStatusEnum

    def __post_init__(self) -> None:
        if not isinstance(self.value, PodcastStatusEnum):
            raise ValueError("PodcastStatus must be a PodcastStatusEnum instance")

    def __str__(self) -> str:
        return self.value.value

    @classmethod
    def pending(cls) -> PodcastStatus:
        return cls(PodcastStatusEnum.PENDING)

    @classmethod
    def processing(cls) -> PodcastStatus:
        return cls(PodcastStatusEnum.PROCESSING)

    @classmethod
    def completed(cls) -> PodcastStatus:
        return cls(PodcastStatusEnum.COMPLETED)

    @classmethod
    def failed(cls) -> PodcastStatus:
        return cls(PodcastStatusEnum.FAILED)

    @classmethod
    def from_string(cls, value: str) -> PodcastStatus:
        return cls(PodcastStatusEnum(value))

    def is_pending(self) -> bool:
        return self.value == PodcastStatusEnum.PENDING

    def is_processing(self) -> bool:
        return self.value == PodcastStatusEnum.PROCESSING

    def is_completed(self) -> bool:
        return self.value == PodcastStatusEnum.COMPLETED

    def is_failed(self) -> bool:
        return self.value == PodcastStatusEnum.FAILED

    def can_process(self) -> bool:
        return self.value in [PodcastStatusEnum.PENDING, PodcastStatusEnum.FAILED]
