from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from src.domain.message.value_objects.sender_type import SenderTypeEnum
from src.presentation.api.schemas.base_schema import BaseRequestSchemaModel, BaseSchemaModel

_MAX_MESSAGE_CONTENT = 30_000
_MAX_METADATA_KEYS = 32

# M-4: クライアントから送信できる metadata キーを限定する。
# プロンプト関連のメタデータを攻撃者が自由設定できると、LLM コンテキスト汚染や
# 内部処理ルートの分岐操作に繋がる可能性があるため、明示的な allow-list で受け付ける。
_ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "client_message_id",
        "ui_locale",
        "ui_theme",
        "ui_session_id",
        "selected_text",
        "highlight_id",
        "annotation_id",
        "model_preference",
    }
)
_MAX_METADATA_VALUE_LEN = 4_000


def _sanitize_metadata(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("metadata must be an object")
    if len(value) > _MAX_METADATA_KEYS:
        raise ValueError(f"metadata has too many keys (max {_MAX_METADATA_KEYS})")
    sanitized: dict[str, Any] = {}
    for k, v in value.items():
        if not isinstance(k, str):
            raise ValueError("metadata keys must be strings")
        if k not in _ALLOWED_METADATA_KEYS:
            # 未知のキーは静かに捨てる（クライアント拡張で勝手に追加されても無害化）。
            continue
        if v is None:
            sanitized[k] = None
            continue
        if isinstance(v, bool | int | float):
            sanitized[k] = v
            continue
        if isinstance(v, str):
            if len(v) > _MAX_METADATA_VALUE_LEN:
                raise ValueError(f"metadata value too long for key '{k}'")
            sanitized[k] = v
            continue
        # その他の型は文字列化して長さ制限を適用する。
        coerced = str(v)
        if len(coerced) > _MAX_METADATA_VALUE_LEN:
            raise ValueError(f"metadata value too long for key '{k}'")
        sanitized[k] = coerced
    return sanitized


class MessageBase(BaseRequestSchemaModel):
    """メッセージの基本モデル."""

    content: str = Field(..., description="メッセージの内容", min_length=1, max_length=_MAX_MESSAGE_CONTENT)
    chat_id: str = Field(..., description="メッセージが所属するチャットID", max_length=64)


class MessageCreate(MessageBase):
    """メッセージ作成リクエストモデル."""

    # CR-4: sender_id は認証 user_id から取得するため受け取らない。
    metadata: dict[str, Any] | None = Field(None, description="メッセージの追加情報", max_length=_MAX_METADATA_KEYS)
    book_id: str | None = Field(None, description="メッセージが所属するブックID", max_length=64)

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _sanitize_metadata(value)


class MessageUpdate(BaseRequestSchemaModel):
    """メッセージ更新リクエストモデル."""

    content: str | None = Field(None, description="メッセージの内容", max_length=_MAX_MESSAGE_CONTENT)
    # CR-4: sender_type の自由設定はロール詐称につながるため受け取らない。
    metadata: dict[str, Any] | None = Field(None, description="メッセージの追加情報", max_length=_MAX_METADATA_KEYS)

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _sanitize_metadata(value)


class MessageBulkDelete(BaseRequestSchemaModel):
    """複数メッセージ削除リクエストモデル."""

    # H-12: 件数上限。
    message_ids: list[str] = Field(..., description="削除するメッセージIDのリスト", min_length=1, max_length=200)


class MessageResponse(BaseSchemaModel):
    """メッセージレスポンスモデル."""

    id: str
    content: str
    sender_id: str
    sender_type: SenderTypeEnum
    chat_id: str
    created_at: datetime
    metadata: dict[str, Any] | None = None


class MessageListResponse(BaseSchemaModel):
    """メッセージリストレスポンスモデル."""

    messages: list[MessageResponse]
    total: int


class FailedMessageIdsResponse(BaseSchemaModel):
    """失敗したメッセージIDレスポンスモデル."""

    failed_ids: list[str]
