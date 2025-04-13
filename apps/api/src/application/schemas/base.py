from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


# 共通モデル
class BaseResponse(BaseModel):
    """基本レスポンスモデル"""

    success: bool = True
    message: str | None = None


# エラーモデル
class ErrorDetail(BaseModel):
    """エラー詳細モデル"""

    loc: list[str | int] | None = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """標準エラーレスポンスモデル"""

    success: bool = False
    detail: str
    status_code: int
    errors: list[ErrorDetail] | None = None


# Root エンドポイント用モデル
class RootResponse(BaseResponse):
    """ルートエンドポイントのレスポンスモデル"""

    message: str = "BookWith FastAPI Server"


# Auth エンドポイント用モデル
class CallbackRequest(BaseModel):
    """認証コールバックのリクエストモデル"""

    provider: str
    state: str
    code: str


class CallbackResponse(BaseResponse):
    """認証コールバックのレスポンスモデル"""

    redirect_url: HttpUrl


class RefreshTokenRequest(BaseModel):
    """トークンリフレッシュのリクエストモデル"""

    refresh_token: str


class TokenResponse(BaseModel):
    """トークンレスポンスモデル"""

    access_token: str
    access_token_expires_at: int | None = None


class Annotation(BaseModel):
    """アノテーションモデル"""

    class AnnotationType(str, Enum):
        """アノテーションタイプ列挙型"""

        highlight = "highlight"

    class AnnotationColor(str, Enum):
        """アノテーション色列挙型"""

        yellow = "yellow"
        red = "red"
        green = "green"
        blue = "blue"

    """アノテーションモデル"""

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


class BookDetail(BaseModel):
    """書籍の詳細情報モデル"""

    id: str
    annotations: list[Annotation] | None = None
    author: str | None = None
    book_metadata: dict[str, Any] | None = None
    cfi: str | None = None
    configuration: dict[str, Any] | None = None
    cover_path: str | None = None
    definitions: list[str] = []
    has_cover: bool = False
    name: str
    percentage: int = 0
    size: int

    created_at: Any
    updated_at: Any

    @field_validator("has_cover")
    def set_has_cover(cls, v, values):
        return "cover_path" in values and values["cover_path"] is not None

    class Config:
        from_attributes = True


class BookResponse(BaseResponse):
    """書籍レスポンスモデル"""

    data: BookDetail


class BooksResponse(BaseResponse):
    """複数書籍レスポンスモデル"""

    data: list[BookDetail]
    count: int


class BookCreateRequest(BaseModel):
    """書籍作成リクエストモデル"""

    file_data: str
    file_name: str
    file_type: str
    user_id: str
    book_id: str | None
    book_name: str | None
    book_metadata: str | None
    cover_image: str | None


class BookFileResponse(BaseResponse):
    """書籍ファイルのレスポンスモデル"""

    url: str


class BookUpdateRequest(BaseModel):
    """書籍更新リクエストモデル"""

    annotations: list[Annotation] | None = None
    author: str | None = None
    book_metadata: dict[str, Any] | None = None
    cfi: str | None = None
    configuration: dict[str, Any] | None = None
    cover_path: str | None = None
    definitions: list[str] | None = None
    is_deleted: bool | None = None
    name: str | None = None
    percentage: float | None = None

    @field_validator("percentage")
    def validate_percentage(cls, v):
        if v is not None:
            # 小数値が送信された場合、内部的には整数として扱う
            return int(v)
        return v


# LLM エンドポイント用モデル
class Question(BaseModel):
    """質問リクエストモデル"""

    question: str
    tenant_id: str | None = None


class Answer(BaseModel):
    """回答レスポンスモデル"""

    answer: str


class RagUploadRequest(BaseModel):
    """RAGアップロードリクエストモデル"""

    file: Any = Field(..., description="アップロードするEPUBファイル")
    user_id: str = Field(..., description="ユーザーID (テナント分離に使用)")


class RagChunk(BaseModel):
    """RAG処理で生成されたテキストチャンク"""

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagProcessResponse(BaseResponse):
    """RAG処理レスポンスモデル"""

    file_name: str
    chunk_count: int
    tenant_id: str | None = None
    index_name: str | None = None
    chunks: list[RagChunk] | None = None
