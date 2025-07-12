from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for declarative SQLAlchemy models"""

    # Include default repr for easier debugging
    def __repr__(self) -> str:  # pragma: no cover
        attrs = " ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
        return f"<{self.__class__.__name__} {attrs}>"


class TimestampMixin:
    """Mixin class to add created_at and updated_at timestamps to SQLAlchemy models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
