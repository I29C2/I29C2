# backend/app/main.py
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialise DB on startup."""
    logger.info("betbot_starting", app_name=settings.APP_NAME, debug=settings.DEBUG)
    try:
        from app.core.database import init_db
        init_db()
        logger.info("database_ready")
    except Exception as exc:
        logger.error("startup_db_failed", error=str(exc))
        # Don't crash the whole app — let individual requests surface DB errors

    yield  # Application runs here

    logger.info("betbot_shutdown")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "AI-powered sports betting analysis platform. "
            "Provides value-bet detection, integrity scoring, and ML predictions."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Request timing middleware
    # ------------------------------------------------------------------
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "validation_error",
            url=str(request.url),
            errors=exc.errors(),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": str(exc.body)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            url=str(request.url),
            error=str(exc),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    # ------------------------------------------------------------------
    # Health check (no auth required)
    # ------------------------------------------------------------------
    @app.get("/health", tags=["Health"], include_in_schema=True)
    async def health_check() -> dict:
        """Lightweight liveness probe."""
        return {"status": "ok", "app": settings.APP_NAME}

    @app.get("/health/db", tags=["Health"], include_in_schema=True)
    async def health_db() -> dict:
        """Check database connectivity."""
        from app.core.database import engine
        from sqlalchemy import text

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as exc:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "error", "database": str(exc)},
            )

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
