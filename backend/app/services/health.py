from app.core.database import check_database_connection
from app.core.redis import check_redis_connection
from app.core.logging import logger
from app.schemas.health import HealthResponse

class HealthService:
    @staticmethod
    async def check_health() -> HealthResponse:
        """
        Executes health probe against PostgreSQL and Redis services.
        Returns HealthResponse with status='ok' when healthy.
        """
        db_healthy = await check_database_connection()
        redis_healthy = await check_redis_connection()
        
        is_all_ok = db_healthy and redis_healthy
        
        logger.info(f"Health Probe - PostgreSQL: {'OK' if db_healthy else 'FAILED'}, Redis: {'OK' if redis_healthy else 'FAILED'}")
        
        return HealthResponse(
            status="ok" if is_all_ok else "unhealthy",
            database="connected" if db_healthy else "disconnected",
            redis="connected" if redis_healthy else "disconnected"
        )
