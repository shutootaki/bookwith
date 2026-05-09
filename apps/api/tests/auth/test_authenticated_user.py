"""AuthenticatedUser dataclass の不変性テスト.

CR-1 補強: 認証 principal を表す `AuthenticatedUser` は frozen dataclass で
属性書き換え不可。間違って middleware や handler が user_id を上書きする経路を
封じる回帰検出。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import dataclasses

import pytest

from src.presentation.api.auth.dependencies import AuthenticatedUser


def test_dataclass_is_frozen():
    user = AuthenticatedUser(user_id="11111111-1111-1111-1111-111111111111")
    with pytest.raises(dataclasses.FrozenInstanceError):
        user.user_id = "22222222-2222-2222-2222-222222222222"  # type: ignore[misc]


def test_email_optional_default_none():
    user = AuthenticatedUser(user_id="11111111-1111-1111-1111-111111111111")
    assert user.email is None


def test_email_value_carried_through():
    user = AuthenticatedUser(
        user_id="11111111-1111-1111-1111-111111111111",
        email="user@example.com",
    )
    assert user.email == "user@example.com"


def test_equality_based_on_fields():
    a = AuthenticatedUser(user_id="11111111-1111-1111-1111-111111111111")
    b = AuthenticatedUser(user_id="11111111-1111-1111-1111-111111111111")
    c = AuthenticatedUser(user_id="22222222-2222-2222-2222-222222222222")
    assert a == b
    assert a != c
