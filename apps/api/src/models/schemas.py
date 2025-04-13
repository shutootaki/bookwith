from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# 共通モデル
class BaseResponse(BaseModel):
    """基本レスポンスモデル"""

    success: bool = True
    message: Optional[str] = None


# エラーモデル
class ErrorDetail(BaseModel):
    """エラー詳細モデル"""

    loc: Optional[List[str | int]] = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """標準エラーレスポンスモデル"""

    success: bool = False
    detail: str
    status_code: int
    errors: Optional[List[ErrorDetail]] = None


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
    access_token_expires_at: Optional[int] = None


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
    spine: Dict[str, Any]
    type: AnnotationType
    color: AnnotationColor
    notes: Optional[str] = None
    text: str

    class Config:
        from_attributes = True
        populate_by_name = True


class BookDetail(BaseModel):
    """書籍の詳細情報モデル"""

    id: str
    annotations: Optional[List[Annotation]] = None
    author: Optional[str] = None
    book_metadata: Optional[Dict[str, Any]] = None
    cfi: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    cover_path: Optional[str] = None
    definitions: List[str] = []
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

    data: List[BookDetail]
    count: int


class BookCreateRequest(BaseModel):
    """書籍作成リクエストモデル"""

    file_data: str
    file_name: str
    file_type: str
    user_id: str
    book_id: Optional[str]
    book_name: Optional[str]
    book_metadata: Optional[str]
    cover_image: Optional[str]


class BookFileResponse(BaseResponse):
    """書籍ファイルのレスポンスモデル"""

    url: str


class BookUpdateRequest(BaseModel):
    """書籍更新リクエストモデル"""

    annotations: Optional[List[Annotation]] = None
    author: Optional[str] = None
    book_metadata: Optional[Dict[str, Any]] = None
    cfi: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    cover_path: Optional[str] = None
    definitions: Optional[List[str]] = None
    is_deleted: Optional[bool] = None
    name: Optional[str] = None
    percentage: Optional[float] = None

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
    tenant_id: Optional[str] = None


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
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagProcessResponse(BaseResponse):
    """RAG処理レスポンスモデル"""

    file_name: str
    chunk_count: int
    tenant_id: Optional[str] = None
    index_name: Optional[str] = None
    chunks: Optional[List[RagChunk]] = None
