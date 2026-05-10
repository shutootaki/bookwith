"""pytest フィクスチャと共通環境変数.

このテストスイートは「認証ガードが正しく機能していること」を最低限確認する目的で書かれている。
実 DB / 実 Weaviate / 実 GCS は不要なように、必要に応じて Depends 上書きやフェイクオブジェクトを使う。

session-level の環境変数は本ファイル内で `os.environ.setdefault` する。
個別テストで上書きしたい場合は `monkeypatch.setenv(...)` を使う。
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

# ----------------------------------------
# Session-level 環境変数（全テスト共通）
# ----------------------------------------
# AppConfig が起動時に読む値を最低限揃える。実際のテスト境界では monkeypatch で上書きする。
_DEFAULT_ENV: dict[str, str] = {
    "ENVIRONMENT": "development",
    "AUTH_DEV_BYPASS": "false",
    "DATABASE_URL": "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    "OPENAI_API_KEY": "test-openai-key",
    "CORS_ALLOW_ORIGINS": "http://localhost:7127",
    "SQL_ECHO": "false",
    "SQLALCHEMY_AUTO_CREATE": "false",  # テストで create_all を走らせない
    "MAX_UPLOAD_BYTES": str(1024 * 1024),
    "EPUB_FETCH_ALLOWED_HOSTS": "",
}

for _key, _value in _DEFAULT_ENV.items():
    os.environ.setdefault(_key, _value)


import pytest  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def app() -> Iterator[Any]:
    """FastAPI app を返す。`init_db` 等の startup は呼ばずに直接生成する.

    lifespan を回避するため、`main.app` を直接 import する。
    ASGI ライフスパンが回らない代わりに、routes と middleware だけ動作する。
    """
    from src.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
