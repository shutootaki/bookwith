from fastapi import APIRouter, Cookie, HTTPException, Response
from src.models import CallbackResponse, TokenResponse
from src.services import handle_dropbox_callback, refresh_dropbox_token

router = APIRouter()


@router.get("/callback/{provider}", response_model=CallbackResponse)
async def callback(provider: str, state: str, code: str, response: Response):
    if provider != "dropbox":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    try:
        # サービス関数を呼び出し
        redirect_url = handle_dropbox_callback(state, code, response)
        return CallbackResponse(success=True, redirect_url=redirect_url)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.get("/refresh", response_model=TokenResponse)
async def refresh(dropbox_refresh_token: str = Cookie(None)):
    if not dropbox_refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # サービス関数を呼び出し
        token_data = refresh_dropbox_token(dropbox_refresh_token)
        return TokenResponse(
            access_token=token_data["access_token"],
            access_token_expires_at=token_data["access_token_expires_at"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")
