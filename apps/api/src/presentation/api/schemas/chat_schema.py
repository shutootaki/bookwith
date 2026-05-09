from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from src.presentation.api.schemas.base_schema import BaseRequestSchemaModel, BaseSchemaModel

if TYPE_CHECKING:
    from src.domain.chat.entities.chat import Chat


class ChatCreateRequest(BaseRequestSchemaModel):
    # CR-4: user_id は認証から取得するため、リクエストでは受けない。
    title: str | None = Field(None, description="チャットのタイトル", max_length=255)
    book_id: str | None = Field(None, description="関連する本のID", max_length=64)


class ChatUpdateTitleRequest(BaseRequestSchemaModel):
    title: str = Field(..., description="更新するチャットのタイトル", min_length=1, max_length=255)


class ChatResponse(BaseSchemaModel):
    id: str = Field(..., description="チャットID")
    user_id: str = Field(..., description="ユーザーID")
    title: str = Field(..., description="チャットのタイトル")
    book_id: str | None = Field(None, description="関連する本のID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    @classmethod
    def from_entity(cls, chat: "Chat") -> "ChatResponse":
        return cls(
            id=chat.id.value,
            user_id=chat.user_id.value,
            title=chat.title.value if chat.title else None,
            book_id=chat.book_id.value if chat.book_id else None,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )


class ChatsResponse(BaseSchemaModel):
    chats: list[ChatResponse] = Field(..., description="チャットリスト")
