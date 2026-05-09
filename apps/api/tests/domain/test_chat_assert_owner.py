"""Chat.assert_owned_by の単体テスト.

CR-3 補強。Chat エンティティが所有者チェックを正しく行うことを保証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.domain.chat.entities.chat import Chat
from src.domain.chat.exceptions.chat_exceptions import ChatPermissionDeniedError
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId

_OWNER = "11111111-1111-1111-1111-111111111111"
_OTHER = "22222222-2222-2222-2222-222222222222"


def test_assert_owned_by_passes_for_owner():
    chat = Chat.create(user_id=UserId(value=_OWNER), title=ChatTitle(value="hello"))
    chat.assert_owned_by(_OWNER)  # 例外でない


def test_assert_owned_by_raises_for_other_user():
    chat = Chat.create(user_id=UserId(value=_OWNER), title=ChatTitle(value="hello"))
    with pytest.raises(ChatPermissionDeniedError):
        chat.assert_owned_by(_OTHER)


def test_assert_owned_by_strict_string_match():
    """user_id は完全一致でないと弾かれる（前後空白、大文字小文字含む）."""
    chat = Chat.create(user_id=UserId(value=_OWNER), title=ChatTitle(value="hi"))
    with pytest.raises(ChatPermissionDeniedError):
        chat.assert_owned_by(_OWNER.upper())
    with pytest.raises(ChatPermissionDeniedError):
        chat.assert_owned_by(f" {_OWNER} ")
