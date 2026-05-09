"""retry_decorator の動作テスト.

H-09 補強. `idempotent=False` 指定時に副作用処理が再試行されないこと、
`non_retryable_exceptions` で指定した例外型で即座に伝播することを保証する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from unittest.mock import patch

import pytest

from src.infrastructure.memory.retry_decorator import retry_on_error


def test_retries_when_idempotent_default():
    counter = {"calls": 0}

    @retry_on_error(max_retries=3, initial_delay=0)
    def flaky() -> str:
        counter["calls"] += 1
        if counter["calls"] < 3:
            raise RuntimeError("transient")
        return "ok"

    # time.sleep をモックして高速化
    with patch("src.infrastructure.memory.retry_decorator.time.sleep"):
        assert flaky() == "ok"
    assert counter["calls"] == 3


def test_does_not_retry_when_idempotent_false():
    counter = {"calls": 0}

    @retry_on_error(max_retries=5, initial_delay=0, idempotent=False)
    def expensive() -> str:
        counter["calls"] += 1
        raise RuntimeError("paid for half a chapter")

    with pytest.raises(RuntimeError, match="paid for half a chapter"):
        expensive()
    assert counter["calls"] == 1, "Non-idempotent operation must not retry"


def test_non_retryable_exceptions_propagate_immediately():
    counter = {"calls": 0}

    class AuthError(Exception):
        pass

    @retry_on_error(
        max_retries=5,
        initial_delay=0,
        non_retryable_exceptions=(AuthError,),
    )
    def authorized() -> str:
        counter["calls"] += 1
        raise AuthError("forbidden")

    with pytest.raises(AuthError):
        authorized()
    assert counter["calls"] == 1


def test_returns_after_max_retries_raises():
    counter = {"calls": 0}

    @retry_on_error(max_retries=2, initial_delay=0)
    def always_fails() -> str:
        counter["calls"] += 1
        raise RuntimeError("never works")

    with patch("src.infrastructure.memory.retry_decorator.time.sleep"):
        with pytest.raises(RuntimeError):
            always_fails()
    # 1 (初回) + 2 (再試行) = 3 回呼ばれる
    assert counter["calls"] == 3
