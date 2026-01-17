"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deepthought import __version__
from deepthought.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
    logger.info(f"Starting {settings.app_name} v{__version__}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("Shutting down DeepThought")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="DeepThought",
        description="AI-powered multi-agent calculation service using LangGraph",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from deepthought.api.routes import health, tasks

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

    return app


# Create the app instance
app = create_app()
