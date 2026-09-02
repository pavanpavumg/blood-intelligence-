from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    BaseSystemException,
    global_exception_handler,
    system_exception_handler,
)
from app.api.routes import api_router

def create_application() -> FastAPI:
    """
    Application factory initializing FastAPI, CORS, Exception Handlers, and Routes.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Configuration
    if settings.ALLOWED_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Exception Handlers
    app.add_exception_handler(BaseSystemException, system_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # API Routers
    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": "0.2.0",
            "status": "running",
            "docs_url": "/docs",
            "health_url": "/api/health",
            "upload_url": "/api/reports/upload"
        }

    logger.info(f"Initialized {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode.")
    return app

app = create_application()
