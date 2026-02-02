import redis.asyncio as redis
from app.core.config import settings

# Create Redis Client
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    socket_timeout=5.0,
    socket_connect_timeout=5.0
)

async def get_redis():
    return redis_client
