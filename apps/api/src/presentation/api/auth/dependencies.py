"""認証用依存関係（CR-1）.

Supabase Auth が発行する JWT を `Authorization: Bearer <token>` ヘッダから取り出して検証する。

`auth_dev_bypass=true` の場合は検証をスキップして固定ユーザーを返す（開発・テスト用）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.app_config import AppConfig
from src.domain.shared.identifiers import is_strict_uuid
from src.presentation.api.error_messages.error_handlers import UnauthorizedException

logger = logging.getLogger(__name__)

# PyJWT は module load 時に解決し、毎リクエストの import 試行を避ける。
# 未インストール時は jwt=None としてアプリ起動は通し、リクエスト時に 401 を返す。
try:
    import jwt as _jwt  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _jwt = None  # type: ignore[assignment]


@dataclass(frozen=True)
class AuthenticatedUser:
    """認証済みユーザー."""

    user_id: str
    email: str | None = None


# auto_error=False で「未提供」と「不正トークン」を分けて扱う。
_bearer = HTTPBearer(auto_error=False, bearerFormat="JWT")


def _decode_jwt(token: str, config: AppConfig) -> dict:
    """Supabase の HS256 JWT を検証する."""

    if not config.supabase_jwt_secret:
        # 本番なら設定漏れ。dev でも warn してバイパスを使うよう指示する。
        logger.error("SUPABASE_JWT_SECRET is not configured; cannot verify JWT")
        raise UnauthorizedException("Authentication is not configured on this server")

    if _jwt is None:  # pragma: no cover
        logger.error("PyJWT is not installed; cannot verify JWT")
        raise UnauthorizedException("Authentication is not available")

    decode_kwargs: dict = {
        "algorithms": config.jwt_algorithms_list,
        "audience": config.supabase_jwt_audience,
        "leeway": config.supabase_jwt_leeway_seconds,
        "options": {"require": ["exp", "sub"]},
    }
    # 設定されているときだけ issuer pinning を有効化する。
    if config.supabase_jwt_issuer:
        decode_kwargs["issuer"] = config.supabase_jwt_issuer

    try:
        payload: dict = _jwt.decode(  # type: ignore[no-untyped-call]
            token, config.supabase_jwt_secret, **decode_kwargs
        )
    except _jwt.PyJWTError as e:
        # PyJWT の例外階層 (期限切れ・署名不一致・audience 不一致など) のみを 401 に折りたたむ。
        # それ以外 (kwargs ミス等の programmer error) は 500 として上位に伝える。
        logger.warning("JWT decode failed: %s", e)
        raise UnauthorizedException("Invalid authentication token")

    return payload


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser:
    """JWT を検証して認証済みユーザーを返す."""

    config: AppConfig = AppConfig.get_config()

    if config.auth_dev_bypass and not config.is_production:
        # 開発・テスト用バイパス。本番では絶対通らないよう environment でガード。
        bypass_id = config.auth_dev_bypass_user_id
        if not is_strict_uuid(bypass_id):
            raise UnauthorizedException("Configured bypass user_id is not a valid UUID")
        # H-1: rate limiter の `_user_key` が user-scoped に効くよう state に立てておく。
        request.state.user_id = bypass_id
        return AuthenticatedUser(user_id=bypass_id, email=None)

    if credentials is None or not credentials.credentials:
        raise UnauthorizedException("Authentication required")

    payload = _decode_jwt(credentials.credentials, config)

    sub = payload.get("sub")
    if not isinstance(sub, str) or not is_strict_uuid(sub):
        raise UnauthorizedException("Invalid token subject")

    email = payload.get("email")
    if email is not None and not isinstance(email, str):
        email = None

    # request.state に保存しておくとログ等で参照しやすい。
    request.state.user_id = sub

    return AuthenticatedUser(user_id=sub, email=email)


async def require_user_id(user: AuthenticatedUser = Depends(get_current_user)) -> str:
    """認証済みユーザーの user_id（UUID 文字列）を返す."""

    return user.user_id
