from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from src.config.app_config import TEST_USER_ID
from src.presentation.api.schemas.annotation_schema import AnnotationSchema
from src.presentation.api.schemas.base_schema import BaseSchemaModel


class BookCreateRequest(BaseSchemaModel):
    user_id: str = Field(..., description="User ID")
    file_data: str = Field(..., description="Base64 encoded file data")
    file_name: str = Field(..., description="File name")
    book_id: str | None = Field(None, description="Book ID (auto-generated if not specified)")
    book_name: str | None = Field(None, description="Book name (file name is used if not specified)")
    cover_image: str | None = Field(None, description="Base64 encoded cover image data")
    book_metadata: str | None = Field(None, description="Book metadata (JSON string)")


class BookUpdateRequest(BaseSchemaModel):
    user_id: str = Field(TEST_USER_ID, description="User ID")
    name: str | None = Field(None, description="Book name")
    author: str | None = Field(None, description="Author name")
    cfi: str | None = Field(None, description="Current reading position (CFI)")
    percentage: float | None = Field(None, description="Reading progress percentage (%)")
    annotations: list[AnnotationSchema] | None = Field(None, description="Annotation information")
    book_metadata: dict[str, Any] | None = Field(None, description="Book metadata")
    definitions: list[str] | None = Field(None, description="User defined information")
    configuration: dict[str, Any] | None = Field(None, description="Book configuration information")


class BookDetail(BaseSchemaModel):
    id: str
    annotations: list[AnnotationSchema] | None = None
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
    user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BookResponse(BaseSchemaModel):
    success: bool
    data: BookDetail
    message: str | None = None


class BooksResponse(BaseSchemaModel):
    success: bool
    data: list[BookDetail]
    count: int
    message: str | None = None


class BookFileResponse(BaseSchemaModel):
    success: bool
    url: str
    message: str | None = None


class BulkDeleteRequestBody(BaseSchemaModel):
    book_ids: list[str]


class BulkDeleteResponse(BaseSchemaModel):
    success: bool
    deleted_ids: list[str]
    count: int
    message: str | None = None


class RagProcessResponse(BaseSchemaModel):
    class RagChunk(BaseSchemaModel):
        text: str
        metadata: dict[str, Any] = {}

    success: bool
    message: str | None = None
    file_name: str
    chunk_count: int
    user_id: str | None = None
    index_name: str | None = None
    chunks: list[RagChunk] | None = None
