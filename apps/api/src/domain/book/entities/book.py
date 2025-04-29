from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.domain.book.value_objects.tennant_id import TenantId


class Book(BaseModel):
    id: BookId
    name: BookTitle
    user_id: str
    file_path: str
    author: str | None = None
    cover_path: str | None = None
    size: int = 0
    cfi: str | None = None
    percentage: float = 0.0
    book_metadata: dict[str, Any] = Field(default_factory=dict)
    definitions: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    annotations: list[Annotation] = Field(default_factory=list)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Value Object を許容するため
        json_encoders={
            BookId: lambda x: x.value,
            BookTitle: lambda x: x.value,
            TenantId: lambda x: x.value,
        },
    )

    @classmethod
    def create(
        cls,
        id: BookId,
        name: BookTitle,
        user_id: str,
        file_path: str,
        author: str | None = None,
        cover_path: str | None = None,
        size: int = 0,
        book_metadata: dict[str, Any] | None = None,
    ) -> "Book":
        # Pydanticがデフォルト値を処理するため、ここでは単純にインスタンス化する
        return cls(
            id=id,
            name=name,
            user_id=user_id,
            file_path=file_path,
            author=author,
            cover_path=cover_path,
            size=size,
            book_metadata=book_metadata or {},
        )

    def update_title(self, name: BookTitle) -> None:
        self.name = name
        self.updated_at = datetime.now()

    def update_reading_progress(self, cfi: str, percentage: float) -> None:
        self.cfi = cfi
        self.percentage = percentage
        self.updated_at = datetime.now()

    def mark_as_deleted(self) -> None:
        if not self.deleted_at:
            self.deleted_at = datetime.now()
            self.updated_at = datetime.now()

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.id == other.id
