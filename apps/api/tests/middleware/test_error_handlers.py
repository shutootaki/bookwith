"""error_handlers のテスト.

H-5: 例外メッセージがクライアントに漏れない。AppException は固定文言、
generic Exception は "Internal server error"。ValidationError は 422 で
errors 配列を返す。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from src.presentation.api.error_messages.error_handlers import (
    AppException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    setup_exception_handlers,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/raise-app")
    async def raise_app() -> dict:
        raise AppException("custom app error", status_code=418)

    @app.get("/raise-bad")
    async def raise_bad() -> dict:
        raise BadRequestException("bad input")

    @app.get("/raise-401")
    async def raise_401() -> dict:
        raise UnauthorizedException

    @app.get("/raise-403")
    async def raise_403() -> dict:
        raise ForbiddenException

    @app.get("/raise-404")
    async def raise_404() -> dict:
        raise NotFoundException

    @app.get("/raise-generic")
    async def raise_generic() -> dict:
        raise RuntimeError("internal secret detail")

    class Body(BaseModel):
        value: int = Field(..., ge=0)

    @app.post("/validate")
    async def validate(body: Body) -> dict:
        return body.model_dump()

    return app


def test_app_exception_returns_custom_status_and_detail():
    client = TestClient(_build_app())
    res = client.get("/raise-app")
    assert res.status_code == 418
    assert res.json()["detail"] == "custom app error"
    assert res.json()["success"] is False


def test_bad_request_returns_400():
    client = TestClient(_build_app())
    res = client.get("/raise-bad")
    assert res.status_code == 400
    assert res.json()["detail"] == "bad input"


def test_unauthorized_returns_401():
    client = TestClient(_build_app())
    res = client.get("/raise-401")
    assert res.status_code == 401
    assert res.json()["detail"] == "Authentication required"


def test_forbidden_returns_403():
    client = TestClient(_build_app())
    res = client.get("/raise-403")
    assert res.status_code == 403


def test_not_found_returns_404():
    client = TestClient(_build_app())
    res = client.get("/raise-404")
    assert res.status_code == 404


def test_generic_exception_does_not_leak_detail():
    """H-5: 内部例外文字列はレスポンスに混入しない."""
    client = TestClient(_build_app(), raise_server_exceptions=False)
    res = client.get("/raise-generic")
    assert res.status_code == 500
    body = res.json()
    assert body["detail"] == "Internal server error"
    # 内部の文字列が漏れていないこと
    assert "internal secret detail" not in body.get("detail", "")
    assert "RuntimeError" not in body.get("detail", "")


def test_validation_error_returns_422_with_errors():
    client = TestClient(_build_app())
    res = client.post("/validate", json={"value": -1})
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["status_code"] == 422
    assert len(body["errors"]) >= 1
