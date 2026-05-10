"""MessageCreate / MessageUpdate のバリデーションテスト.

M-4 / CR-4: metadata の allow-list と値の長さ制限が機能していること。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas.message_schema import (
    MessageBulkDelete,
    MessageCreate,
    MessageUpdate,
)


def test_message_create_drops_unknown_metadata_keys():
    """allow-list 外の key は静かに無視される（クライアント拡張は無害化）."""
    msg = MessageCreate(
        content="hello",
        chat_id="00000000-0000-0000-0000-000000000000",
        metadata={"client_message_id": "abc", "evil_role_override": "system"},
    )
    assert msg.metadata is not None
    assert "client_message_id" in msg.metadata
    assert "evil_role_override" not in msg.metadata


def test_message_create_metadata_value_too_long():
    big_value = "x" * 5_000  # _MAX_METADATA_VALUE_LEN は 4_000
    with pytest.raises(ValidationError):
        MessageCreate(
            content="hi",
            chat_id="00000000-0000-0000-0000-000000000000",
            metadata={"client_message_id": big_value},
        )


def test_message_create_content_max_length_enforced():
    big_content = "a" * 100_000  # _MAX_MESSAGE_CONTENT は 30_000
    with pytest.raises(ValidationError):
        MessageCreate(content=big_content, chat_id="00000000-0000-0000-0000-000000000000")


def test_message_update_drops_unknown_metadata_keys():
    upd = MessageUpdate(metadata={"ui_locale": "ja", "internal_secret": "sk-..."})
    assert upd.metadata == {"ui_locale": "ja"}


def test_message_bulk_delete_max_count():
    # 200 件以下は OK
    MessageBulkDelete(message_ids=[f"{i:08x}-0000-0000-0000-000000000000" for i in range(50)])

    # 201 件は弾く
    with pytest.raises(ValidationError):
        MessageBulkDelete(message_ids=[f"{i:08x}-0000-0000-0000-000000000000" for i in range(201)])


def test_message_bulk_delete_empty_rejected():
    with pytest.raises(ValidationError):
        MessageBulkDelete(message_ids=[])


def test_message_create_extra_field_rejected():
    """CR-4 補強: 予期しないフィールド（sender_id 等）を送ると 422 で弾かれる."""
    with pytest.raises(ValidationError):
        MessageCreate(
            content="hi",
            chat_id="00000000-0000-0000-0000-000000000000",
            sender_id="evil-user",  # type: ignore[call-arg]
        )


def test_message_update_extra_field_rejected():
    """sender_type のロール詐称を強制的に拒否する."""
    with pytest.raises(ValidationError):
        MessageUpdate(content="hi", sender_type="system")  # type: ignore[call-arg]
