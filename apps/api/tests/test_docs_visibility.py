"""本番環境での Swagger / ReDoc / OpenAPI 隠蔽テスト.

CR-1 補強: 本番では `/docs` / `/redoc` / `/openapi.json` を 404 にして、
内部実装の API シグネチャを攻撃者に公開しない。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")


def _build_app(monkeypatch, environment: str):
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")

    if environment == "production":
        # 本番では assert_production_ready を通すために必要な値を揃える
        monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
        monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
        monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
        monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
        monkeypatch.setenv("SQL_ECHO", "false")
        monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)
    else:
        monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
        monkeypatch.setenv("AUTH_DEV_BYPASS_USER_ID", "11111111-1111-1111-1111-111111111111")

    from src.config import app_config

    importlib.reload(app_config)
    from src import main

    importlib.reload(main)
    return main.app


def test_dev_environment_exposes_docs(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, "development")
    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_production_hides_swagger(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, "production")
    client = TestClient(app)
    assert client.get("/docs").status_code == 404


def test_production_hides_redoc(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, "production")
    client = TestClient(app)
    assert client.get("/redoc").status_code == 404


def test_production_hides_openapi_json(monkeypatch):
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, "production")
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 404


def test_production_health_still_accessible(monkeypatch):
    """本番でも /health は素通しする（liveness probe 用）."""
    from fastapi.testclient import TestClient

    app = _build_app(monkeypatch, "production")
    client = TestClient(app)
    assert client.get("/health").status_code == 200
