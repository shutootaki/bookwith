"""JWT issuer pinning と clock skew leeway のテスト.

`SUPABASE_JWT_ISSUER` が設定されている場合、別 issuer の JWT が拒否されること、
および `SUPABASE_JWT_LEEWAY_SECONDS` で僅かなクロックスキューが許容されることを検証する。
"""

from __future__ import annotations

import importlib
import os
import time
from typing import Any

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

# PyJWT が無い環境ではテストスキップ（CI 上では明示インストール）。
jwt = pytest.importorskip("jwt")


JWT_SECRET = "test-secret-do-not-use-in-prod"
EXPECTED_ISSUER = "https://abc123.supabase.co/auth/v1"
USER_UUID = "11111111-2222-3333-4444-555555555555"


def _make_token(
    *,
    secret: str = JWT_SECRET,
    issuer: str | None = EXPECTED_ISSUER,
    audience: str = "authenticated",
    sub: str = USER_UUID,
    exp_offset: int = 3600,
    iat_offset: int = 0,
) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "aud": audience,
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()) + iat_offset,
    }
    if issuer:
        payload["iss"] = issuer
    return jwt.encode(payload, secret, algorithm="HS256")


def _build_app(monkeypatch, *, issuer: str | None = EXPECTED_ISSUER, leeway: int = 10):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    if issuer is not None:
        monkeypatch.setenv("SUPABASE_JWT_ISSUER", issuer)
    else:
        monkeypatch.delenv("SUPABASE_JWT_ISSUER", raising=False)
    monkeypatch.setenv("SUPABASE_JWT_LEEWAY_SECONDS", str(leeway))

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


def test_token_with_matching_issuer_is_accepted(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, issuer=EXPECTED_ISSUER)
    client = TestClient(app)

    token = _make_token(issuer=EXPECTED_ISSUER)
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["user_id"] == USER_UUID


def test_token_with_wrong_issuer_is_rejected(monkeypatch):
    """別 Supabase プロジェクトの JWT を流し込まれても弾く."""
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, issuer=EXPECTED_ISSUER)
    client = TestClient(app)

    token = _make_token(issuer="https://attacker.supabase.co/auth/v1")
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_token_without_issuer_when_pinning_disabled_is_accepted(monkeypatch):
    """`SUPABASE_JWT_ISSUER` が未設定なら issuer pinning 無し（後方互換）."""
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, issuer=None)
    client = TestClient(app)

    token = _make_token(issuer=None)
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_clock_skew_within_leeway_is_accepted(monkeypatch):
    """わずか先の発行時刻でも leeway 内なら通過する."""
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, issuer=EXPECTED_ISSUER, leeway=10)
    client = TestClient(app)

    # iat が +5 秒先 — leeway=10 内なので通過
    token = _make_token(issuer=EXPECTED_ISSUER, iat_offset=5)
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_expired_beyond_leeway_is_rejected(monkeypatch):
    """Leeway を超える期限切れトークンは弾かれる."""
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, issuer=EXPECTED_ISSUER, leeway=2)
    client = TestClient(app)

    # exp が -120 秒（既に切れて 2 分経過）
    token = _make_token(issuer=EXPECTED_ISSUER, exp_offset=-120)
    res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
