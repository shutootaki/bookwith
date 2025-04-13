import json
from typing import Dict, Optional

from fastapi import Response
from src.application.utils.helpers import TOKEN_MAPPING, get_dropbox_client


def handle_dropbox_callback(state: str, code: str, response: Response) -> str:
    """Dropboxコールバック処理のためのサービス関数"""
    state_data = json.loads(state)
    redirect_uri = state_data.get("redirectUri")

    # Dropboxクライアント取得
    dbx = get_dropbox_client()

    # アクセストークン取得
    token_result = dbx.auth.get_access_token_from_code(redirect_uri, code)

    # リフレッシュトークンをクッキーに設定
    response.set_cookie(
        key=TOKEN_MAPPING["dropbox"],
        value=token_result.refresh_token,
        max_age=365 * 24 * 60 * 60,
        secure=True,
        httponly=True,
        samesite="lax",
    )

    # 成功ページへのリダイレクトURLを返す
    return "/success"


def refresh_dropbox_token(refresh_token: str) -> Dict[str, Optional[int]]:
    """Dropboxトークン更新のためのサービス関数"""
    # Dropboxクライアント取得
    dbx = get_dropbox_client()

    # リフレッシュトークン設定
    dbx.auth.set_refresh_token(refresh_token)

    # アクセストークンを更新
    dbx.auth.refresh_access_token()

    return {
        "access_token": dbx.auth.get_access_token(),
        "access_token_expires_at": dbx.auth.get_access_token_expires_at(),
    }
