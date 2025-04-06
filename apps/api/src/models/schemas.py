from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


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


# LLM エンドポイント用モデル
class Question(BaseModel):
    """質問リクエストモデル"""

    question: str


class Answer(BaseModel):
    """回答レスポンスモデル"""

    answer: str


# RAG エンドポイント用モデル
class RagUploadRequest(BaseModel):
    """RAGアップロードリクエストモデル"""

    # FastAPIのFile依存関係を使用するため、実際のリクエストボディでは使用されない
    # このモデルはドキュメント生成用
    file: Any = Field(..., description="アップロードするEPUBファイル")


class RagChunk(BaseModel):
    """RAG処理で生成されたテキストチャンク"""

    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagProcessResponse(BaseResponse):
    """RAG処理レスポンスモデル"""

    file_name: str
    chunk_count: int
    chunks: Optional[List[RagChunk]] = None
