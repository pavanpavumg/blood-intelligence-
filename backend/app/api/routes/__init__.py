from fastapi import APIRouter
from app.api.routes import health, reports

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Checks"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports Extraction"])
