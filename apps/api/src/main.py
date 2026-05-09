import logging
from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session

from src.config.app_config import AppConfig
from src.config.db import get_db, init_db
from src.presentation.api import setup_routes
from src.presentation.api.error_messages.error_handlers import setup_exception_handlers
from src.presentation.api.middleware import register_api_middleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


_config = AppConfig.get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Database initialization error: {e}")

    # 本番環境で必須な設定値が漏れていないかを起動時に検証する（fail-fast）。
    _config.assert_production_ready()

    # 開発バイパスが有効な場合は誤った staging 投入を検知できるよう、起動ログで明示的に警告する。
    if _config.auth_dev_bypass:
        logging.warning(
            "AUTH_DEV_BYPASS is enabled (env=%s). All requests will be authenticated as %s. "
            "Disable this in staging / production deployments.",
            _config.environment,
            _config.auth_dev_bypass_user_id,
        )

    yield

    # Shutdown
    logging.info("Closing database connection")


# 本番では Swagger UI / ReDoc / openapi.json を隠す（攻撃面の縮小）。
# 開発・staging では通常通り `/docs` / `/redoc` / `/openapi.json` を提供する。
_docs_url = None if _config.is_production else "/docs"
_redoc_url = None if _config.is_production else "/redoc"
_openapi_url = None if _config.is_production else "/openapi.json"

app = FastAPI(
    title="BookWith API",
    description="Book related API service",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)


# CR-2: CORS は明示 allow-list のみ。`*` + credentials の併用は厳禁。
_allowed_origins = _config.allowed_cors_origins
if "*" in _allowed_origins:
    raise RuntimeError("CORS allow_origins must not contain '*' when credentials are allowed")


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
    max_age=600,
)


def get_db_session() -> Generator[Session]:
    yield from get_db()


register_api_middleware(app)
setup_routes(app)


# 認証不要のヘルスチェック（Cloud Run / k8s の liveness probe 用）.
# DB / Weaviate / GCS の到達性は確認せず、プロセスが生きているかだけを返す。
@app.get("/health", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


# Readiness probe.
# 現時点では liveness と同じだが、将来 DB ping 等を追加できるよう分離しておく。
@app.get("/ready", include_in_schema=False)
async def readiness() -> dict[str, str]:
    return {"status": "ready"}


setup_exception_handlers(app)


def _custom_openapi():
    """OpenAPI スキーマに Bearer 認証を明示する.

    CR-1 補強: フロントの型生成（`pnpm openapi:ts`）時に `Authorization: Bearer <jwt>`
    が必須であることを伝えるため、`securitySchemes` と `security` を追加する。
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description=app.description,
        routes=app.routes,
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Supabase Auth が発行する JWT を `Authorization: Bearer <token>` で送る。",
    }
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]
