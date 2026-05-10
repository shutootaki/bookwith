"""BodySizeLimitMiddleware のテスト.

H-1 強化として導入した `BodySizeLimitMiddleware` が、
- 上限以下のリクエストは通す
- Content-Length 超過時は 413 で拒否する
- チャンク受信でも累積バイトで 413 を返す
ことを検証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("AUTH_DEV_BYPASS", "true")
os.environ.setdefault("AUTH_DEV_BYPASS_USER_ID", "11111111-1111-1111-1111-111111111111")
os.environ.setdefault("MAX_UPLOAD_BYTES", "1024")  # 1KB（テスト用）

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.body_size_limit import (
    BodySizeLimitMiddleware,
    register_body_size_limit,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_body_size_limit(app)

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return {"received_keys": sorted(payload.keys())}

    return app


def test_small_payload_passes_through():
    app = _build_app()
    client = TestClient(app)
    res = client.post("/echo", json={"hello": "world"})
    assert res.status_code == 200
    assert res.json()["received_keys"] == ["hello"]


def test_oversized_content_length_returns_413():
    app = _build_app()
    client = TestClient(app)
    # ボディは小さくても、Content-Length ヘッダで 100MB を主張すると 413 になる。
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(100 * 1024 * 1024),
    }
    res = client.post("/echo", data='{"hello":"world"}', headers=headers)
    assert res.status_code == 413


def test_oversized_chunked_body_returns_413():
    app = _build_app()
    client = TestClient(app)
    # 上限 1KB + 余裕 7MB = 約 7MB が body 上限。8MB の本文は 413。
    big_body = b'{"data":"' + b"a" * (8 * 1024 * 1024) + b'"}'
    res = client.post(
        "/echo",
        data=big_body,
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 413


def test_middleware_class_signature():
    """Middleware が ASGI app を正しく wrap している."""
    app = FastAPI()
    middleware = BodySizeLimitMiddleware(app)
    assert middleware.app is app


def test_non_http_scope_passes_through():
    """Websocket / lifespan scope は素通しすること."""
    import asyncio

    received: list[dict] = []

    async def fake_app(scope, receive, send) -> None:
        received.append(scope)

    middleware = BodySizeLimitMiddleware(fake_app)
    ws_scope = {"type": "websocket"}

    async def _noop_receive():
        return {}

    async def _noop_send(_) -> None:
        return None

    asyncio.run(middleware(ws_scope, _noop_receive, _noop_send))
    assert received == [ws_scope]


def test_get_request_skips_content_length_check():
    """GET は Content-Length チェック対象外。"""
    app = FastAPI()
    register_body_size_limit(app)

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    client = TestClient(app)
    # 100MB を主張する Content-Length を付けても GET なので素通り
    res = client.get("/ping", headers={"Content-Length": str(100 * 1024 * 1024)})
    assert res.status_code == 200
