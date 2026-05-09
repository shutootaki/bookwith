"""認証 Depends 単体テスト.

`get_current_user` の dev_bypass / 不正 UUID / 既存実装の挙動を検証する。
"""

from __future__ import annotations

import os

# AppConfig 初期化前に環境変数を必須で揃える。
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("AUTH_DEV_BYPASS", "false")
os.environ.setdefault("SUPABASE_JWT_SECRET", "")

import importlib

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def _reload_auth() -> tuple[object, object]:
    """環境変数変更後に AppConfig と auth.dependencies をリロードする."""
    from src.config import app_config

    importlib.reload(app_config)
    from src.presentation.api.auth import dependencies as auth_dep

    importlib.reload(auth_dep)
    return app_config, auth_dep


def _build_app(auth_dep) -> FastAPI:  # noqa: ANN001
    from src.presentation.api.error_messages.error_handlers import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/whoami")
    async def whoami(user_id: str = Depends(auth_dep.require_user_id)):  # noqa: ANN001
        return {"user_id": user_id}

    return app


def test_dev_bypass_invalid_uuid_returns_401(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("AUTH_DEV_BYPASS_USER_ID", "not-a-uuid")
    monkeypatch.setenv("ENVIRONMENT", "development")

    _, auth_dep = _reload_auth()
    app = _build_app(auth_dep)
    client = TestClient(app)

    res = client.get("/whoami")
    assert res.status_code == 401, res.text


def test_dev_bypass_valid_uuid_returns_200(monkeypatch):
    bypass_id = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("AUTH_DEV_BYPASS_USER_ID", bypass_id)
    monkeypatch.setenv("ENVIRONMENT", "development")

    _, auth_dep = _reload_auth()
    app = _build_app(auth_dep)
    client = TestClient(app)

    res = client.get("/whoami")
    assert res.status_code == 200
    assert res.json()["user_id"] == bypass_id


def test_authenticated_user_dataclass_is_frozen():
    _, auth_dep = _reload_auth()
    user = auth_dep.AuthenticatedUser(user_id="11111111-1111-1111-1111-111111111111")
    with pytest.raises(Exception):
        user.user_id = "22222222-2222-2222-2222-222222222222"  # type: ignore[misc]


def test_no_bearer_returns_401_without_bypass(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")

    _, auth_dep = _reload_auth()
    app = _build_app(auth_dep)
    client = TestClient(app)

    res = client.get("/whoami")
    assert res.status_code == 401
