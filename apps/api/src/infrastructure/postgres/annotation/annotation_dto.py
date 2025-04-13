from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from src.db import Base
from src.domain.annotation.value_objects.annotation_color import AnnotationColorEnum
from src.domain.annotation.value_objects.annotation_type import AnnotationTypeEnum
from src.infrastructure.postgres.db_util import TimestampMixin


class AnnotationDTO(Base, TimestampMixin):
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
        default=AnnotationTypeEnum.HIGHLIGHT,
        nullable=False,
    )
    spine = Column(JSON, nullable=True)

    book = relationship("BookDTO", back_populates="annotations", uselist=False)
    user = relationship("UserDTO", back_populates="annotations", uselist=False)
