"""L-01 (seed.py の本番ガード) の回帰テスト.

`seed_data()` は固定 UUID のテストユーザを Postgres に挿入する開発専用スクリプト。
誤って本番で実行されると `TEST_USER_ID` のレコードが本番 DB に混入し、CR-1 防御層
（実際にはここまで到達しないが、in-depth として）の信用を毀損する。

`config.is_production` が True なら `RuntimeError` を上げるガードが入っているため、
そのガードが将来のリファクタで外れないよう回帰テストで保護する。
"""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

import pytest


def _reload_modules():
    from src.config import app_config, seed

    importlib.reload(app_config)
    importlib.reload(seed)
    return seed


def test_seed_data_raises_in_production(monkeypatch):
    """ENVIRONMENT=production で seed_data を呼ぶと RuntimeError が上がる."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
    monkeypatch.setenv("SQL_ECHO", "false")
    monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)

    seed = _reload_modules()
    with pytest.raises(RuntimeError, match="must not be executed in production"):
        seed.seed_data()


def test_seed_data_short_circuits_before_db_access(monkeypatch):
    """RuntimeError は SessionLocal 取得より前で投げられる（DB に触らない）."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    monkeypatch.setenv("WEAVIATE_URL", "https://x.weaviate.network")
    monkeypatch.setenv("WEAVIATE_API_KEY", "abc")
    monkeypatch.setenv("WEAVIATE_AUTO_TENANT_CREATION", "false")
    monkeypatch.setenv("SQL_ECHO", "false")
    monkeypatch.delenv("GCS_EMULATOR_HOST", raising=False)

    seed = _reload_modules()

    # SessionLocal が呼ばれたら警告。production guard が SessionLocal より前にいないと意味がない。
    db_called = {"flag": False}

    class _Boom:
        def __call__(self, *a, **kw):  # noqa: ANN002, ANN003
            db_called["flag"] = True
            raise AssertionError("SessionLocal must not be invoked when production guard fires")

    monkeypatch.setattr(seed, "SessionLocal", _Boom())

    with pytest.raises(RuntimeError):
        seed.seed_data()

    assert db_called["flag"] is False, "production guard must short-circuit BEFORE acquiring DB session"


def test_seed_data_runs_in_development_environment(monkeypatch):
    """ENVIRONMENT=development では production guard が発火しない（開発フローを壊さない）."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:7127")

    seed = _reload_modules()

    # SessionLocal を mock して RuntimeError 以外の問題で落ちないようにする。
    class _NoopSession:
        def add_all(self, *a, **kw) -> None:  # noqa: ANN002, ANN003
            pass

        def commit(self) -> None:
            pass

        def rollback(self) -> None:
            pass

        def close(self) -> None:
            pass

    monkeypatch.setattr(seed, "SessionLocal", lambda: _NoopSession())

    # 例外が出ないこと（development では普通に通る）
    seed.seed_data()
