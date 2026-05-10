from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.user.user_dto import UserDTO

__all__ = ["UserDTO"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "UserDTO":
        from src.infrastructure.postgres.user.user_dto import UserDTO

        return UserDTO
    raise AttributeError(name)
