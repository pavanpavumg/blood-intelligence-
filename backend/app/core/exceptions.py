from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger

class BaseSystemException(Exception):
    """Base exception for application domain errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches unhandled exceptions and formats a consistent error response.
    """
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

async def system_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handles domain-specific BaseSystemException errors.
    """
    if isinstance(exc, BaseSystemException):
        logger.warning(f"Domain Exception on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    return await global_exception_handler(request, exc)
