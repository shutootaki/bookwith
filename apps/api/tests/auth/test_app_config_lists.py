"""AppConfig の各種カンマ区切りリストプロパティの動作テスト.

CR-2 / H-3 補強: 環境変数のリストパースが正しく動作することを保証する。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")


def _reload_config(monkeypatch, **env: str) -> object:
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    from src.config import app_config

    importlib.reload(app_config)
    return app_config.AppConfig.get_config()


def test_cors_allow_origins_single(monkeypatch):
    config = _reload_config(monkeypatch, CORS_ALLOW_ORIGINS="https://app.example.com")
    assert config.allowed_cors_origins == ["https://app.example.com"]


def test_cors_allow_origins_multiple(monkeypatch):
    config = _reload_config(
        monkeypatch,
        CORS_ALLOW_ORIGINS="https://app.example.com,http://localhost:7127, https://staging.example",
    )
    assert config.allowed_cors_origins == [
        "https://app.example.com",
        "http://localhost:7127",
        "https://staging.example",
    ]


def test_cors_allow_origins_empty_segments_filtered(monkeypatch):
    config = _reload_config(
        monkeypatch,
        CORS_ALLOW_ORIGINS=",,https://x,,",
    )
    assert config.allowed_cors_origins == ["https://x"]


def test_jwt_algorithms_default_hs256(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_ALGORITHMS", raising=False)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://x")
    config = _reload_config(monkeypatch)
    assert "HS256" in config.jwt_algorithms_list


def test_jwt_algorithms_multiple(monkeypatch):
    config = _reload_config(
        monkeypatch,
        SUPABASE_JWT_ALGORITHMS="HS256, RS256",
        CORS_ALLOW_ORIGINS="https://x",
    )
    assert config.jwt_algorithms_list == ["HS256", "RS256"]


def test_epub_fetch_allowed_hosts_default_empty(monkeypatch):
    monkeypatch.delenv("EPUB_FETCH_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://x")
    config = _reload_config(monkeypatch)
    assert config.epub_fetch_allowed_hosts_list == []


def test_epub_fetch_allowed_hosts_parses(monkeypatch):
    config = _reload_config(
        monkeypatch,
        EPUB_FETCH_ALLOWED_HOSTS="standardebooks.org,archive.org,storage.googleapis.com",
        CORS_ALLOW_ORIGINS="https://x",
    )
    assert config.epub_fetch_allowed_hosts_list == [
        "standardebooks.org",
        "archive.org",
        "storage.googleapis.com",
    ]


def test_audio_dirs_default_empty(monkeypatch):
    monkeypatch.delenv("AUDIO_BGM_DIRS", raising=False)
    monkeypatch.delenv("AUDIO_OUTPUT_DIRS", raising=False)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://x")
    config = _reload_config(monkeypatch)
    assert config.audio_bgm_dirs_list == []
    assert config.audio_output_dirs_list == []


def test_is_production_lowercase_match(monkeypatch):
    config = _reload_config(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ALLOW_ORIGINS="https://x",
        AUTH_DEV_BYPASS="false",
        SUPABASE_JWT_SECRET="secret",
        WEAVIATE_URL="https://x",
        WEAVIATE_API_KEY="abc",
    )
    assert config.is_production is True


def test_is_production_false_for_dev(monkeypatch):
    config = _reload_config(
        monkeypatch,
        ENVIRONMENT="development",
        CORS_ALLOW_ORIGINS="https://x",
    )
    assert config.is_production is False
