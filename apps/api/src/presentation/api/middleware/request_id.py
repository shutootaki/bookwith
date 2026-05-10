"""Request ID ミドルウェア.

レスポンスに `X-Request-ID` を付与し、`request.state.request_id` に保存する。
クライアントが `X-Request-ID` ヘッダーを送ってきた場合はそれを尊重し、
複数サービスを跨ぐ分散トレースのキーとして使えるようにする。

監査ログ・Sentry とのトレース連結・障害解析に有効。
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

# 受信側で受け入れる ID 形式（UUID/英数字 + ハイフンのみ、長すぎる値は弾く）
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_\-]{1,128}$")


def _extract_or_generate_request_id(headers: list[tuple[bytes, bytes]]) -> str:
    """`X-Request-ID` ヘッダーがあれば検証して返し、無ければ UUID4 を生成する."""
    for name, value in headers:
        if name.decode("ascii", "ignore").lower() == "x-request-id":
            candidate = value.decode("ascii", "ignore").strip()
            if _VALID_REQUEST_ID.match(candidate):
                return candidate
            # 不正な文字を含む値は安全のため捨てる
            break
    return uuid4().hex


class RequestIdMiddleware:
    """ASGI ミドルウェア: 受信時に request_id を発行・保持し、レスポンスにも付与."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = list(scope.get("headers", []))
        request_id = _extract_or_generate_request_id(headers)

        # Starlette の `Request.state` は `scope["state"]` (dict) を `State` でラップする。
        # 同じ dict に書き込めば下流ハンドラで `request.state.request_id` として参照できる。
        state = scope.setdefault("state", {})
        if isinstance(state, dict):
            state["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
                # 既に付与されていれば尊重、なければ付ける
                exists = any(h[0].decode("ascii", "ignore").lower() == "x-request-id" for h in response_headers)
                if not exists:
                    response_headers.append((b"x-request-id", request_id.encode("ascii", "ignore")))
                message["headers"] = response_headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def register_request_id(app) -> None:  # noqa: ANN001
    app.add_middleware(RequestIdMiddleware)
