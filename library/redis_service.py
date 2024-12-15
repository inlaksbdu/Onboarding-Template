from redis import asyncio as aioredis
from .config import settings

JIT_EXP = 3600

token_blocklist = aioredis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    db=settings.REDIS_DB,
    decode_responses=True,
)


async def add_jti_to_blocklist(jti: str, expire: int = JIT_EXP) -> None:
    await token_blocklist.set(jti, "", ex=expire)


async def is_jti_blacklisted(jti: str) -> bool:
    return (await token_blocklist.exists(jti)) == 1
