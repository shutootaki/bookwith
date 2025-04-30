from datetime import datetime

from pydantic import Field

from src.presentation.api.schemas.base_schema import BaseSchemaModel


class ChatCreateRequest(BaseSchemaModel):
    user_id: str = Field(..., description="ユーザーID")
    title: str | None = Field(None, description="チャットのタイトル", max_length=255)
    book_id: str | None = Field(None, description="関連する本のID")


class ChatUpdateTitleRequest(BaseSchemaModel):
    title: str = Field(..., description="更新するチャットのタイトル", max_length=255)


class ChatResponse(BaseSchemaModel):
    id: str = Field(..., description="チャットID")
    user_id: str = Field(..., description="ユーザーID")
    title: str = Field(..., description="チャットのタイトル")
    book_id: str | None = Field(None, description="関連する本のID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
