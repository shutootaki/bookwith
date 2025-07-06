import logging
from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.config.app_config import AppConfig
from src.config.db import get_db, init_db
from src.presentation.api import setup_routes
from src.presentation.api.error_messages.error_handlers import setup_exception_handlers

# 設定を読み込み、ログレベルを決定
config = AppConfig.get_config()
log_level = logging.DEBUG if config.debug_llm_logging else logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Database initialization error: {e}")

    yield

    # Shutdown
    logging.info("Closing database connection")


app = FastAPI(title="BookWith API", description="Book related API service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_session() -> Generator[Session]:
    yield from get_db()


setup_routes(app)

setup_exception_handlers(app)
