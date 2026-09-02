from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional

router = APIRouter()

@router.get("/history")
async def get_biomarker_history(
    code: str = Query(..., description="Canonical biomarker code (e.g. HBA1C, TSH, CHOLESTEROL_TOTAL)"),
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get historical trend time-series data for a specific biomarker to render progress charts.
    """
    return {
        "biomarker_code": code,
        "unit": "mg/dL",
        "data_points": [
            {"date": "2025-08-20", "value": 110, "status": "ELEVATED"},
            {"date": "2026-02-15", "value": 102, "status": "SLIGHTLY_ELEVATED"},
            {"date": "2026-08-10", "value": 94, "status": "OPTIMAL"}
        ]
    }
