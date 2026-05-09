"""CORS allow-list の起動時ガードテスト.

CR-2 補強。`CORS_ALLOW_ORIGINS` に `*` を入れたまま起動しようとすると
RuntimeError で fail-fast することを確認する。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")


def test_main_rejects_wildcard_origins(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")

    # AppConfig をリロード
    from src.config import app_config

    importlib.reload(app_config)

    import pytest

    # main.py のリロードで RuntimeError が起きることを確認
    with pytest.raises(RuntimeError):
        from src import main  # noqa: F401

        importlib.reload(main)


def test_main_accepts_explicit_origins(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS",
        "https://app.bookwith.example,http://localhost:7127",
    )
    from src.config import app_config

    importlib.reload(app_config)

    from src import main

    importlib.reload(main)

    # CORS middleware が登録されていることを確認
    from starlette.middleware.cors import CORSMiddleware

    found = any(mw.cls is CORSMiddleware for mw in main.app.user_middleware)
    assert found
