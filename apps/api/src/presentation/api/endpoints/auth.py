from fastapi import APIRouter, Cookie, Response
from src.application.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
    UnauthorizedException,
)
from src.application.schemas.base import CallbackResponse, TokenResponse
from src.application.services import handle_dropbox_callback, refresh_dropbox_token

router = APIRouter()


@router.get("/callback/{provider}", response_model=CallbackResponse)
async def callback(provider: str, state: str, code: str, response: Response):
    if provider != "dropbox":
        raise BadRequestException("Unsupported provider")

    try:
        # サービス関数を呼び出し
        redirect_url = handle_dropbox_callback(state, code, response)
        return CallbackResponse(success=True, redirect_url=redirect_url)

    except Exception as e:
        raise ServiceUnavailableException(
            f"Error occurred during authentication: {str(e)}"
        )


@router.get("/refresh", response_model=TokenResponse)
async def refresh(dropbox_refresh_token: str = Cookie(None)):
    if not dropbox_refresh_token:
        raise UnauthorizedException("Authentication required")

    try:
        # サービス関数を呼び出し
        token_data = refresh_dropbox_token(dropbox_refresh_token)
        return TokenResponse(
            access_token=token_data["access_token"],
            access_token_expires_at=token_data["access_token_expires_at"],
        )

    except Exception as e:
        raise ServiceUnavailableException(
            f"Error occurred while refreshing token: {str(e)}"
        )
