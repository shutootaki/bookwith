from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO
    from src.infrastructure.postgres.book.book_dto import BookDTO
    from src.infrastructure.postgres.chat.chat_dto import ChatDTO
    from src.infrastructure.postgres.message.message_dto import MessageDTO
    from src.infrastructure.postgres.user.user_dto import UserDTO

__all__ = ["UserDTO", "BookDTO", "AnnotationDTO", "ChatDTO", "MessageDTO"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "AnnotationDTO":
        from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO

        return AnnotationDTO
    if name == "BookDTO":
        from src.infrastructure.postgres.book.book_dto import BookDTO

        return BookDTO
    if name == "ChatDTO":
        from src.infrastructure.postgres.chat.chat_dto import ChatDTO

        return ChatDTO
    if name == "MessageDTO":
        from src.infrastructure.postgres.message.message_dto import MessageDTO

        return MessageDTO
    if name == "UserDTO":
        from src.infrastructure.postgres.user.user_dto import UserDTO

        return UserDTO
    raise AttributeError(name)
