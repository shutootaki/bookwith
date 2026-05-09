"""H-1: per-user / per-IP のレート制限.

slowapi を使用。`Limiter` の key は認証 user_id を優先し、未認証は IP にフォールバック。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _user_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


try:
    from slowapi import Limiter  # type: ignore[import-untyped]
    from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]

    limiter: Limiter | None = Limiter(key_func=_user_key, default_limits=["120/minute"])
except ImportError:  # pragma: no cover
    # slowapi が未インストールでもアプリ起動は通すため、フォールバックでデコレータを no-op に。
    limiter = None
    RateLimitExceeded = Exception  # type: ignore[assignment,misc]


# 用途別レート（slowapi のリミット文字列）。
GENERAL_LIMIT = "60/minute"
UPLOAD_LIMIT = "10/minute"
EXPENSIVE_LIMIT = "20/minute"  # LLM / TTS など高額エンドポイント


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Rate limit exceeded for %s", _user_key(request))
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "detail": "Too many requests",
            "status_code": 429,
        },
    )


def register_rate_limit(app: FastAPI) -> None:
    """FastAPI app にレート制限ミドルウェア + 例外ハンドラを登録する."""
    if limiter is None:  # pragma: no cover
        logger.warning("slowapi is not installed; rate limiting is disabled")
        return

    # SlowAPIMiddleware: ASGI middleware
    try:
        from slowapi.middleware import SlowAPIMiddleware  # type: ignore[import-untyped]

        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    except Exception:  # pragma: no cover
        logger.exception("Failed to register slowapi middleware")


def _noop_decorator(*_: Any, **__: Any):  # pragma: no cover
    def decorator(func):
        return func

    return decorator


def expensive_limit():  # pragma: no cover
    if limiter is None:
        return _noop_decorator()
    return limiter.limit(EXPENSIVE_LIMIT)


def upload_limit():  # pragma: no cover
    if limiter is None:
        return _noop_decorator()
    return limiter.limit(UPLOAD_LIMIT)


def general_limit():  # pragma: no cover
    if limiter is None:
        return _noop_decorator()
    return limiter.limit(GENERAL_LIMIT)
