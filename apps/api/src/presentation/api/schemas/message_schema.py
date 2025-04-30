from datetime import datetime
from typing import Any

from pydantic import Field

from src.domain.message.value_objects.sender_type import SenderTypeEnum
from src.presentation.api.schemas.base_schema import BaseSchemaModel


class MessageBase(BaseSchemaModel):
    """メッセージの基本モデル."""

    content: str = Field(..., description="メッセージの内容")
    chat_id: str = Field(..., description="メッセージが所属するチャットID")


class MessageCreate(MessageBase):
    """メッセージ作成リクエストモデル."""

    sender_id: str = Field(..., description="送信者ID")
    metadata: dict[str, Any] | None = Field(None, description="メッセージの追加情報")
    book_id: str | None = Field(None, description="メッセージが所属するブックID")


class MessageUpdate(BaseSchemaModel):
    """メッセージ更新リクエストモデル."""

    content: str | None = Field(None, description="メッセージの内容")
    sender_type: SenderTypeEnum | None = Field(None, description="送信者の種類")
    metadata: dict[str, Any] | None = Field(None, description="メッセージの追加情報")


class MessageBulkDelete(BaseSchemaModel):
    """複数メッセージ削除リクエストモデル."""

    message_ids: list[str] = Field(..., description="削除するメッセージIDのリスト")


class MessageResponse(BaseSchemaModel):
    """メッセージレスポンスモデル."""

    id: str
    content: str
    sender_id: str
    sender_type: SenderTypeEnum
    chat_id: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None


class MessageListResponse(BaseSchemaModel):
    """メッセージリストレスポンスモデル."""

    messages: list[MessageResponse]
    total: int


class FailedMessageIdsResponse(BaseSchemaModel):
    """失敗したメッセージIDレスポンスモデル."""

    failed_ids: list[str]
