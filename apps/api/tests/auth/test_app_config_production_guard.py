"""AppConfig.assert_production_ready の検証.

本番環境で必須となる設定値（CORS、JWT_SECRET、Weaviate 認証）が抜けていたら
fail-fast で `RuntimeError` を上げる。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

import pytest


def _reload_config():
    from src.config import app_config

    importlib.reload(app_config)
    return app_config.AppConfig.get_config()


def test_dev_environment_skips_production_guard(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:7127")
    config = _reload_config()
    # development では throw しない
    config.assert_production_ready()


def test_production_requires_jwt_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    config = _reload_config()
    with pytest.raises(RuntimeError, match="SUPABASE_JWT_SECRET"):
        config.assert_production_ready()


def test_production_requires_weaviate_auth(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "")
    monkeypatch.setenv("WEAVIATE_API_KEY", "")
    config = _reload_config()
    with pytest.raises(RuntimeError, match="WEAVIATE"):
        config.assert_production_ready()


def test_production_rejects_dev_bypass(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    config = _reload_config()
    with pytest.raises(RuntimeError, match="AUTH_DEV_BYPASS"):
        config.assert_production_ready()


def test_production_rejects_wildcard_cors(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    config = _reload_config()
    with pytest.raises(RuntimeError, match="CORS_ALLOW_ORIGINS"):
        config.assert_production_ready()


def test_production_passes_with_full_config(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
    monkeypatch.setenv("SQL_ECHO", "false")
    monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)
    config = _reload_config()
    config.assert_production_ready()


def test_production_rejects_unbounded_max_upload_bytes(monkeypatch):
    """メモリ枯渇 DoS 防止: 100 MiB を超える MAX_UPLOAD_BYTES を本番でガード."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
    monkeypatch.setenv("SQL_ECHO", "false")
    monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)
    # 1 GiB を試す（hard cap=100 MiB を超える）
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(1024 * 1024 * 1024))
    config = _reload_config()
    with pytest.raises(RuntimeError, match="MAX_UPLOAD_BYTES"):
        config.assert_production_ready()


def test_production_accepts_max_upload_bytes_at_cap(monkeypatch):
    """境界値: hard cap (100 MiB) ぴったりは許容."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
    monkeypatch.setenv("SQL_ECHO", "false")
    monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))
    config = _reload_config()
    config.assert_production_ready()
