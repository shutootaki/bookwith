"""RequestIdMiddleware のテスト.

X-Request-ID をレスポンスに付与し、リクエスト側で送られた値があれば検証して尊重する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.request_id import register_request_id


def _build_app() -> FastAPI:
    app = FastAPI()
    register_request_id(app)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "yes"}

    return app


def test_response_has_request_id_header():
    client = TestClient(_build_app())
    res = client.get("/ping")
    assert res.status_code == 200
    rid = res.headers.get("x-request-id")
    assert rid
    assert len(rid) >= 16  # uuid hex は 32 文字


def test_request_id_is_unique_per_request():
    client = TestClient(_build_app())
    rid1 = client.get("/ping").headers.get("x-request-id")
    rid2 = client.get("/ping").headers.get("x-request-id")
    assert rid1 != rid2


def test_client_provided_request_id_is_respected():
    client = TestClient(_build_app())
    custom_id = "trace-abc-123"
    res = client.get("/ping", headers={"X-Request-ID": custom_id})
    assert res.headers.get("x-request-id") == custom_id


def test_invalid_client_request_id_is_replaced():
    """変な制御文字や長すぎる ID を受け取った場合は捨てて新規生成する."""
    client = TestClient(_build_app())
    bad_id = "x" * 200  # 128 文字超
    res = client.get("/ping", headers={"X-Request-ID": bad_id})
    rid = res.headers.get("x-request-id")
    assert rid != bad_id
    assert rid
    assert len(rid) <= 128


def test_request_id_invalid_chars_replaced():
    client = TestClient(_build_app())
    res = client.get(
        "/ping",
        headers={"X-Request-ID": "evil id with space"},
    )
    rid = res.headers.get("x-request-id")
    assert rid != "evil id with space"
    assert rid
