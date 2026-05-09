"""OpenAPI スキーマに Bearer scheme が含まれることを検証する.

CR-1 補強: フロントの `pnpm openapi:ts` で型生成する際に `Authorization: Bearer <jwt>`
が必須であることが伝わる構造になっていることを保証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")
os.environ.setdefault("AUTH_DEV_BYPASS", "true")
os.environ.setdefault("AUTH_DEV_BYPASS_USER_ID", "11111111-1111-1111-1111-111111111111")
os.environ.setdefault("ENVIRONMENT", "development")


def test_openapi_includes_bearer_security_scheme(app):  # noqa: ANN001
    schema = app.openapi()
    components = schema.get("components", {})
    schemes = components.get("securitySchemes", {})
    assert "BearerAuth" in schemes, "BearerAuth scheme must be present in OpenAPI schema"

    bearer = schemes["BearerAuth"]
    assert bearer["type"] == "http"
    assert bearer["scheme"] == "bearer"
    assert bearer["bearerFormat"] == "JWT"


def test_openapi_global_security_requires_bearer(app):  # noqa: ANN001
    schema = app.openapi()
    security = schema.get("security", [])
    assert any("BearerAuth" in entry for entry in security), (
        "global security must reference BearerAuth"
    )


def test_openapi_schema_caches(app):  # noqa: ANN001
    """`_custom_openapi` は 1 回計算したらキャッシュを返すこと."""
    first = app.openapi()
    second = app.openapi()
    assert first is second
