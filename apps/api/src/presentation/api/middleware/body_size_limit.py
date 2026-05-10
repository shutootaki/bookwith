"""H-1 強化: リクエストボディの最大サイズを ASGI 段で強制する.

Pydantic の max_length 検証より前に、Content-Length / 受信バイト数を見て
過大ペイロードを 413 で拒否する。これにより、巨大 base64 を貼られて
FastAPI 内に全部メモリ展開される前に落とせる。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.app_config import AppConfig

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


# 上限は max_upload_bytes（base64 ファイル含む）に余裕を足したバッファサイズ。
# 現状: 25MB のアップロード上限 + メタデータ等 → 32MB を上限に。
_OVERHEAD_BYTES = 7 * 1024 * 1024


def _max_request_body() -> int:
    config = AppConfig.get_config()
    return config.max_upload_bytes + _OVERHEAD_BYTES


class BodySizeLimitMiddleware:
    """Content-Length と実受信バイト数の両方で過大ペイロードを弾く."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        max_bytes = _max_request_body()

        # Content-Length ヘッダで先に判定する（POST / PUT / PATCH のみ）。
        method = scope.get("method", "").upper()
        if method in {"POST", "PUT", "PATCH"}:
            for name, value in scope.get("headers", []):
                if name.decode("ascii", "ignore").lower() == "content-length":
                    try:
                        if int(value.decode("ascii", "ignore")) > max_bytes:
                            await self._reject(send)
                            return
                    except ValueError:
                        # 不正な Content-Length は受信側で弾かせる
                        pass
                    break

        # チャンクされた body の場合は累積カウントで監視する。
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                body: bytes = message.get("body", b"") or b""
                received += len(body)
                if received > max_bytes:
                    # 長すぎる場合はそのまま 413 をクライアントに返す。
                    raise _PayloadTooLargeError
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _PayloadTooLargeError:
            await self._reject(send)

    @staticmethod
    async def _reject(send: Send) -> None:
        body = b'{"success":false,"detail":"Payload too large","status_code":413}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


class _PayloadTooLargeError(Exception):
    """累積受信が上限を超えた時に内部で raise する."""


def register_body_size_limit(app) -> None:  # noqa: ANN001
    app.add_middleware(BodySizeLimitMiddleware)
