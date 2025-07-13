from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SpeakerRoleEnum(str, Enum):
    HOST = "HOST"
    GUEST = "GUEST"


@dataclass(frozen=True)
class SpeakerRole:
    value: SpeakerRoleEnum

    def __post_init__(self) -> None:
        if not isinstance(self.value, SpeakerRoleEnum):
            raise ValueError("SpeakerRole must be a SpeakerRoleEnum instance")

    def __str__(self) -> str:
        return self.value.value

    @classmethod
    def host(cls) -> SpeakerRole:
        return cls(SpeakerRoleEnum.HOST)

    @classmethod
    def guest(cls) -> SpeakerRole:
        return cls(SpeakerRoleEnum.GUEST)

    @classmethod
    def from_string(cls, value: str) -> SpeakerRole:
        return cls(SpeakerRoleEnum(value))

    def is_host(self) -> bool:
        return self.value == SpeakerRoleEnum.HOST

    def is_guest(self) -> bool:
        return self.value == SpeakerRoleEnum.GUEST
