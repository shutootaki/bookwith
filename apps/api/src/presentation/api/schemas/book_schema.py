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
    metadata_title: str | None = Field(None, description="Book title from metadata")
    metadata_creator: str | None = Field(None, description="Book creator/author from metadata")
    metadata_description: str | None = Field(None, description="Book description from metadata")
    metadata_pubdate: str | None = Field(None, description="Publication date from metadata")
    metadata_publisher: str | None = Field(None, description="Publisher from metadata")
    metadata_identifier: str | None = Field(None, description="Book identifier from metadata")
    metadata_language: str | None = Field(None, description="Language from metadata")
    metadata_rights: str | None = Field(None, description="Rights information from metadata")
    metadata_modified_date: str | None = Field(None, description="Modified date from metadata")
    metadata_layout: str | None = Field(None, description="Layout setting from metadata")
    metadata_orientation: str | None = Field(None, description="Orientation setting from metadata")
    metadata_flow: str | None = Field(None, description="Flow setting from metadata")
    metadata_viewport: str | None = Field(None, description="Viewport setting from metadata")
    metadata_spread: str | None = Field(None, description="Spread setting from metadata")


class BookDetail(BaseSchemaModel):
    id: str
    annotations: list[AnnotationSchema] | None = None
    author: str | None = None
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
    metadata_title: str | None = None
    metadata_creator: str | None = None
    metadata_description: str | None = None
    metadata_pubdate: str | None = None
    metadata_publisher: str | None = None
    metadata_identifier: str | None = None
    metadata_language: str | None = None
    metadata_rights: str | None = None
    metadata_modified_date: str | None = None
    metadata_layout: str | None = None
    metadata_orientation: str | None = None
    metadata_flow: str | None = None
    metadata_viewport: str | None = None
    metadata_spread: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookResponse(BaseSchemaModel):
    book_detail: BookDetail


class BooksResponse(BaseSchemaModel):
    books: list[BookDetail]
    count: int


class BookFileResponse(BaseSchemaModel):
    url: str


class BulkDeleteRequestBody(BaseSchemaModel):
    book_ids: list[str]


class BulkDeleteResponse(BaseSchemaModel):
    deleted_ids: list[str]
    count: int


class RagProcessRequest(BaseSchemaModel):
    user_id: str
    book_id: str
    file_data: str
    file_name: str


class RagProcessResponse(BaseSchemaModel):
    class RagChunk(BaseSchemaModel):
        text: str
        metadata: dict[str, Any] = {}

    file_name: str
    chunk_count: int
    user_id: str | None = None
    index_name: str | None = None
    chunks: list[RagChunk] | None = None


class CoversResponse(BaseSchemaModel):
    class CoverData(BaseSchemaModel):
        book_id: str
        name: str
        cover_url: str

    covers: list[CoverData]
