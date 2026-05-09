"""SecurityHeadersMiddleware のテスト.

L-04 補強。CSP / HSTS / X-Frame-Options / X-Content-Type-Options 等が
すべて HTTP レスポンスに付与されていることを検証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.security_headers import register_security_headers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_security_headers(app)

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    return app


def test_security_headers_attached() -> None:
    client = TestClient(_build_app())
    res = client.get("/ping")
    assert res.status_code == 200
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("referrer-policy") == "no-referrer"
    assert "max-age=" in (res.headers.get("strict-transport-security") or "")
    assert res.headers.get("cross-origin-opener-policy") == "same-origin"
    assert res.headers.get("cross-origin-resource-policy") == "same-site"
    assert "geolocation=" in (res.headers.get("permissions-policy") or "")


def test_security_headers_do_not_overwrite_existing() -> None:
    """既にハンドラが X-Frame-Options を付けていたら上書きしないこと."""
    app = FastAPI()
    register_security_headers(app)

    @app.get("/custom")
    async def custom() -> dict:
        from fastapi import Response

        resp = Response(content='{"ok":true}', media_type="application/json")
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp  # type: ignore[return-value]

    client = TestClient(app)
    res = client.get("/custom")
    assert res.headers.get("x-frame-options") == "SAMEORIGIN"


def test_authenticated_paths_get_no_store_cache_control() -> None:
    """認証必須エンドポイントのレスポンスは `Cache-Control: no-store` でキャッシュ漏洩を抑止."""
    client = TestClient(_build_app())
    res = client.get("/ping")
    assert res.headers.get("cache-control") == "no-store"
    assert res.headers.get("pragma") == "no-cache"


def test_health_and_ready_paths_are_exempt_from_cache_control() -> None:
    """health/ready/docs は冪等な公開メタエンドポイントなのでキャッシュ抑止しない."""
    app = FastAPI()
    register_security_headers(app)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True}

    @app.get("/ready")
    async def ready() -> dict:
        return {"ok": True}

    @app.get("/docs/anything")
    async def docs_path() -> dict:
        return {"ok": True}

    client = TestClient(app)
    for url in ("/health", "/ready", "/docs/anything"):
        res = client.get(url)
        # 公開メタなので Cache-Control を強制付与しない
        assert "no-store" not in (res.headers.get("cache-control") or "")


def test_existing_cache_control_is_respected() -> None:
    """ハンドラ側で `Cache-Control` を明示している場合はミドルウェアで上書きしない."""
    from fastapi import Response

    app = FastAPI()
    register_security_headers(app)

    @app.get("/cached")
    async def cached() -> Response:
        return Response(
            content='{"ok":true}',
            media_type="application/json",
            headers={"Cache-Control": "public, max-age=60"},
        )

    client = TestClient(app)
    res = client.get("/cached")
    assert res.headers.get("cache-control") == "public, max-age=60"
