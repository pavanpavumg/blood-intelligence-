from fastapi import APIRouter
from app.api.v1.endpoints import reports, biomarkers

api_v1_router = APIRouter()

api_v1_router.include_router(reports.router, prefix="/reports", tags=["Lab Reports"])
api_v1_router.include_router(biomarkers.router, prefix="/biomarkers", tags=["Biomarker Analytics"])
