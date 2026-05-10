"""rate_limit middleware のテスト.

H-1: slowapi が利用可能なら register_rate_limit が動作する。
slowapi 未インストール環境でも no-op で例外を起こさないことを確認する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from fastapi import FastAPI

from src.presentation.api.middleware import (
    EXPENSIVE_LIMIT,
    GENERAL_LIMIT,
    UPLOAD_LIMIT,
    register_rate_limit,
)


def test_register_rate_limit_does_not_raise():
    """Slowapi が無くても登録は成功する（フォールバック動作）."""
    app = FastAPI()
    # 例外なく完了することを確認
    register_rate_limit(app)


def test_limit_constants_have_expected_format():
    """`<count>/<period>` 形式の文字列であること."""
    for limit in (GENERAL_LIMIT, UPLOAD_LIMIT, EXPENSIVE_LIMIT):
        assert "/" in limit
        count_str, period = limit.split("/", 1)
        assert int(count_str) > 0
        assert period in {"second", "minute", "hour", "day"}


def test_user_key_uses_user_id_when_available():
    """Key 関数が認証 user_id を優先することを確認."""
    from starlette.requests import Request

    from src.presentation.api.middleware.rate_limit import _user_key

    scope = {
        "type": "http",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "method": "GET",
        "path": "/",
    }
    req = Request(scope)  # type: ignore[arg-type]
    req.state.user_id = "11111111-1111-1111-1111-111111111111"
    assert _user_key(req).startswith("user:11111111-")


def test_user_key_falls_back_to_ip():
    from starlette.requests import Request

    from src.presentation.api.middleware.rate_limit import _user_key

    scope = {
        "type": "http",
        "headers": [],
        "client": ("203.0.113.10", 4444),
        "method": "GET",
        "path": "/",
    }
    req = Request(scope)  # type: ignore[arg-type]
    assert _user_key(req).startswith("ip:203.0.113.10")
