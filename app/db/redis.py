import aioredis
from app.core.settings import settings
from redis.asyncio import Redis

# JTI: JWT ID
JTI_EXPIRY = 3600

#  aioredis.StrictRedis is outdated/deprecated.
# aioredis is now merged into redis-py.
#  So in modern projects, use Redis

# token_blocklist = aioredis.StrictRedis(
#     host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
# )


token_blocklist = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_blocklist(jti: str) -> bool:
    jti = await token_blocklist.get(jti)

    return jti is not None
