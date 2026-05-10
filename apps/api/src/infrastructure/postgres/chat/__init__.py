from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.chat.chat_dto import ChatDTO

__all__ = ["ChatDTO"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "ChatDTO":
        from src.infrastructure.postgres.chat.chat_dto import ChatDTO

        return ChatDTO
    raise AttributeError(name)
