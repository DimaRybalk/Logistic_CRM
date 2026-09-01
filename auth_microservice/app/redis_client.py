import os
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv("REDIS_PORT")
NAME = os.getenv("REDIS_NAME")
HOST = os.getenv("REDIS_HOST")

REDIS_URL = f"{NAME}://{HOST}:{PORT}/0"

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis_client
