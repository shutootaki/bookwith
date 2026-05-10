from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.message.message_dto import MessageDTO
    from src.infrastructure.postgres.message.message_repository import MessageRepositoryImpl

__all__ = ["MessageDTO", "MessageRepositoryImpl"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "MessageDTO":
        from src.infrastructure.postgres.message.message_dto import MessageDTO

        return MessageDTO
    if name == "MessageRepositoryImpl":
        from src.infrastructure.postgres.message.message_repository import MessageRepositoryImpl

        return MessageRepositoryImpl
    raise AttributeError(name)
