import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    loc: list[str | int] | None = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
    status_code: int
    errors: list[ErrorDetail] | None = None


class AppException(Exception):  # noqa: N818
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        self.errors = errors
        super().__init__(detail)


class BadRequestException(AppException):
    def __init__(self, detail: str, errors: list[ErrorDetail] | None = None) -> None:
        super().__init__(detail, status.HTTP_400_BAD_REQUEST, errors)


class UnauthorizedException(AppException):
    def __init__(
        self,
        detail: str = "Authentication required",
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED, errors)


class ForbiddenException(AppException):
    def __init__(
        self,
        detail: str = "Access forbidden",
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(detail, status.HTTP_403_FORBIDDEN, errors)


class NotFoundException(AppException):
    def __init__(
        self,
        detail: str = "Resource not found",
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(detail, status.HTTP_404_NOT_FOUND, errors)


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(detail, status.HTTP_503_SERVICE_UNAVAILABLE, errors)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
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


async def validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError) -> JSONResponse:
    errors: list[ErrorDetail] = []

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
    app.add_exception_handler(AppException, app_exception_handler)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    app.add_exception_handler(Exception, internal_exception_handler)
