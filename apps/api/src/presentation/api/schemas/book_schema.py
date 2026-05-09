from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from src.presentation.api.schemas.annotation_schema import AnnotationSchema
from src.presentation.api.schemas.base_schema import BaseRequestSchemaModel, BaseSchemaModel


# CR-4 / M-3: クライアント由来の user_id / sender_id / book_id を排除し、
# 認証 principal とパス引数から導出する。
# 文字列フィールドは長さ上限を必須化（XSS / DoS 軽減）。

_MAX_NAME_LEN = 500
_MAX_AUTHOR_LEN = 500
_MAX_DESCRIPTION_LEN = 5000
_MAX_CFI_LEN = 1000
_MAX_DEFINITIONS_LEN = 200
_MAX_DEFINITION_ITEM_LEN = 200
_MAX_BOOK_METADATA_BYTES = 32_000  # JSON サイズ概算
_MAX_BOOK_METADATA_KEYS = 64
_MAX_FILE_NAME = 255

# H-1 / M-3: アップロードサイズ上限。base64 のため実バイトは ~1.37x。
# 25MB 程度。app_config の MAX_UPLOAD_BYTES と整合。
_MAX_FILE_DATA_LEN = 40 * 1024 * 1024


class BookCreateRequest(BaseRequestSchemaModel):
    file_data: str = Field(..., description="Base64 encoded file data", max_length=_MAX_FILE_DATA_LEN)
    file_name: str = Field(..., description="File name", max_length=_MAX_FILE_NAME)
    book_id: str | None = Field(None, description="Book ID (auto-generated if not specified)", max_length=64)
    book_name: str | None = Field(None, description="Book name (file name is used if not specified)", max_length=_MAX_NAME_LEN)
    cover_image: str | None = Field(None, description="Base64 encoded cover image data", max_length=_MAX_FILE_DATA_LEN)
    book_metadata: str | None = Field(None, description="Book metadata (JSON string)", max_length=_MAX_BOOK_METADATA_BYTES)


class BookUpdateRequest(BaseRequestSchemaModel):
    name: str | None = Field(None, description="Book name", max_length=_MAX_NAME_LEN)
    author: str | None = Field(None, description="Author name", max_length=_MAX_AUTHOR_LEN)
    cfi: str | None = Field(None, description="Current reading position (CFI)", max_length=_MAX_CFI_LEN)
    percentage: float | None = Field(None, ge=0, le=100, description="Reading progress percentage (%)")
    annotations: list[AnnotationSchema] | None = Field(None, description="Annotation information", max_length=10_000)
    book_metadata: dict[str, Any] | None = Field(None, description="Book metadata", max_length=_MAX_BOOK_METADATA_KEYS)
    definitions: list[str] | None = Field(None, description="User defined information", max_length=_MAX_DEFINITIONS_LEN)
    configuration: dict[str, Any] | None = Field(None, description="Book configuration information", max_length=_MAX_BOOK_METADATA_KEYS)
    metadata_title: str | None = Field(None, max_length=_MAX_NAME_LEN, description="Book title from metadata")
    metadata_creator: str | None = Field(None, max_length=_MAX_AUTHOR_LEN, description="Book creator/author from metadata")
    metadata_description: str | None = Field(None, max_length=_MAX_DESCRIPTION_LEN, description="Book description from metadata")
    metadata_pubdate: str | None = Field(None, max_length=255, description="Publication date from metadata")
    metadata_publisher: str | None = Field(None, max_length=_MAX_NAME_LEN, description="Publisher from metadata")
    metadata_identifier: str | None = Field(None, max_length=255, description="Book identifier from metadata")
    metadata_language: str | None = Field(None, max_length=64, description="Language from metadata")
    metadata_rights: str | None = Field(None, max_length=_MAX_DESCRIPTION_LEN, description="Rights information from metadata")
    metadata_modified_date: str | None = Field(None, max_length=255, description="Modified date from metadata")
    metadata_layout: str | None = Field(None, max_length=64, description="Layout setting from metadata")
    metadata_orientation: str | None = Field(None, max_length=64, description="Orientation setting from metadata")
    metadata_flow: str | None = Field(None, max_length=64, description="Flow setting from metadata")
    metadata_viewport: str | None = Field(None, max_length=255, description="Viewport setting from metadata")
    metadata_spread: str | None = Field(None, max_length=64, description="Spread setting from metadata")


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

    @classmethod
    def from_entity(cls, book: Any) -> "BookDetail":
        return cls(**book.model_dump(mode="json"))


class BookResponse(BaseSchemaModel):
    book_detail: BookDetail


class BooksResponse(BaseSchemaModel):
    books: list[BookDetail]
    count: int


class BookFileResponse(BaseSchemaModel):
    url: str


class BulkDeleteRequestBody(BaseRequestSchemaModel):
    # H-12: 件数上限を明示。1リクエストで全データ削除を阻止。
    book_ids: list[str] = Field(..., min_length=1, max_length=100)


class BulkDeleteResponse(BaseSchemaModel):
    deleted_ids: list[str]
    count: int


class RagProcessRequest(BaseRequestSchemaModel):
    # CR-4: user_id は認証から取得。リクエストでは受けない。
    book_id: str = Field(..., max_length=64)
    file_data: str = Field(..., max_length=_MAX_FILE_DATA_LEN)
    file_name: str = Field(..., max_length=_MAX_FILE_NAME)


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
