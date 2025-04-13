import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.config.app_config import AppConfig

config = AppConfig()


engine = create_engine(config.database_url, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables initialized successfully")
    except Exception as e:
        logging.error(f"Error occurred during database initialization: {str(e)}", exc_info=True)
        raise


__all__ = ["Base", "get_db", "init_db", "engine", "SessionLocal"]
