from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    success: bool = True
    message: str | None = None


class ErrorDetail(BaseModel):
    loc: list[str | int] | None = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
    status_code: int
    errors: list[ErrorDetail] | None = None


class RootResponse(BaseResponse):
    message: str = "BookWith FastAPI Server"


class Question(BaseModel):
    question: str
    tenant_id: str | None = None


class Answer(BaseModel):
    answer: str


class RagUploadRequest(BaseModel):
    file: Any = Field(..., description="アップロードするEPUBファイル")
    user_id: str = Field(..., description="ユーザーID (テナント分離に使用)")


class RagChunk(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagProcessResponse(BaseResponse):
    file_name: str
    chunk_count: int
    tenant_id: str | None = None
    index_name: str | None = None
    chunks: list[RagChunk] | None = None
