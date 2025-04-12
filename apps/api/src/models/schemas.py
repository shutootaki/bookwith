from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


# 共通モデル
class BaseResponse(BaseModel):
    """基本レスポンスモデル"""

    success: bool = True
    message: Optional[str] = None


# エラーモデル
class ErrorDetail(BaseModel):
    """エラー詳細モデル"""

    loc: Optional[List[str]] = None
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


# Book エンドポイント用モデル
class BookBase(BaseModel):
    """書籍の基本情報モデル"""

    id: str
    name: str
    author: Optional[str] = None
    size: int
    percentage: int = 0
    cfi: Optional[str] = None
    has_cover: bool = False

    @validator("has_cover", pre=True, always=True)
    def set_has_cover(cls, v, values):
        # cover_pathがあればhas_coverをTrue、なければFalseに設定
        return "cover_path" in values and values["cover_path"] is not None

    class Config:
        from_attributes = True


class BookDetail(BookBase):
    """書籍の詳細情報モデル"""

    book_metadata: Optional[Dict[str, Any]] = None
    definitions: List[str] = []
    configuration: Optional[Dict[str, Any]] = None
    cover_path: Optional[str] = None
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class BookResponse(BaseResponse):
    """書籍レスポンスモデル"""

    data: BookDetail


class BooksResponse(BaseResponse):
    """複数書籍レスポンスモデル"""

    data: List[BookBase]
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

    name: Optional[str] = None
    author: Optional[str] = None
    percentage: Optional[float] = None
    cfi: Optional[str] = None
    book_metadata: Optional[Dict[str, Any]] = None
    definitions: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    cover_path: Optional[str] = None

    @validator("percentage")
    def validate_percentage(cls, v):
        if v is not None:
            # 小数値が送信された場合、内部的には整数として扱う
            return int(v)
        return v


# LLM エンドポイント用モデル
class Question(BaseModel):
    """質問リクエストモデル"""

    question: str
    tenant_id: Optional[str] = None  # テナントIDを追加


class Answer(BaseModel):
    """回答レスポンスモデル"""

    answer: str


# RAG エンドポイント用モデル
class RagUploadRequest(BaseModel):
    """RAGアップロードリクエストモデル"""

    # FastAPIのFile依存関係を使用するため、実際のリクエストボディでは使用されない
    # このモデルはドキュメント生成用
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
