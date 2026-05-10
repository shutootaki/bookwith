"""ヘルスチェックエンドポイントのテスト.

`/health` は Cloud Run / k8s の liveness probe 用。認証不要、固定 JSON 応答。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")
os.environ.setdefault("AUTH_DEV_BYPASS", "true")
os.environ.setdefault("AUTH_DEV_BYPASS_USER_ID", "11111111-1111-1111-1111-111111111111")


def test_health_returns_ok_without_auth(client):
    """認証ヘッダーなしでも 200 OK を返す."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_health_response_has_security_headers(client):
    """SecurityHeadersMiddleware が ヘルスチェックにも適用される."""
    res = client.get("/health")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"


def test_health_not_in_openapi_schema(app):
    """`include_in_schema=False` のため OpenAPI には現れない（公開ドキュメント上は隠す）."""
    schema = app.openapi()
    paths = schema.get("paths", {})
    assert "/health" not in paths
