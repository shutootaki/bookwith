"""エラーハンドリングユーティリティ"""

import logging
from typing import List, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.application.schemas.base import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """アプリケーション例外のベースクラス"""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors: Optional[List[ErrorDetail]] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.errors = errors
        super().__init__(detail)


class BadRequestException(AppException):
    """不正なリクエストエラー"""

    def __init__(self, detail: str, errors: Optional[List[ErrorDetail]] = None):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST, errors)


class UnauthorizedException(AppException):
    """認証エラー"""

    def __init__(
        self,
        detail: str = "Authentication required",
        errors: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED, errors)


class ForbiddenException(AppException):
    """アクセス権限エラー"""

    def __init__(
        self,
        detail: str = "Access forbidden",
        errors: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(detail, status.HTTP_403_FORBIDDEN, errors)


class NotFoundException(AppException):
    """リソース未検出エラー"""

    def __init__(
        self,
        detail: str = "Resource not found",
        errors: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(detail, status.HTTP_404_NOT_FOUND, errors)


class ServiceUnavailableException(AppException):
    """サービス利用不可エラー"""

    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        errors: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(detail, status.HTTP_503_SERVICE_UNAVAILABLE, errors)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """アプリケーション例外ハンドラー"""
    logger.error(f"Application error: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            detail=exc.detail,
            status_code=exc.status_code,
            errors=exc.errors,
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """バリデーションエラーハンドラー"""
    errors: List[ErrorDetail] = []

    for error in exc.errors():
        errors.append(
            ErrorDetail(
                loc=error.get("loc", []),
                msg=error.get("msg", ""),
                type=error.get("type", ""),
            )
        )

    detail = "Validation error"
    logger.warning(f"Validation error: {detail}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
        ).model_dump(),
    )


async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """内部エラーハンドラー"""
    detail = "Internal server error"
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).model_dump(),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """エラーハンドラーの登録"""
    # アプリケーション定義の例外ハンドラーを登録
    app.add_exception_handler(AppException, app_exception_handler)

    # バリデーションエラー用のハンドラー
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # 予期しない例外用のハンドラー
    app.add_exception_handler(Exception, internal_exception_handler)
