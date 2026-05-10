"""不正トークンの拒否を検証するテスト.

CR-1: dev_bypass を切った状態で、Bearer 形式 / 不正 JWT / 形式不正の Authorization ヘッダーが
すべて 401 になることを保証する。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")


def _build_unauthenticated_app(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")

    from src.config import app_config

    importlib.reload(app_config)
    from src.presentation.api.auth import dependencies as auth_dep

    importlib.reload(auth_dep)

    from fastapi import Depends, FastAPI

    from src.presentation.api.error_messages.error_handlers import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/protected")
    async def protected(user_id: str = Depends(auth_dep.require_user_id)):
        return {"user_id": user_id}

    return app


def test_no_authorization_header_401(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_unauthenticated_app(monkeypatch)
    client = TestClient(app)
    res = client.get("/protected")
    assert res.status_code == 401


def test_malformed_authorization_header_401(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_unauthenticated_app(monkeypatch)
    client = TestClient(app)

    # "Bearer" だけ（トークンなし）
    res = client.get("/protected", headers={"Authorization": "Bearer"})
    assert res.status_code == 401

    # 別 scheme（Basic）
    res = client.get("/protected", headers={"Authorization": "Basic abc"})
    assert res.status_code == 401


def test_invalid_jwt_returns_401(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_unauthenticated_app(monkeypatch)
    client = TestClient(app)

    res = client.get(
        "/protected",
        headers={"Authorization": "Bearer not.a.real.jwt.token"},
    )
    assert res.status_code == 401


def test_jwt_secret_missing_returns_401(monkeypatch):
    """SUPABASE_JWT_SECRET が空のままだと、たとえ正規っぽい JWT を送っても 401."""
    from fastapi.testclient import TestClient

    app = _build_unauthenticated_app(monkeypatch)
    client = TestClient(app)

    # ベース64 dummy（HS256 にはならない）
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTExMTEifQ.signature"
    res = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {fake_jwt}"},
    )
    assert res.status_code == 401
