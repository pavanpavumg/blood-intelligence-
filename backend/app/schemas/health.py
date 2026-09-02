from typing import Optional, Dict
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall health status")
    database: Optional[str] = Field(default=None, description="PostgreSQL connection state")
    redis: Optional[str] = Field(default=None, description="Redis connection state")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok"
            }
        }
    }
