"""L-04: API レスポンスに最低限のセキュリティヘッダーを付与する ASGI ミドルウェア."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

# 全レスポンスに付与する基本ヘッダー
_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-resource-policy", b"same-site"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), interest-cohort=()"),
]

# キャッシュ抑止ヘッダーを免除するパス（health/ready 等の冪等な公開エンドポイント）
_CACHE_EXEMPT_PATH_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/ready",
    "/metrics",
)

# 認証必須レスポンスに付ける `Cache-Control` 値。プロキシ・ブラウザキャッシュからの
# クロスユーザ漏洩を防ぐため、既定では `private, no-store` で固定する。
_CACHE_CONTROL_VALUE = b"no-store"
_PRAGMA_VALUE = b"no-cache"


def _path_is_cache_exempt(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in _CACHE_EXEMPT_PATH_PREFIXES)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "") or ""
        cache_exempt = _path_is_cache_exempt(path)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
                existing = {k.lower() for k, _ in headers}
                for k, v in _HEADERS:
                    if k not in existing:
                        headers.append((k, v))
                # 認証必須レスポンスのキャッシュ抑止（既存の Cache-Control があれば尊重）
                if not cache_exempt:
                    if b"cache-control" not in existing:
                        headers.append((b"cache-control", _CACHE_CONTROL_VALUE))
                    if b"pragma" not in existing:
                        headers.append((b"pragma", _PRAGMA_VALUE))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


def register_security_headers(app) -> None:  # noqa: ANN001
    app.add_middleware(SecurityHeadersMiddleware)
