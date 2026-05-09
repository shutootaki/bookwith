from fastapi import FastAPI

from src.presentation.api.middleware.body_size_limit import register_body_size_limit
from src.presentation.api.middleware.rate_limit import (
    EXPENSIVE_LIMIT,
    GENERAL_LIMIT,
    UPLOAD_LIMIT,
    expensive_limit,
    general_limit,
    limiter,
    rate_limit_exceeded_handler,
    register_rate_limit,
    upload_limit,
)
from src.presentation.api.middleware.request_id import register_request_id
from src.presentation.api.middleware.security_headers import register_security_headers


def register_api_middleware(app: FastAPI) -> None:
    register_request_id(app)
    register_security_headers(app)
    register_body_size_limit(app)
    register_rate_limit(app)

__all__ = [
    "EXPENSIVE_LIMIT",
    "GENERAL_LIMIT",
    "UPLOAD_LIMIT",
    "expensive_limit",
    "general_limit",
    "limiter",
    "register_api_middleware",
    "register_body_size_limit",
    "rate_limit_exceeded_handler",
    "register_rate_limit",
    "register_request_id",
    "register_security_headers",
    "upload_limit",
]
