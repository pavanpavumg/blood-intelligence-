import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

async def check_redis_connection() -> bool:
    """
    Probes Redis connectivity. Returns True if ping successful, False otherwise.
    """
    try:
        response = await redis_client.ping()
        return response is True
    except Exception as exc:
        logger.error(f"Redis connection check failed: {exc}")
        return False
