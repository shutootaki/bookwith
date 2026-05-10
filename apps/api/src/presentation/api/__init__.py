from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.presentation.api.routes import setup_routes

__all__ = ["setup_routes"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "setup_routes":
        from src.presentation.api.routes import setup_routes

        return setup_routes
    raise AttributeError(name)
