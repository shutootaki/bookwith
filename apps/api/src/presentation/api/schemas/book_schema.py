from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.book.entities.book import Book


class BookCreateRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    file_data: str = Field(..., description="Base64 encoded file data")
    file_name: str = Field(..., description="File name")
    book_id: str | None = Field(None, description="Book ID (auto-generated if not specified)")
    book_name: str | None = Field(None, description="Book name (file name is used if not specified)")
    cover_image: str | None = Field(None, description="Base64 encoded cover image data")
    book_metadata: str | None = Field(None, description="Book metadata (JSON string)")


class AnnotationSchemaTmp(BaseModel):
    class AnnotationType(str, Enum):
        highlight = "highlight"

    class AnnotationColor(str, Enum):
        yellow = "yellow"
        red = "red"
        green = "green"
        blue = "blue"

    id: str
    book_id: str = Field(alias="bookId")
    cfi: str
    spine: dict[str, Any]
    type: AnnotationType
    color: AnnotationColor
    notes: str | None = None
    text: str

    class Config:
        from_attributes = True
        populate_by_name = True


class BookUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Book name")
    author: str | None = Field(None, description="Author name")
    cfi: str | None = Field(None, description="Current reading position (CFI)")
    percentage: float | None = Field(None, description="Reading progress percentage (%)")
    annotations: list[AnnotationSchemaTmp] | None = Field(None, description="Annotation information")
    book_metadata: dict[str, Any] | None = Field(None, description="Book metadata")
    definitions: list[dict[str, Any]] | None = Field(None, description="User defined information")
    configuration: dict[str, Any] | None = Field(None, description="Book configuration information")


class BookDetail(BaseModel):
    id: str
    annotations: list[AnnotationSchemaTmp] | None = None
    author: str | None = None
    book_metadata: dict[str, Any] | None = None
    cfi: str | None = None
    configuration: dict[str, Any] | None = None
    cover_path: str | None = None
    definitions: list[str] = []
    has_cover: bool = False
    name: str
    percentage: float = 0
    size: int

    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class BookResponse(BaseModel):
    success: bool
    data: BookDetail
    message: str | None = None


class BooksResponse(BaseModel):
    success: bool
    data: list[BookDetail]
    count: int
    message: str | None = None


class BookFileResponse(BaseModel):
    success: bool
    url: str
    message: str | None = None


class BulkDeleteResponse(BaseModel):
    success: bool
    deletedIds: list[str]
    count: int
    message: str | None = None


def entity_to_detail(book: Book) -> BookDetail:
    return BookDetail(
        id=book.id.value,
        name=book.title.value,
        author=book.author,
        cover_path=book.cover_path,
        size=book.size,
        cfi=book.cfi,
        percentage=book.percentage,
        book_metadata=book.book_metadata,
        definitions=book.definitions,
        configuration=book.configuration,
        created_at=book.created_at,
        updated_at=book.updated_at,
        annotations=book.annotations,
    )
