from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[DateTime]:
        return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @declared_attr
    def updated_at(cls) -> Mapped[DateTime]:
        return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
