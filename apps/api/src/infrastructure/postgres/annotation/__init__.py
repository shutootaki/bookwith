from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO

__all__ = ["AnnotationDTO"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "AnnotationDTO":
        from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO

        return AnnotationDTO
    raise AttributeError(name)
