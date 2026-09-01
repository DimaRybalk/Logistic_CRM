import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import TaskModel
import redis.asyncio as aioredis
from app.redis_client import get_redis

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
REDIS_NAME = os.getenv("REDIS_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_HOST = os.getenv("REDIS_HOST")

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, fixture_redis_client: aioredis.Redis):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fixture_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def fixture_task(db_session: AsyncSession) -> TaskModel:
    task = TaskModel(
        title="Купить сервер",
        description="Для деплоя CRM",
        is_completed=False,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture(scope="function")
async def fixture_redis_client():
    if not all([REDIS_NAME, REDIS_PORT, REDIS_HOST]):
        raise RuntimeError(
            "Missing required Redis environment variables: REDIS_NAME, REDIS_PORT,"
            " REDIS_HOST"
        )

    client = aioredis.from_url(
        f"{REDIS_NAME}://{REDIS_HOST}:{REDIS_PORT}/0", decode_responses=True
    )

    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()
