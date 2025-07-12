from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .speaker_role import SpeakerRole


class ScriptTurnDict(TypedDict):
    speaker: str
    text: str


@dataclass(frozen=True)
class ScriptTurn:
    speaker: SpeakerRole
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.speaker, SpeakerRole):
            raise ValueError("speaker must be a SpeakerRole instance")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be a non-empty string")

    def to_dict(self) -> ScriptTurnDict:
        return {"speaker": str(self.speaker), "text": self.text}

    @classmethod
    def from_dict(cls, data: ScriptTurnDict) -> ScriptTurn:
        return cls(speaker=SpeakerRole.from_string(data["speaker"]), text=data["text"])


@dataclass(frozen=True)
class PodcastScript:
    turns: list[ScriptTurn]

    def __post_init__(self) -> None:
        if not isinstance(self.turns, list):
            raise ValueError("turns must be a list")
        if not self.turns:
            raise ValueError("turns cannot be empty")
        for turn in self.turns:
            if not isinstance(turn, ScriptTurn):
                raise ValueError("All turns must be ScriptTurn instances")

    def to_list(self) -> list[ScriptTurnDict]:
        return [turn.to_dict() for turn in self.turns]

    @classmethod
    def from_list(cls, data: list[ScriptTurnDict]) -> PodcastScript:
        turns = [ScriptTurn.from_dict(turn_data) for turn_data in data]
        return cls(turns=turns)

    def get_total_length(self) -> int:
        """Get total character count of all text in the script"""
        return sum(len(turn.text) for turn in self.turns)

    def get_turn_count(self) -> int:
        """Get the number of turns in the script"""
        return len(self.turns)
