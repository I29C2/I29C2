# backend/app/core/database.py
from __future__ import annotations

import structlog
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from app.core.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy 2.0 sync engine (async can be layered later with asyncpg)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables that do not yet exist.

    In production you would use Alembic migrations instead, but this
    function is useful for development and the initial startup event.
    """
    # Import all model modules so that Base.metadata is populated before
    # create_all is called.
    from app.models import (  # noqa: F401
        user,
        league,
        match,
        odds,
        prediction,
        integrity,
        alert,
        model_registry,
    )

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_initialized", tables=list(Base.metadata.tables.keys()))
    except Exception as exc:
        logger.error("database_init_failed", error=str(exc))
        raise
