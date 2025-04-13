import enum

from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship

from src.db import Base
from src.infrastructure.database.models import TimestampMixin


class AnnotationDTO(Base, TimestampMixin):
    """アノテーション（注釈、ハイライト）モデル.
    アノテーションデータとORM（SQLAlchemy）モデル間の変換を行うDTOクラス.
    """

    class AnnotationTypeEnum(enum.Enum):
        highlight = "highlight"

    class AnnotationColorEnum(enum.Enum):
        yellow = "yellow"
        red = "red"
        green = "green"
        blue = "blue"

    __tablename__ = "annotations"

    id = Column(String, primary_key=True, index=True)
    book_id = Column(String, ForeignKey("books.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    cfi = Column(String, index=True)
    text = Column(Text)
    notes = Column(Text, nullable=True)
    color = Column(SQLAlchemyEnum(AnnotationColorEnum), nullable=True)
    type = Column(
        SQLAlchemyEnum(AnnotationTypeEnum),
        default=AnnotationTypeEnum.highlight,
        nullable=False,
    )
    spine = Column(JSON, nullable=True)

    book = relationship("BookDTO", back_populates="annotations")
    user = relationship("User", back_populates="annotations")
